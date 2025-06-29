"""
Stream Methods - Following pytgcalls patterns
"""

import asyncio
from typing import Union, Optional
from pathlib import Path

from ..types import MediaStream, AudioParameters, VideoParameters, CallUpdate, CallStatus
from ..exceptions import StreamError, MediaError


class StreamMethods:
    """Stream management methods"""
    
    async def play(
        self,
        chat_id: int,
        source: Union[str, Path, MediaStream],
        audio_parameters: Optional[AudioParameters] = None,
        video_parameters: Optional[VideoParameters] = None
    ) -> bool:
        """
        Play media in call
        
        Args:
            chat_id: Chat ID
            source: Media source (file path, URL, or MediaStream)
            audio_parameters: Audio configuration
            video_parameters: Video configuration
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            # Auto-join if not in call
            await self.join_call(chat_id, audio_parameters, video_parameters)
        
        try:
            # Create MediaStream if needed
            if not isinstance(source, MediaStream):
                stream = MediaStream(
                    path=source,
                    audio_parameters=audio_parameters,
                    video_parameters=video_parameters
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
                message=f"Playing: {stream.path}"
            )
            await self._emit_event('stream_started', update)
            
            self._logger.info(f"Started playing {stream.path} in chat {chat_id}")
            return True
            
        except Exception as e:
            raise StreamError(f"Failed to play media: {e}")
    
    async def stop(self, chat_id: int) -> bool:
        """
        Stop current stream
        
        Args:
            chat_id: Chat ID
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            return False
        
        call_session = self._active_calls[chat_id]
        
        if 'current_stream' not in call_session:
            return False
        
        # Stop playback
        call_session['status'] = CallStatus.CONNECTED
        call_session.pop('current_stream', None)
        
        # Emit event
        update = CallUpdate(
            chat_id=chat_id,
            status=CallStatus.CONNECTED,
            message="Stream stopped"
        )
        await self._emit_event('stream_stopped', update)
        
        self._logger.info(f"Stopped stream in chat {chat_id}")
        return True
    
    async def change_stream(
        self,
        chat_id: int,
        source: Union[str, Path, MediaStream]
    ) -> bool:
        """
        Change current stream
        
        Args:
            chat_id: Chat ID
            source: New media source
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            raise StreamError(f"Not in call for chat {chat_id}")
        
        # Stop current stream
        await self.stop(chat_id)
        
        # Start new stream
        return await self.play(chat_id, source)
    
    async def seek(self, chat_id: int, position: float) -> bool:
        """
        Seek to position in stream
        
        Args:
            chat_id: Chat ID
            position: Position in seconds
            
        Returns:
            True if successful
        """
        if chat_id not in self._active_calls:
            raise StreamError(f"Not in call for chat {chat_id}")
        
        call_session = self._active_calls[chat_id]
        
        if 'current_stream' not in call_session:
            raise StreamError("No active stream")
        
        # Update position
        call_session['position'] = position
        
        self._logger.info(f"Seeked to {position}s in chat {chat_id}")
        return True
    
    async def get_stream_time(self, chat_id: int) -> Optional[float]:
        """
        Get current stream time
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Current position in seconds
        """
        if chat_id not in self._active_calls:
            return None
        
        call_session = self._active_calls[chat_id]
        return call_session.get('position', 0.0)
    
    async def _validate_media(self, stream: MediaStream):
        """Validate media stream"""
        if stream.is_file:
            if not Path(stream.path).exists():
                raise MediaError(f"File not found: {stream.path}")
        elif not stream.is_url:
            raise MediaError(f"Invalid media source: {stream.path}")
    
    async def _simulate_playback(self, chat_id: int, stream: MediaStream):
        """Simulate media playback"""
        try:
            # Simulate playback duration (10 seconds for demo)
            duration = stream.duration or 10.0
            
            for i in range(int(duration)):
                if chat_id not in self._active_calls:
                    break
                
                call_session = self._active_calls[chat_id]
                
                if call_session.get('status') != CallStatus.PLAYING:
                    break
                
                # Update position
                call_session['position'] = i + 1
                
                await asyncio.sleep(1)
            
            # Stream ended
            if chat_id in self._active_calls:
                call_session = self._active_calls[chat_id]
                
                if stream.repeat:
                    # Restart stream
                    await self.play(chat_id, stream)
                else:
                    # End stream
                    call_session['status'] = CallStatus.CONNECTED
                    call_session.pop('current_stream', None)
                    
                    update = CallUpdate(
                        chat_id=chat_id,
                        status=CallStatus.CONNECTED,
                        message="Stream ended"
                    )
                    await self._emit_event('stream_end', update)
                    
        except Exception as e:
            self._logger.error(f"Playback error in chat {chat_id}: {e}")