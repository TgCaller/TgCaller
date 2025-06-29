"""
Video Configuration
"""

from typing import Tuple
from dataclasses import dataclass


@dataclass
class VideoConfig:
    """Video configuration for calls"""
    
    width: int = 1280
    """Video width in pixels"""
    
    height: int = 720
    """Video height in pixels"""
    
    fps: int = 30
    """Video frame rate"""
    
    bitrate: int = 1000000
    """Video bitrate in bps"""
    
    codec: str = "h264"
    """Video codec (h264, vp8)"""
    
    hardware_acceleration: bool = True
    """Enable hardware acceleration"""
    
    def __post_init__(self):
        """Validate parameters"""
        if self.width < 320 or self.width > 1920:
            raise ValueError("Width must be between 320 and 1920")
        
        if self.height < 240 or self.height > 1080:
            raise ValueError("Height must be between 240 and 1080")
        
        if self.fps not in [15, 24, 30, 60]:
            raise ValueError("FPS must be 15, 24, 30, or 60")
        
        if self.bitrate < 100000 or self.bitrate > 5000000:
            raise ValueError("Bitrate must be between 100000 and 5000000")
        
        if self.codec not in ["h264", "vp8"]:
            raise ValueError("Codec must be h264 or vp8")
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Get resolution as tuple"""
        return (self.width, self.height)
    
    @classmethod
    def hd_720p(cls) -> 'VideoConfig':
        """720p HD preset"""
        return cls(width=1280, height=720, fps=30, bitrate=1500000)
    
    @classmethod
    def full_hd_1080p(cls) -> 'VideoConfig':
        """1080p Full HD preset"""
        return cls(width=1920, height=1080, fps=30, bitrate=3000000)
    
    @classmethod
    def low_quality(cls) -> 'VideoConfig':
        """Low quality preset for poor connections"""
        return cls(width=640, height=480, fps=15, bitrate=500000)