"""
Call Update Types
"""

from typing import Optional, Any, Dict
from dataclasses import dataclass
from enum import Enum


class CallStatus(Enum):
    """Call status enumeration"""
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    PLAYING = "playing"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class CallUpdate:
    """Call update information"""
    
    chat_id: int
    """Chat ID where the call is happening"""
    
    status: CallStatus
    """Current call status"""
    
    user_id: Optional[int] = None
    """User ID (for user-specific updates)"""
    
    message: Optional[str] = None
    """Update message"""
    
    error: Optional[Exception] = None
    """Error information if status is ERROR"""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional metadata"""
    
    def __post_init__(self):
        """Initialize metadata if None"""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_error(self) -> bool:
        """Check if update represents an error"""
        return self.status == CallStatus.ERROR or self.error is not None
    
    @property
    def is_active(self) -> bool:
        """Check if call is active"""
        return self.status in [CallStatus.CONNECTED, CallStatus.PLAYING]