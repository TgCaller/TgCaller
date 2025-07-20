"""
Device Types for Stream Sources
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any


class DeviceType(Enum):
    """Device type enumeration"""
    MICROPHONE = "microphone"
    SPEAKER = "speaker"
    CAMERA = "camera"
    SCREEN = "screen"
    FILE = "file"
    STREAM = "stream"
    UNKNOWN = "unknown"


class Direction(Enum):
    """Stream direction enumeration"""
    INCOMING = "incoming"
    OUTGOING = "outgoing"
    BIDIRECTIONAL = "bidirectional"
    
    @classmethod
    def from_raw(cls, raw_mode):
        """Convert from raw stream mode"""
        # This would map from ntgcalls StreamMode
        return cls.OUTGOING  # Default mapping


@dataclass
class Device:
    """Device information for streaming"""
    
    device_type: DeviceType
    """Type of device"""
    
    device_id: Optional[str] = None
    """Device identifier"""
    
    name: Optional[str] = None
    """Device name"""
    
    capabilities: Optional[Dict[str, Any]] = None
    """Device capabilities"""
    
    def __post_init__(self):
        """Initialize capabilities if None"""
        if self.capabilities is None:
            self.capabilities = {}
    
    @classmethod
    def from_raw(cls, raw_device):
        """Create Device from raw device data"""
        # This would map from ntgcalls StreamDevice
        return cls(
            device_type=DeviceType.UNKNOWN,
            device_id="unknown",
            name="Unknown Device"
        )
    
    @property
    def is_input(self) -> bool:
        """Check if device is input device"""
        return self.device_type in [DeviceType.MICROPHONE, DeviceType.CAMERA]
    
    @property
    def is_output(self) -> bool:
        """Check if device is output device"""
        return self.device_type in [DeviceType.SPEAKER, DeviceType.SCREEN]
    
    @property
    def supports_audio(self) -> bool:
        """Check if device supports audio"""
        return self.device_type in [
            DeviceType.MICROPHONE, 
            DeviceType.SPEAKER, 
            DeviceType.FILE, 
            DeviceType.STREAM
        ]
    
    @property
    def supports_video(self) -> bool:
        """Check if device supports video"""
        return self.device_type in [
            DeviceType.CAMERA, 
            DeviceType.SCREEN, 
            DeviceType.FILE, 
            DeviceType.STREAM
        ]


@dataclass
class ExternalMedia:
    """External media source configuration"""
    
    source_path: str
    """Path to media source"""
    
    device: Device
    """Device information"""
    
    loop: bool = False
    """Whether to loop the media"""
    
    start_time: float = 0.0
    """Start time in seconds"""
    
    duration: Optional[float] = None
    """Duration limit in seconds"""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata"""
    
    def __post_init__(self):
        """Initialize metadata if None"""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_file(self) -> bool:
        """Check if source is a file"""
        return not self.source_path.startswith(('http://', 'https://', 'rtmp://'))
    
    @property
    def is_stream(self) -> bool:
        """Check if source is a stream URL"""
        return self.source_path.startswith(('http://', 'https://', 'rtmp://'))