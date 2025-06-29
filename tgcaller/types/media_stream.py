"""
Media Stream Configuration
"""

from typing import Optional, Union
from dataclasses import dataclass
from pathlib import Path

from .audio_config import AudioConfig
from .video_config import VideoConfig


@dataclass
class MediaStream:
    """Media stream configuration"""
    
    source: Union[str, Path]
    """Path to media file or stream URL"""
    
    audio_config: Optional[AudioConfig] = None
    """Audio configuration"""
    
    video_config: Optional[VideoConfig] = None
    """Video configuration"""
    
    repeat: bool = False
    """Repeat the stream when it ends"""
    
    start_time: Optional[float] = None
    """Start time in seconds"""
    
    duration: Optional[float] = None
    """Duration in seconds"""
    
    def __post_init__(self):
        """Initialize default configurations"""
        if self.audio_config is None:
            self.audio_config = AudioConfig()
        
        if self.video_config is None and self.has_video:
            self.video_config = VideoConfig()
    
    @property
    def has_video(self) -> bool:
        """Check if stream has video"""
        if isinstance(self.source, str):
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.webm']
            return any(self.source.lower().endswith(ext) for ext in video_extensions) or \
                   'youtube.com' in self.source or 'youtu.be' in self.source
        return False
    
    @property
    def is_file(self) -> bool:
        """Check if source is a file"""
        return isinstance(self.source, (str, Path)) and Path(self.source).exists()
    
    @property
    def is_url(self) -> bool:
        """Check if source is a URL"""
        return isinstance(self.source, str) and (
            self.source.startswith('http://') or 
            self.source.startswith('https://') or
            self.source.startswith('rtmp://')
        )