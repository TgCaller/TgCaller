"""
Stream Ended Event Types
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum

from .device import Device


class StreamEndReason(Enum):
    """Reason why stream ended"""
    FINISHED = "finished"
    STOPPED = "stopped"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    REPLACED = "replaced"
    TIMEOUT = "timeout"


@dataclass
class StreamEnded:
    """Stream ended event information"""
    
    chat_id: int
    """Chat ID where stream ended"""
    
    stream_type: str
    """Type of stream that ended"""
    
    device: Device
    """Device that was streaming"""
    
    reason: StreamEndReason = StreamEndReason.FINISHED
    """Reason why stream ended"""
    
    duration: Optional[float] = None
    """Total stream duration"""
    
    error_message: Optional[str] = None
    """Error message if reason is ERROR"""
    
    metadata: Optional[dict] = None
    """Additional metadata"""
    
    def __post_init__(self):
        """Initialize metadata if None"""
        if self.metadata is None:
            self.metadata = {}
    
    class Type:
        """Stream type constants for compatibility"""
        AUDIO = "audio"
        VIDEO = "video"
        SCREEN = "screen"
        MICROPHONE = "microphone"
        CAMERA = "camera"
        
        @classmethod
        def from_raw(cls, raw_type):
            """Convert from raw stream type"""
            # This would map from ntgcalls StreamType
            return cls.AUDIO  # Default mapping
    
    @property
    def is_error(self) -> bool:
        """Check if stream ended due to error"""
        return self.reason == StreamEndReason.ERROR
    
    @property
    def was_successful(self) -> bool:
        """Check if stream ended successfully"""
        return self.reason in [StreamEndReason.FINISHED, StreamEndReason.STOPPED]