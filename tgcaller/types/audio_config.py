"""
Audio Configuration
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Audio configuration for calls"""
    
    bitrate: int = 48000
    """Audio bitrate in bps"""
    
    channels: int = 2
    """Number of audio channels (1=mono, 2=stereo)"""
    
    sample_rate: int = 48000
    """Audio sample rate in Hz"""
    
    codec: str = "opus"
    """Audio codec (opus, aac)"""
    
    noise_suppression: bool = False
    """Enable noise suppression"""
    
    echo_cancellation: bool = True
    """Enable echo cancellation"""
    
    auto_gain_control: bool = True
    """Enable automatic gain control"""
    
    def __post_init__(self):
        """Validate parameters"""
        if self.bitrate < 8000 or self.bitrate > 320000:
            raise ValueError("Bitrate must be between 8000 and 320000")
        
        if self.channels not in [1, 2]:
            raise ValueError("Channels must be 1 (mono) or 2 (stereo)")
        
        if self.sample_rate not in [8000, 16000, 24000, 48000]:
            raise ValueError("Sample rate must be 8000, 16000, 24000, or 48000")
        
        if self.codec not in ["opus", "aac"]:
            raise ValueError("Codec must be opus or aac")
    
    @classmethod
    def high_quality(cls) -> 'AudioConfig':
        """High quality audio preset"""
        return cls(bitrate=128000, sample_rate=48000, channels=2)
    
    @classmethod
    def low_bandwidth(cls) -> 'AudioConfig':
        """Low bandwidth audio preset"""
        return cls(bitrate=32000, sample_rate=24000, channels=1)