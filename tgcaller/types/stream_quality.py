"""
Stream Quality Types
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AudioQuality(Enum):
    """Audio quality presets"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    
    @property
    def bitrate(self) -> int:
        """Get bitrate for quality level"""
        quality_map = {
            AudioQuality.LOW: 32000,
            AudioQuality.MEDIUM: 64000,
            AudioQuality.HIGH: 128000,
            AudioQuality.ULTRA: 256000
        }
        return quality_map[self]
    
    @property
    def sample_rate(self) -> int:
        """Get sample rate for quality level"""
        quality_map = {
            AudioQuality.LOW: 24000,
            AudioQuality.MEDIUM: 48000,
            AudioQuality.HIGH: 48000,
            AudioQuality.ULTRA: 48000
        }
        return quality_map[self]


class VideoQuality(Enum):
    """Video quality presets"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    
    @property
    def resolution(self) -> tuple:
        """Get resolution for quality level"""
        quality_map = {
            VideoQuality.LOW: (640, 480),
            VideoQuality.MEDIUM: (1280, 720),
            VideoQuality.HIGH: (1920, 1080),
            VideoQuality.ULTRA: (2560, 1440)
        }
        return quality_map[self]
    
    @property
    def bitrate(self) -> int:
        """Get bitrate for quality level"""
        quality_map = {
            VideoQuality.LOW: 500000,
            VideoQuality.MEDIUM: 1500000,
            VideoQuality.HIGH: 3000000,
            VideoQuality.ULTRA: 6000000
        }
        return quality_map[self]
    
    @property
    def fps(self) -> int:
        """Get frame rate for quality level"""
        quality_map = {
            VideoQuality.LOW: 15,
            VideoQuality.MEDIUM: 30,
            VideoQuality.HIGH: 30,
            VideoQuality.ULTRA: 60
        }
        return quality_map[self]


@dataclass
class QualityConfig:
    """Quality configuration"""
    
    audio_quality: Optional[AudioQuality] = None
    """Audio quality preset"""
    
    video_quality: Optional[VideoQuality] = None
    """Video quality preset"""
    
    custom_audio_bitrate: Optional[int] = None
    """Custom audio bitrate (overrides preset)"""
    
    custom_video_bitrate: Optional[int] = None
    """Custom video bitrate (overrides preset)"""
    
    adaptive_quality: bool = True
    """Enable adaptive quality based on network"""
    
    @property
    def effective_audio_bitrate(self) -> int:
        """Get effective audio bitrate"""
        if self.custom_audio_bitrate:
            return self.custom_audio_bitrate
        elif self.audio_quality:
            return self.audio_quality.bitrate
        else:
            return AudioQuality.MEDIUM.bitrate
    
    @property
    def effective_video_bitrate(self) -> int:
        """Get effective video bitrate"""
        if self.custom_video_bitrate:
            return self.custom_video_bitrate
        elif self.video_quality:
            return self.video_quality.bitrate
        else:
            return VideoQuality.MEDIUM.bitrate