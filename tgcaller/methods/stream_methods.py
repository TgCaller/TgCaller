"""
Stream Management Methods
"""

import asyncio
from typing import Union, Optional
from pathlib import Path

from ..types import MediaStream, AudioConfig, VideoConfig, CallUpdate, CallStatus
from ..exceptions import StreamError, MediaError


class StreamMethods:
    """Stream management methods"""
    
    async def play(
        self,
        chat_id: int,
        source: Union[str, Path, MediaStream],
        audio_config: Optional[AudioConfig] = None,
        video_config: Optional[VideoConfig] = None
    ) -> bool:
        """
        Play media in call
        
        Args:
            chat_id: Chat ID
            source: Media source
            audio_config: Audio configuration
            video_config: Video configuration
            
        Returns:
            True if successful
        """
        # Auto-join if not in call
        if chat_id not in self._active_calls:
            await self.join_call(chat_id, audio_config, video_config)
        
        try:
            # Create MediaStream if needed
            if not isinstance(source, MediaStream):
                stream = MediaStream(
                    source=source,
                    audio_config=audio_config,
                    video_config=video_config
                )
            else:
                stream = source
            
            # Validate media
            await self._validate_media(stream)
            
            # Update call session
            call_session = self._active_calls[chat_id]
            call_session['current_stream'] = stream
            call_session['status'] = CallStatus.PLAYING
            
            # Start playback simulation
            asyncio.create_task(self._simulate_playback(chat_id, stream))
            
            # Emit event
            update = CallUpdate(
                chat_id=chat_id,
                status=CallStatus.PLAYING,
                message=f"Playing: {stream.source}"
            )
            await self._emit_event('stream_started', update)
            
            self._logger.info(f"Started playing {stream.source} in chat {chat_id}")
            return True
            
        except Exception as e:
            raise StreamError(f"Failed to play media: {e}")
    
    async def stop_stream(self, chat_id: int) -> bool:
        """Stop current stream"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        
        if 'current_stream' not in call_session:
            return False
        
        call_session['status'] = CallStatus.CONNECTED
        call_session.pop('current_stream', None)
        
        update = CallUpdate(
            chat_id=chat_id,
            status=CallStatus.CONNECTED,
            message="Stream stopped"
        )
        await self._emit_event('stream_stopped', update)
        
        return True
    
    async def pause(self, chat_id: int) -> bool:
        """Pause current stream"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        
        if 'current_stream' not in call_session:
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
        """Resume paused stream"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        
        if 'current_stream' not in call_session:
            return False
        
        if call_session.get('status') != CallStatus.PAUSED:
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
        """Set volume level (0.0 to 1.0)"""
        if not 0.0 <= volume <= 1.0:
            raise ValueError("Volume must be between 0.0 and 1.0")
        
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        call_session['volume'] = volume
        
        self._logger.info(f"Set volume to {volume} in chat {chat_id}")
        return True
    
    async def seek(self, chat_id: int, position: float) -> bool:
        """Seek to position in stream"""
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        
        if 'current_stream' not in call_session:
            return False
        
        call_session['position'] = position
        self._logger.info(f"Seeked to {position}s in chat {chat_id}")
        return True
    
    async def get_position(self, chat_id: int) -> Optional[float]:
        """Get current stream position"""
        if chat_id not in self._active_calls:
            return None
        
        call_session = self._active_calls[chat_id]
        return call_session.get('position', 0.0)