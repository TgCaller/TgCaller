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
        """Join a Telegram group call using the configured real call backend."""
        if not self._is_connected:
            raise ConnectionError("TgCaller not started")
        if chat_id in self._active_calls:
            return True

        backend = self._require_calls_backend()
        audio_config = audio_config or AudioConfig()
        try:
            # PyTgCalls accepts a None stream to join/start the call without
            # starting media playback.
            await backend.play(chat_id, None)
            call_session = {
                "chat_id": chat_id,
                "audio_config": audio_config,
                "video_config": video_config,
                "status": CallStatus.CONNECTED,
            }
            self._active_calls[chat_id] = call_session
            update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.CONNECTED,
                message="Joined Telegram call",
            )
            await self._emit_event("call_joined", update)
            self._logger.info("Joined Telegram call in chat %s", chat_id)
            return True
        except Exception as exc:
            self._active_calls.pop(chat_id, None)
            raise CallError(f"Failed to join Telegram call: {exc}") from exc

    async def leave_call(self, chat_id: int) -> bool:
        """Leave a Telegram call through the configured real backend."""
        if chat_id not in self._active_calls:
            return False
        try:
            backend = self._require_calls_backend()
            await backend.leave_call(chat_id)
            self._active_calls.pop(chat_id, None)
            update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.ENDED,
                message="Left Telegram call",
            )
            await self._emit_event("call_left", update)
            self._logger.info("Left Telegram call in chat %s", chat_id)
            return True
        except Exception as exc:
            self._logger.error("Error leaving call %s: %s", chat_id, exc)
            return False

    async def change_volume_call(self, chat_id: int, volume: float) -> bool:
        """Change volume for specific call (alias for set_volume)"""
        return await self.set_volume(chat_id, volume)
    
    async def get_participants(self, chat_id: int) -> list:
        """Get list of call participants"""
        if chat_id not in self._active_calls:
            return []
        
        backend = self._require_calls_backend()
        get_participants = getattr(backend, "get_participants", None)
        if not callable(get_participants):
            raise CallError("The configured call backend does not support participants")
        return await get_participants(chat_id)
    
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
        
        backend = self._require_calls_backend()
        change_volume = getattr(backend, "change_volume_call", None)
        if not callable(change_volume):
            raise CallError("The configured call backend does not support volume control")
        await change_volume(chat_id, int(round(volume * 100)))
        self._active_calls[chat_id]["volume"] = volume
        self._logger.info("Set volume to %s in chat %s", volume, chat_id)
        return True