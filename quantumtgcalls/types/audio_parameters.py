"""
Audio Parameters Type
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class AudioParameters:
    """Audio parameters for calls"""
    
    bitrate: int = 48000
    """Audio bitrate in bps"""
    
    channels: int = 2
    """Number of audio channels (1=mono, 2=stereo)"""
    
    sample_rate: int = 48000
    """Audio sample rate in Hz"""
    
    codec: str = "opus"
    """Audio codec (opus, aac, mp3)"""
    
    noise_cancellation: bool = False
    """Enable AI noise cancellation"""
    
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
        
        if self.codec not in ["opus", "aac", "mp3"]:
            raise ValueError("Codec must be opus, aac, or mp3")