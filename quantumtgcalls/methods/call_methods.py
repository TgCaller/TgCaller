"""
Call Methods - Following pytgcalls patterns
"""

import asyncio
from typing import Optional, Union

from ..types import AudioParameters, VideoParameters, CallUpdate, CallStatus
from ..exceptions import CallError, ConnectionError


class CallMethods:
    """Call management methods"""
    
    async def join_call(
        self,
        chat_id: int,
        audio_parameters: Optional[AudioParameters] = None,
        video_parameters: Optional[VideoParameters] = None,
        invite_hash: Optional[str] = None
    ) -> bool:
        """
        Join a voice/video call
        
        Args:
            chat_id: Chat ID to join
            audio_parameters: Audio configuration
            video_parameters: Video configuration (optional)
            invite_hash: Invite hash for private calls
            
        Returns:
            True if successful
            
        Raises:
            CallError: If join fails
        """
        if not self._is_connected:
            raise ConnectionError("QuantumTgCalls not started")
        
        if chat_id in self._active_calls:
            raise CallError(f"Already in call for chat {chat_id}")
        
        try:
            # Set default parameters
            if audio_parameters is None:
                audio_parameters = AudioParameters()
            
            # Create call session
            call_session = {
                'chat_id': chat_id,
                'audio_parameters': audio_parameters,
                'video_parameters': video_parameters,
                'status': CallStatus.CONNECTING,
                'invite_hash': invite_hash
            }
            
            self._active_calls[chat_id] = call_session
            
            # Simulate connection process
            await asyncio.sleep(0.5)  # Connection delay
            
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
            # Cleanup on error
            self._active_calls.pop(chat_id, None)
            raise CallError(f"Failed to join call: {e}")
    
    async def leave_call(self, chat_id: int) -> bool:
        """
        Leave a voice/video call
        
        Args:
            chat_id: Chat ID to leave
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            return False
        
        try:
            call_session = self._active_calls[chat_id]
            
            # Update status
            call_session['status'] = CallStatus.ENDED
            
            # Cleanup
            del self._active_calls[chat_id]
            
            # Emit event
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
    
    async def pause_stream(self, chat_id: int) -> bool:
        """
        Pause stream in call
        
        Args:
            chat_id: Chat ID
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            raise CallError(f"Not in call for chat {chat_id}")
        
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
    
    async def resume_stream(self, chat_id: int) -> bool:
        """
        Resume stream in call
        
        Args:
            chat_id: Chat ID
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            raise CallError(f"Not in call for chat {chat_id}")
        
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
    
    async def mute_stream(self, chat_id: int) -> bool:
        """
        Mute audio stream
        
        Args:
            chat_id: Chat ID
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            raise CallError(f"Not in call for chat {chat_id}")
        
        call_session = self._active_calls[chat_id]
        call_session['muted'] = True
        
        self._logger.info(f"Muted stream in chat {chat_id}")
        return True
    
    async def unmute_stream(self, chat_id: int) -> bool:
        """
        Unmute audio stream
        
        Args:
            chat_id: Chat ID
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            raise CallError(f"Not in call for chat {chat_id}")
        
        call_session = self._active_calls[chat_id]
        call_session['muted'] = False
        
        self._logger.info(f"Unmuted stream in chat {chat_id}")
        return True