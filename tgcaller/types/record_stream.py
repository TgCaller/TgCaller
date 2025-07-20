"""
Recording Stream Types
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time


class RecordingFormat(Enum):
    """Recording format options"""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"
    FLAC = "flac"
    AAC = "aac"


class RecordingStatus(Enum):
    """Recording status"""
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class RecordStream:
    """Recording stream configuration"""
    
    chat_id: int
    """Chat ID being recorded"""
    
    output_path: str
    """Output file path"""
    
    format: RecordingFormat = RecordingFormat.WAV
    """Recording format"""
    
    status: RecordingStatus = RecordingStatus.IDLE
    """Current recording status"""
    
    started_at: Optional[float] = None
    """Recording start timestamp"""
    
    duration: float = 0.0
    """Current recording duration"""
    
    file_size: int = 0
    """Current file size in bytes"""
    
    sample_rate: int = 48000
    """Recording sample rate"""
    
    channels: int = 2
    """Number of audio channels"""
    
    bitrate: int = 128000
    """Recording bitrate"""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional recording metadata"""
    
    def __post_init__(self):
        """Initialize metadata if None"""
        if self.metadata is None:
            self.metadata = {}
    
    def start_recording(self):
        """Start recording"""
        self.status = RecordingStatus.RECORDING
        self.started_at = time.time()
    
    def stop_recording(self):
        """Stop recording"""
        self.status = RecordingStatus.STOPPED
        if self.started_at:
            self.duration = time.time() - self.started_at
    
    def pause_recording(self):
        """Pause recording"""
        if self.status == RecordingStatus.RECORDING:
            self.status = RecordingStatus.PAUSED
    
    def resume_recording(self):
        """Resume recording"""
        if self.status == RecordingStatus.PAUSED:
            self.status = RecordingStatus.RECORDING
    
    @property
    def is_active(self) -> bool:
        """Check if recording is active"""
        return self.status == RecordingStatus.RECORDING
    
    @property
    def current_duration(self) -> float:
        """Get current recording duration"""
        if self.started_at and self.status == RecordingStatus.RECORDING:
            return time.time() - self.started_at
        return self.duration
    
    @property
    def file_extension(self) -> str:
        """Get file extension for format"""
        return f".{self.format.value}"