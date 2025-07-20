"""
Frame Types for Raw Streaming
"""

from typing import Optional, List
from dataclasses import dataclass
import time


@dataclass
class FrameInfo:
    """Frame metadata information"""
    
    timestamp_ms: int
    """Frame timestamp in milliseconds"""
    
    width: int = 0
    """Frame width (for video frames)"""
    
    height: int = 0
    """Frame height (for video frames)"""
    
    rotation: int = 0
    """Frame rotation in degrees"""
    
    sample_rate: int = 0
    """Sample rate (for audio frames)"""
    
    channels: int = 0
    """Number of channels (for audio frames)"""


@dataclass
class Frame:
    """Raw frame data"""
    
    ssrc: int
    """Synchronization source identifier"""
    
    data: bytes
    """Raw frame data"""
    
    info: FrameInfo
    """Frame metadata"""
    
    frame_type: str = "audio"
    """Frame type (audio/video)"""
    
    @property
    def is_video(self) -> bool:
        """Check if frame is video"""
        return self.frame_type == "video"
    
    @property
    def is_audio(self) -> bool:
        """Check if frame is audio"""
        return self.frame_type == "audio"
    
    @property
    def size(self) -> int:
        """Get frame data size"""
        return len(self.data)


@dataclass
class StreamFrames:
    """Collection of frames for a stream"""
    
    chat_id: int
    """Chat ID where frames are from"""
    
    direction: str
    """Stream direction (incoming/outgoing)"""
    
    device: str
    """Device type (microphone/camera/screen)"""
    
    frames: List[Frame]
    """List of frames"""
    
    timestamp: float = None
    """Collection timestamp"""
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if self.timestamp is None:
            self.timestamp = time.time()
    
    @property
    def frame_count(self) -> int:
        """Get number of frames"""
        return len(self.frames)
    
    @property
    def total_size(self) -> int:
        """Get total size of all frames"""
        return sum(frame.size for frame in self.frames)
    
    @property
    def video_frames(self) -> List[Frame]:
        """Get only video frames"""
        return [frame for frame in self.frames if frame.is_video]
    
    @property
    def audio_frames(self) -> List[Frame]:
        """Get only audio frames"""
        return [frame for frame in self.frames if frame.is_audio]