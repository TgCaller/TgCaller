"""
Video Parameters Type
"""

from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class VideoParameters:
    """Video parameters for calls"""
    
    width: int = 1280
    """Video width in pixels"""
    
    height: int = 720
    """Video height in pixels"""
    
    frame_rate: int = 30
    """Video frame rate (fps)"""
    
    bitrate: int = 1000000
    """Video bitrate in bps"""
    
    codec: str = "h264"
    """Video codec (h264, vp8, vp9)"""
    
    hardware_acceleration: bool = True
    """Enable hardware acceleration"""
    
    adaptive_bitrate: bool = True
    """Enable adaptive bitrate streaming"""
    
    def __post_init__(self):
        """Validate parameters"""
        if self.width < 320 or self.width > 3840:
            raise ValueError("Width must be between 320 and 3840")
        
        if self.height < 240 or self.height > 2160:
            raise ValueError("Height must be between 240 and 2160")
        
        if self.frame_rate not in [15, 24, 30, 60]:
            raise ValueError("Frame rate must be 15, 24, 30, or 60")
        
        if self.bitrate < 100000 or self.bitrate > 10000000:
            raise ValueError("Bitrate must be between 100000 and 10000000")
        
        if self.codec not in ["h264", "vp8", "vp9"]:
            raise ValueError("Codec must be h264, vp8, or vp9")
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Get resolution as tuple"""
        return (self.width, self.height)
    
    @classmethod
    def preset_720p(cls) -> 'VideoParameters':
        """720p preset"""
        return cls(width=1280, height=720, frame_rate=30, bitrate=1500000)
    
    @classmethod
    def preset_1080p(cls) -> 'VideoParameters':
        """1080p preset"""
        return cls(width=1920, height=1080, frame_rate=30, bitrate=3000000)
    
    @classmethod
    def preset_4k(cls) -> 'VideoParameters':
        """4K preset"""
        return cls(width=3840, height=2160, frame_rate=30, bitrate=8000000)