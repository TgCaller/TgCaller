"""
TgCaller - Modern Telegram Group Calls Library
Copyright (C) 2024 TgCaller Team

A simple, fast, and reliable library for Telegram voice and video calls.
"""

__version__ = "1.0.0"
__author__ = "TgCaller Team"
__email__ = "team@tgcaller.dev"
__license__ = "MIT"

from .client import TgCaller
from .types import *
from .exceptions import *

__all__ = [
    "TgCaller",
    # Types
    "AudioConfig",
    "VideoConfig", 
    "MediaStream",
    "CallUpdate",
    # Exceptions
    "TgCallerError",
    "ConnectionError",
    "MediaError",
]