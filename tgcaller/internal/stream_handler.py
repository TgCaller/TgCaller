"""
Stream Handler - Manage media streams and processing
"""

import asyncio
import logging
from typing import Dict, Optional, List, Any
from enum import Enum

from ..types import MediaStream, StreamFrames, Frame, StreamEnded, Device
from ..exceptions import StreamError

logger = logging.getLogger(__name__)


class StreamState(Enum):
    """Stream state enumeration"""
    IDLE = "idle"
    LOADING = "loading"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


class StreamHandler:
    """Handle media stream processing and management"""
    
    def __init__(self, caller):
        self.caller = caller
        self.streams: Dict[int, Dict[str, Any]] = {}
        self.frame_processors: Dict[int, asyncio.Task] = {}
        self.logger = logger
        
        # Stream statistics
        self.stream_stats: Dict[int, Dict[str, Any]] = {}
    
    async def start_stream(
        self, 
        chat_id: int, 
        stream: MediaStream,
        device: Optional[Device] = None
    ) -> bool:
        """Start media stream"""
        try:
            if chat_id in self.streams:
                await self.stop_stream(chat_id)
            
            # Initialize stream data
            stream_data = {
                'stream': stream,
                'device': device,
                'state': StreamState.LOADING,
                'position': 0.0,
                'start_time': asyncio.get_event_loop().time(),
                'frames_processed': 0,
                'bytes_processed': 0
            }
            
            self.streams[chat_id] = stream_data
            self.stream_stats[chat_id] = {
                'start_time': stream_data['start_time'],
                'frames_sent': 0,
                'frames_received': 0,
                'bytes_sent': 0,
                'bytes_received': 0,
                'errors': 0
            }
            
            # Start frame processing
            self.frame_processors[chat_id] = asyncio.create_task(
                self._process_stream_frames(chat_id)
            )
            
            # Update state
            stream_data['state'] = StreamState.PLAYING
            
            self.logger.info(f"Started stream for chat {chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start stream for chat {chat_id}: {e}")
            return False
    
    async def stop_stream(self, chat_id: int) -> bool:
        """Stop media stream"""
        if chat_id not in self.streams:
            return False
        
        try:
            # Cancel frame processor
            if chat_id in self.frame_processors:
                self.frame_processors[chat_id].cancel()
                del self.frame_processors[chat_id]
            
            # Get stream data
            stream_data = self.streams[chat_id]
            stream_data['state'] = StreamState.STOPPED
            
            # Calculate final duration
            duration = asyncio.get_event_loop().time() - stream_data['start_time']
            
            # Emit stream ended event
            device = stream_data.get('device') or Device.from_raw(None)
            stream_ended = StreamEnded(
                chat_id=chat_id,
                stream_type=stream_data['stream'].source,
                device=device,
                duration=duration
            )
            
            await self.caller._emit_event('stream_ended', stream_ended)
            
            # Cleanup
            del self.streams[chat_id]
            
            self.logger.info(f"Stopped stream for chat {chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping stream for chat {chat_id}: {e}")
            return False
    
    async def pause_stream(self, chat_id: int) -> bool:
        """Pause media stream"""
        if chat_id not in self.streams:
            return False
        
        stream_data = self.streams[chat_id]
        if stream_data['state'] != StreamState.PLAYING:
            return False
        
        stream_data['state'] = StreamState.PAUSED
        self.logger.info(f"Paused stream for chat {chat_id}")
        return True
    
    async def resume_stream(self, chat_id: int) -> bool:
        """Resume paused stream"""
        if chat_id not in self.streams:
            return False
        
        stream_data = self.streams[chat_id]
        if stream_data['state'] != StreamState.PAUSED:
            return False
        
        stream_data['state'] = StreamState.PLAYING
        self.logger.info(f"Resumed stream for chat {chat_id}")
        return True
    
    async def seek_stream(self, chat_id: int, position: float) -> bool:
        """Seek to position in stream"""
        if chat_id not in self.streams:
            return False
        
        stream_data = self.streams[chat_id]
        stream_data['position'] = position
        
        self.logger.info(f"Seeked to {position}s in chat {chat_id}")
        return True
    
    async def _process_stream_frames(self, chat_id: int):
        """Process stream frames"""
        try:
            stream_data = self.streams[chat_id]
            frame_count = 0
            
            while stream_data['state'] in [StreamState.PLAYING, StreamState.PAUSED]:
                if stream_data['state'] == StreamState.PAUSED:
                    await asyncio.sleep(0.1)
                    continue
                
                # Simulate frame processing
                frame_data = self._generate_mock_frame(chat_id, frame_count)
                
                if frame_data:
                    # Update statistics
                    stream_data['frames_processed'] += 1
                    stream_data['bytes_processed'] += len(frame_data.data)
                    
                    stats = self.stream_stats[chat_id]
                    stats['frames_sent'] += 1
                    stats['bytes_sent'] += len(frame_data.data)
                    
                    # Emit frame event
                    stream_frames = StreamFrames(
                        chat_id=chat_id,
                        direction="outgoing",
                        device="file",
                        frames=[frame_data]
                    )
                    
                    await self.caller._emit_event('stream_frames', stream_frames)
                
                frame_count += 1
                await asyncio.sleep(1/30)  # 30 FPS
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error processing frames for chat {chat_id}: {e}")
            if chat_id in self.streams:
                self.streams[chat_id]['state'] = StreamState.ERROR
    
    def _generate_mock_frame(self, chat_id: int, frame_number: int) -> Optional[Frame]:
        """Generate mock frame data for testing"""
        try:
            # Create mock frame data
            frame_data = Frame(
                ssrc=12345,
                data=b"mock_frame_data_" + str(frame_number).encode(),
                info=Frame.Info(
                    timestamp_ms=int(asyncio.get_event_loop().time() * 1000),
                    width=1280,
                    height=720,
                    rotation=0
                ),
                frame_type="video"
            )
            
            return frame_data
            
        except Exception as e:
            self.logger.error(f"Error generating mock frame: {e}")
            return None
    
    def get_stream_state(self, chat_id: int) -> Optional[StreamState]:
        """Get current stream state"""
        if chat_id not in self.streams:
            return None
        return self.streams[chat_id]['state']
    
    def get_stream_position(self, chat_id: int) -> Optional[float]:
        """Get current stream position"""
        if chat_id not in self.streams:
            return None
        return self.streams[chat_id]['position']
    
    def get_stream_stats(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get stream statistics"""
        return self.stream_stats.get(chat_id)
    
    def is_streaming(self, chat_id: int) -> bool:
        """Check if chat is currently streaming"""
        if chat_id not in self.streams:
            return False
        return self.streams[chat_id]['state'] == StreamState.PLAYING
    
    async def cleanup_all(self):
        """Cleanup all streams"""
        for chat_id in list(self.streams.keys()):
            await self.stop_stream(chat_id)