"""
TgCaller - Modern Telegram Group Calls Library
Copyright (C) 2024 TgCaller Team

A simple, fast, and reliable library for Telegram voice and video calls
with advanced features like screen sharing, transcription, and more.
"""

__version__ = "1.0.0"
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
)
from .exceptions import (
    TgCallerError,
    ConnectionError,
    MediaError,
    CallError,
    StreamError,
    ConfigurationError,
)

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
    
    # Exceptions
    "TgCallerError",
    "ConnectionError",
    "MediaError",
    "CallError",
    "StreamError",
    "ConfigurationError",
    
    # Advanced features
    "advanced",
] + __all_advanced__