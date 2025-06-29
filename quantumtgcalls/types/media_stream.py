"""
Media Stream Type
"""

from typing import Optional, Union
from dataclasses import dataclass
from pathlib import Path

from .audio_parameters import AudioParameters
from .video_parameters import VideoParameters


@dataclass
class MediaStream:
    """Media stream configuration"""
    
    path: Union[str, Path]
    """Path to media file or stream URL"""
    
    audio_parameters: Optional[AudioParameters] = None
    """Audio parameters"""
    
    video_parameters: Optional[VideoParameters] = None
    """Video parameters"""
    
    repeat: bool = False
    """Repeat the stream when it ends"""
    
    start_time: Optional[float] = None
    """Start time in seconds"""
    
    duration: Optional[float] = None
    """Duration in seconds"""
    
    def __post_init__(self):
        """Initialize default parameters"""
        if self.audio_parameters is None:
            self.audio_parameters = AudioParameters()
        
        if self.video_parameters is None and self._has_video():
            self.video_parameters = VideoParameters()
    
    def _has_video(self) -> bool:
        """Check if stream has video"""
        if isinstance(self.path, str):
            # Check for video file extensions or streaming URLs
            video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.webm', '.flv']
            return any(self.path.lower().endswith(ext) for ext in video_extensions) or \
                   'youtube.com' in self.path or 'youtu.be' in self.path
        return False
    
    @property
    def is_file(self) -> bool:
        """Check if path is a file"""
        return isinstance(self.path, (str, Path)) and Path(self.path).exists()
    
    @property
    def is_url(self) -> bool:
        """Check if path is a URL"""
        return isinstance(self.path, str) and (
            self.path.startswith('http://') or 
            self.path.startswith('https://') or
            self.path.startswith('rtmp://') or
            self.path.startswith('rtsp://')
        )