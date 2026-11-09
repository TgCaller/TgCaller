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
        """Start playback through TgCaller's real configured media transport."""
        try:
            if chat_id in self.streams:
                await self.stop_stream(chat_id)

            started = await self.caller.play(chat_id, stream)
            if not started:
                return False

            now = asyncio.get_running_loop().time()
            self.streams[chat_id] = {
                "stream": stream,
                "device": device,
                "state": StreamState.PLAYING,
                "position": 0.0,
                "start_time": now,
                "frames_processed": 0,
                "bytes_processed": 0,
            }
            self.stream_stats[chat_id] = {
                "start_time": now,
                "frames_sent": 0,
                "frames_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0,
                "errors": 0,
            }
            return True
        except Exception as exc:
            self.logger.error("Failed to start real stream for chat %s: %s", chat_id, exc)
            return False

    async def stop_stream(self, chat_id: int) -> bool:
        """Stop playback through TgCaller's configured media transport."""
        stream_data = self.streams.get(chat_id)
        if stream_data is None:
            return False
        try:
            if not await self.caller.stop_stream(chat_id):
                return False
            stream_data["state"] = StreamState.STOPPED
            duration = asyncio.get_running_loop().time() - stream_data["start_time"]
            device = stream_data.get("device") or Device.from_raw(None)
            await self.caller._emit_event(
                "stream_ended",
                StreamEnded(
                    chat_id=chat_id,
                    stream_type=stream_data["stream"].source,
                    device=device,
                    duration=duration,
                ),
            )
            self.streams.pop(chat_id, None)
            return True
        except Exception as exc:
            self.logger.error("Error stopping stream for chat %s: %s", chat_id, exc)
            return False

    async def pause_stream(self, chat_id: int) -> bool:
        """Pause the real transport before updating local stream state."""
        stream_data = self.streams.get(chat_id)
        if stream_data is None or stream_data["state"] != StreamState.PLAYING:
            return False
        if not await self.caller.pause(chat_id):
            return False
        stream_data["state"] = StreamState.PAUSED
        return True

    async def resume_stream(self, chat_id: int) -> bool:
        """Resume the real transport before updating local stream state."""
        stream_data = self.streams.get(chat_id)
        if stream_data is None or stream_data["state"] != StreamState.PAUSED:
            return False
        if not await self.caller.resume(chat_id):
            return False
        stream_data["state"] = StreamState.PLAYING
        return True

    async def seek_stream(self, chat_id: int, position: float) -> bool:
        """Seek only when the real media transport confirms the operation."""
        if chat_id not in self.streams:
            return False
        if not await self.caller.seek(chat_id, position):
            return False
        self.streams[chat_id]["position"] = float(position)
        return True

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
        """Release stream bookkeeping after call transports have been shut down."""
        for chat_id in list(self.streams.keys()):
            try:
                await self.stop_stream(chat_id)
            except Exception as exc:
                self.logger.error("Stream cleanup failed for chat %s: %s", chat_id, exc)
        self.streams.clear()
        self.stream_stats.clear()
        self.frame_processors.clear()
