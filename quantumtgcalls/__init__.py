"""
QuantumTgCalls - Next-generation alternative to pytgcalls
Copyright (C) 2025 xAI Quantum Team

This file is part of QuantumTgCalls.
"""

__version__ = "1.0.0-Ω"
__author__ = "xAI Quantum Team"
__email__ = "quantum@xai.dev"
__license__ = "LGPL-3.0"

from .quantum_core import QuantumTgCalls
from .types import *
from .exceptions import *

__all__ = [
    "QuantumTgCalls",
    # Types
    "AudioParameters",
    "VideoParameters", 
    "MediaStream",
    "CallUpdate",
    # Exceptions
    "QuantumError",
    "ConnectionError",
    "MediaError",
]