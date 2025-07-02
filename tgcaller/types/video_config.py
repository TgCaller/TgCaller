"""
Video Configuration
"""

from typing import Tuple
from dataclasses import dataclass


@dataclass
class VideoConfig:
    """
    Video configuration for calls
    
    Example:
        ```python
        # HD 720p video
        config = VideoConfig.hd_720p()
        
        # Custom configuration
        config = VideoConfig(
            width=1920,
            height=1080,
            fps=30,
            bitrate=2000000
        )
        ```
    """
    
    width: int = 1280
    """Video width in pixels (320-1920)"""
    
    height: int = 720
    """Video height in pixels (240-1080)"""
    
    fps: int = 30
    """Video frame rate (15, 24, 30, 60)"""
    
    bitrate: int = 1000000
    """Video bitrate in bps (100000-5000000)"""
    
    codec: str = "h264"
    """Video codec (h264, vp8)"""
    
    hardware_acceleration: bool = True
    """Enable hardware acceleration"""
    
    def __post_init__(self):
        """Validate parameters"""
        if not isinstance(self.width, int) or self.width < 320 or self.width > 1920:
            raise ValueError("Width must be an integer between 320 and 1920")
        
        if not isinstance(self.height, int) or self.height < 240 or self.height > 1080:
            raise ValueError("Height must be an integer between 240 and 1080")
        
        if self.fps not in [15, 24, 30, 60]:
            raise ValueError("FPS must be 15, 24, 30, or 60")
        
        if not isinstance(self.bitrate, int) or self.bitrate < 100000 or self.bitrate > 5000000:
            raise ValueError("Bitrate must be an integer between 100000 and 5000000")
        
        if self.codec not in ["h264", "vp8"]:
            raise ValueError("Codec must be 'h264' or 'vp8'")
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Get resolution as (width, height) tuple"""
        return (self.width, self.height)
    
    @classmethod
    def hd_720p(cls) -> 'VideoConfig':
        """
        720p HD preset
        
        Returns:
            VideoConfig with 1280x720, 30fps, 1.5Mbps
        """
        return cls(
            width=1280,
            height=720,
            fps=30,
            bitrate=1500000
        )
    
    @classmethod
    def full_hd_1080p(cls) -> 'VideoConfig':
        """
        1080p Full HD preset
        
        Returns:
            VideoConfig with 1920x1080, 30fps, 3Mbps
        """
        return cls(
            width=1920,
            height=1080,
            fps=30,
            bitrate=3000000
        )
    
    @classmethod
    def low_quality(cls) -> 'VideoConfig':
        """
        Low quality preset for poor connections
        
        Returns:
            VideoConfig with 640x480, 15fps, 500kbps
        """
        return cls(
            width=640,
            height=480,
            fps=15,
            bitrate=500000
        )
    
    @classmethod
    def mobile_optimized(cls) -> 'VideoConfig':
        """
        Mobile optimized preset
        
        Returns:
            VideoConfig optimized for mobile devices
        """
        return cls(
            width=854,
            height=480,
            fps=24,
            bitrate=800000
        )