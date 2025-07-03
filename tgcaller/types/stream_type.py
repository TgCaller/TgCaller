"""
Stream Type Enumeration
"""

from enum import Enum


class StreamType(Enum):
    """Stream type enumeration for different media types"""
    
    AUDIO = "audio"
    """Audio only stream"""
    
    VIDEO = "video"
    """Video stream (includes audio)"""
    
    SCREEN = "screen"
    """Screen sharing stream"""
    
    MICROPHONE = "microphone"
    """Live microphone input"""
    
    CAMERA = "camera"
    """Live camera input"""
    
    MIXED = "mixed"
    """Mixed audio/video stream"""
    
    RAW = "raw"
    """Raw stream data"""
    
    PIPED = "piped"
    """Piped stream from external source"""
    
    def __str__(self) -> str:
        """String representation"""
        return self.value
    
    @property
    def has_audio(self) -> bool:
        """Check if stream type includes audio"""
        return self in [
            StreamType.AUDIO,
            StreamType.VIDEO,
            StreamType.MICROPHONE,
            StreamType.MIXED,
            StreamType.RAW,
            StreamType.PIPED
        ]
    
    @property
    def has_video(self) -> bool:
        """Check if stream type includes video"""
        return self in [
            StreamType.VIDEO,
            StreamType.SCREEN,
            StreamType.CAMERA,
            StreamType.MIXED,
            StreamType.RAW,
            StreamType.PIPED
        ]
    
    @property
    def is_live(self) -> bool:
        """Check if stream type is live input"""
        return self in [
            StreamType.MICROPHONE,
            StreamType.CAMERA,
            StreamType.SCREEN
        ]