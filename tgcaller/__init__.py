"""
TgCaller - Modern Telegram Group Calls Library
Copyright (C) 2024 TgCaller Team

A simple, fast, and reliable library for Telegram voice and video calls
with advanced features like screen sharing, transcription, and more.
"""

__version__ = "1.0.3"
__author__ = "TgCaller Team"
__email__ = "team@tgcaller.dev"
__license__ = "MIT"
__description__ = "Modern, fast, and reliable Telegram group calls library with advanced features"

from .client import TgCaller
from .types import (
    AudioConfig,
    VideoConfig,
    MediaStream,
    CallUpdate,
    CallStatus,
    StreamType,
    GroupCallParticipant,
    UpdatedGroupCallParticipant,
    ParticipantAction,
    VideoInfo,
    AudioQuality,
    VideoQuality,
    QualityConfig,
    Frame,
    FrameInfo,
    StreamFrames,
    Device,
    DeviceType,
    Direction,
    ExternalMedia,
    RecordStream,
    RecordingFormat,
    RecordingStatus,
    StreamEnded,
    StreamEndReason,
)
from .exceptions import (
    TgCallerError,
    ConnectionError,
    MediaError,
    CallError,
    StreamError,
    ConfigurationError,
)
from .api import CustomAPIServer, on_custom_update
from .devices import MediaDevices, DeviceInfo, InputDevice, SpeakerDevice, CameraDevice, ScreenDevice
from .handlers.event_system import Filters, BaseFilter, and_filter, or_filter
from .utilities import CpuMonitor, PingMonitor, CallHolder, PeerResolver
from .internal import ConnectionManager, CacheManager, StreamHandler, CallHandler, RetryManager
from . import streaming

# Advanced features (optional imports)
try:
    from . import advanced
    __all_advanced__ = [
        "BridgedCallManager",
        "MicrophoneCapture",
        "CustomAPIHandler", 
        "AudioFilters",
        "VideoFilters",
        "ScreenShare",
        "WhisperTranscription",
        "YouTubeDownloader",
        "AdvancedYouTubeStreamer",
    ]
except ImportError:
    advanced = None
    __all_advanced__ = []

__all__ = [
    # Main client
    "TgCaller",
    
    # Configuration types
    "AudioConfig",
    "VideoConfig", 
    "MediaStream",
    
    # Update types
    "CallUpdate",
    "CallStatus",
    "StreamType",
    
    # Participant types
    "GroupCallParticipant",
    "UpdatedGroupCallParticipant",
    "ParticipantAction",
    "VideoInfo",
    
    # Quality types
    "AudioQuality",
    "VideoQuality", 
    "QualityConfig",
    
    # Frame types
    "Frame",
    "FrameInfo",
    "StreamFrames",
    
    # Device types
    "Device",
    "DeviceType",
    "Direction",
    "ExternalMedia",
    
    # Recording types
    "RecordStream",
    "RecordingFormat",
    "RecordingStatus",
    
    # Stream event types
    "StreamEnded",
    "StreamEndReason",
    
    # Exceptions
    "TgCallerError",
    "ConnectionError",
    "MediaError",
    "CallError",
    "StreamError",
    "ConfigurationError",
    
    # API System
    "CustomAPIServer",
    "on_custom_update",
    
    # Device System
    "MediaDevices",
    "DeviceInfo",
    "InputDevice",
    "SpeakerDevice", 
    "CameraDevice",
    "ScreenDevice",
    
    # Event System
    "Filters",
    "BaseFilter",
    "and_filter",
    "or_filter",
    
    # Utilities
    "CpuMonitor",
    "PingMonitor",
    "CallHolder", 
    "PeerResolver",
    
    # Internal Systems
    "ConnectionManager",
    "CacheManager",
    "StreamHandler",
    "CallHandler",
    "RetryManager",
    
    # Advanced features
    "advanced",
    "streaming",
] + __all_advanced__
