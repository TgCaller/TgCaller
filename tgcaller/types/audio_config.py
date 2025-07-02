"""
Audio Configuration
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """
    Audio configuration for calls
    
    Example:
        ```python
        # High quality audio
        config = AudioConfig.high_quality()
        
        # Custom configuration
        config = AudioConfig(
            bitrate=128000,
            sample_rate=48000,
            channels=2,
            noise_suppression=True
        )
        ```
    """
    
    bitrate: int = 48000
    """Audio bitrate in bps (8000-320000)"""
    
    channels: int = 2
    """Number of audio channels (1=mono, 2=stereo)"""
    
    sample_rate: int = 48000
    """Audio sample rate in Hz (8000, 16000, 24000, 48000)"""
    
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
        if not isinstance(self.bitrate, int) or self.bitrate < 8000 or self.bitrate > 320000:
            raise ValueError("Bitrate must be an integer between 8000 and 320000")
        
        if self.channels not in [1, 2]:
            raise ValueError("Channels must be 1 (mono) or 2 (stereo)")
        
        if self.sample_rate not in [8000, 16000, 24000, 48000]:
            raise ValueError("Sample rate must be 8000, 16000, 24000, or 48000")
        
        if self.codec not in ["opus", "aac"]:
            raise ValueError("Codec must be 'opus' or 'aac'")
    
    @classmethod
    def high_quality(cls) -> 'AudioConfig':
        """
        High quality audio preset
        
        Returns:
            AudioConfig with 128kbps, stereo, 48kHz
        """
        return cls(
            bitrate=128000,
            sample_rate=48000,
            channels=2,
            noise_suppression=True,
            echo_cancellation=True
        )
    
    @classmethod
    def low_bandwidth(cls) -> 'AudioConfig':
        """
        Low bandwidth audio preset
        
        Returns:
            AudioConfig with 32kbps, mono, 24kHz
        """
        return cls(
            bitrate=32000,
            sample_rate=24000,
            channels=1,
            noise_suppression=False,
            echo_cancellation=True
        )
    
    @classmethod
    def voice_call(cls) -> 'AudioConfig':
        """
        Voice call optimized preset
        
        Returns:
            AudioConfig optimized for voice calls
        """
        return cls(
            bitrate=64000,
            sample_rate=48000,
            channels=1,
            noise_suppression=True,
            echo_cancellation=True,
            auto_gain_control=True
        )