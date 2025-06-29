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
            # Set default parameters
            if audio_config is None:
                audio_config = AudioConfig()
            
            # Create call session
            call_session = {
                'chat_id': chat_id,
                'audio_config': audio_config,
                'video_config': video_config,
                'status': CallStatus.CONNECTING
            }
            
            self._active_calls[chat_id] = call_session
            
            # Simulate connection
            await asyncio.sleep(0.5)
            
            # Update status
            call_session['status'] = CallStatus.CONNECTED
            
            # Emit event
            update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.CONNECTED,
                message="Successfully joined call"
            )
            await self._emit_event('call_joined', update)
            
            self._logger.info(f"Joined call in chat {chat_id}")
            return True
            
        except Exception as e:
            self._active_calls.pop(chat_id, None)
            raise CallError(f"Failed to join call: {e}")
    
    async def leave_call(self, chat_id: int) -> bool:
        """Leave a call"""
        if chat_id not in self._active_calls:
            return False
        
        try:
            call_session = self._active_calls[chat_id]
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