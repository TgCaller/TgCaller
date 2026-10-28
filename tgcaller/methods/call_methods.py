"""
Call Management Methods
"""

import asyncio
from typing import Optional

from ..types import AudioConfig, VideoConfig, CallUpdate, CallStatus
from ..exceptions import CallError, ConnectionError


class CallMethods:
    """Call management methods"""
    
    async def join_call(
        self,
        chat_id: int,
        audio_config: Optional[AudioConfig] = None,
        video_config: Optional[VideoConfig] = None
    ) -> bool:
        """
        Join a voice/video call
        
        Args:
            chat_id: Chat ID to join
            audio_config: Audio configuration
            video_config: Video configuration (optional)
            
        Returns:
            True if successful
        """
        if not self._is_connected:
            raise ConnectionError("TgCaller not started")
        
        if chat_id in self._active_calls:
            return True  # Already in call
        
        try:
            if audio_config is None:
                audio_config = AudioConfig()

            call_session = {
                'chat_id': chat_id,
                'audio_config': audio_config,
                'video_config': video_config,
                'status': CallStatus.CONNECTING,
            }
            self._active_calls[chat_id] = call_session

            # ConnectionManager delegates to the configured real transport.
            # A missing or failed backend must never be reported as a joined call.
            connected = await self._connection_manager.connect_call(
                chat_id, audio_config, video_config
            )
            if not connected:
                self._active_calls.pop(chat_id, None)
                raise CallError(
                    "Could not join Telegram group call: no working call transport "
                    "is configured or the transport connection failed."
                )

            call_session['status'] = CallStatus.CONNECTED
            update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.CONNECTED,
                message="Successfully joined call",
            )
            await self._emit_event('call_joined', update)
            self._logger.info(f"Joined call in chat {chat_id}")
            return True

        except BaseException as e:
            # Cancellation can occur while the transport is negotiating. Remove
            # the provisional local session, but preserve task cancellation.
            self._active_calls.pop(chat_id, None)
            if isinstance(e, asyncio.CancelledError):
                raise
            if isinstance(e, CallError):
                raise
            if isinstance(e, Exception):
                raise CallError(f"Failed to join call: {e}") from e
            raise
    
    async def leave_call(self, chat_id: int) -> bool:
        """Leave a call"""
        if chat_id not in self._active_calls:
            return False
        
        try:
            call_session = self._active_calls[chat_id]
            disconnected = await self._connection_manager.disconnect_call(chat_id)
            if not disconnected:
                return False
            call_session['status'] = CallStatus.ENDED

            del self._active_calls[chat_id]

            update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.ENDED,
                message="Left call"
            )
            await self._emit_event('call_left', update)
            
            self._logger.info(f"Left call in chat {chat_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error leaving call {chat_id}: {e}")
            return False
    
    async def change_volume_call(self, chat_id: int, volume: float) -> bool:
        """Change volume for specific call (alias for set_volume)"""
        return await self.set_volume(chat_id, volume)
    
    async def get_participants(self, chat_id: int) -> list:
        """Get list of call participants"""
        if chat_id not in self._active_calls:
            return []
        
        try:
            return await self._connection.get_participants(chat_id)
            
        except Exception as e:
            self._logger.error(f"Error getting participants for chat {chat_id}: {e}")
            return []
    
    async def get_call_status(self, chat_id: int) -> Optional[str]:
        """Get current call status"""
        if chat_id not in self._active_calls:
            return None
        
        call_session = self._active_calls[chat_id]
        return call_session.get('status', CallStatus.IDLE).value
    
    async def is_muted(self, chat_id: int) -> bool:
        """Check if microphone is muted"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        return call_session.get('muted', False)
    
    async def is_video_enabled(self, chat_id: int) -> bool:
        """Check if video is enabled"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        return call_session.get('video_enabled', False)
    async def pause(self, chat_id: int) -> bool:
        """Pause stream"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        if call_session['status'] != CallStatus.PLAYING:
            return False
        
        call_session['status'] = CallStatus.PAUSED
        
        update = CallUpdate(
            chat_id=chat_id,
            status=CallStatus.PAUSED,
            message="Stream paused"
        )
        await self._emit_event('stream_paused', update)
        
        return True
    
    async def resume(self, chat_id: int) -> bool:
        """Resume stream"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        if call_session['status'] != CallStatus.PAUSED:
            return False
        
        call_session['status'] = CallStatus.PLAYING
        
        update = CallUpdate(
            chat_id=chat_id,
            status=CallStatus.PLAYING,
            message="Stream resumed"
        )
        await self._emit_event('stream_resumed', update)
        
        return True
    
    async def set_volume(self, chat_id: int, volume: float) -> bool:
        """Set volume (0.0 to 1.0)"""
        if chat_id not in self._active_calls:
            return False
        
        if not 0.0 <= volume <= 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        
        call_session = self._active_calls[chat_id]
        call_session['volume'] = volume
        
        self._logger.info(f"Set volume to {volume} in chat {chat_id}")
        return True