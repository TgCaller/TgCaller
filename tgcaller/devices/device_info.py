"""
Device Information Classes
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """Base device information"""
    
    index: int
    """Device index"""
    
    name: str
    """Device name"""
    
    metadata: Dict[str, Any]
    """Additional device metadata"""
    
    is_video: bool = False
    """Whether device supports video"""
    
    is_default: bool = False
    """Whether this is the default device"""


@dataclass
class InputDevice(DeviceInfo):
    """Audio input device (microphone)"""
    
    channels: int = 1
    """Number of input channels"""
    
    sample_rate: float = 48000.0
    """Default sample rate"""
    
    def __post_init__(self):
        """Set device type"""
        self.is_video = False


@dataclass
class SpeakerDevice(DeviceInfo):
    """Audio output device (speaker)"""
    
    channels: int = 2
    """Number of output channels"""
    
    sample_rate: float = 48000.0
    """Default sample rate"""
    
    def __post_init__(self):
        """Set device type"""
        self.is_video = False


@dataclass
class CameraDevice(DeviceInfo):
    """Video input device (camera)"""
    
    width: int = 640
    """Default video width"""
    
    height: int = 480
    """Default video height"""
    
    fps: float = 30.0
    """Default frame rate"""
    
    def __post_init__(self):
        """Set device type"""
        self.is_video = True


@dataclass
class ScreenDevice(DeviceInfo):
    """Screen/monitor device"""
    
    width: int = 1920
    """Screen width"""
    
    height: int = 1080
    """Screen height"""
    
    x: int = 0
    """Screen X position"""
    
    y: int = 0
    """Screen Y position"""
    
    is_primary: bool = False
    """Whether this is the primary screen"""
    
    def __post_init__(self):
        """Set device type"""
        self.is_video = True