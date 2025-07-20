"""
Group Call Participant Types
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ParticipantAction(Enum):
    """Participant action types"""
    JOINED = "joined"
    LEFT = "left"
    UPDATED = "updated"
    KICKED = "kicked"
    MUTED = "muted"
    UNMUTED = "unmuted"


@dataclass
class VideoInfo:
    """Video stream information"""
    endpoint: str
    """Video endpoint identifier"""
    
    sources: list
    """Video source configurations"""
    
    width: int = 640
    """Video width"""
    
    height: int = 480
    """Video height"""
    
    fps: int = 30
    """Frame rate"""


@dataclass
class GroupCallParticipant:
    """Group call participant information"""
    
    user_id: int
    """User ID of participant"""
    
    muted: bool = False
    """Whether participant is muted"""
    
    muted_by_admin: bool = False
    """Whether participant is muted by admin"""
    
    video_camera: bool = False
    """Whether participant has camera enabled"""
    
    screen_sharing: bool = False
    """Whether participant is screen sharing"""
    
    video_info: Optional[VideoInfo] = None
    """Video stream information"""
    
    presentation_info: Optional[VideoInfo] = None
    """Screen sharing stream information"""
    
    joined_at: Optional[float] = None
    """Timestamp when participant joined"""
    
    metadata: Optional[Dict[str, Any]] = None
    """Additional participant metadata"""
    
    def __post_init__(self):
        """Initialize metadata if None"""
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def has_video(self) -> bool:
        """Check if participant has any video stream"""
        return self.video_camera or self.screen_sharing
    
    @property
    def is_speaking(self) -> bool:
        """Check if participant is currently speaking"""
        return not self.muted and self.metadata.get('speaking', False)


@dataclass
class UpdatedGroupCallParticipant:
    """Updated group call participant event"""
    
    participant: GroupCallParticipant
    """Updated participant information"""
    
    action: ParticipantAction
    """Action that triggered the update"""
    
    chat_id: int
    """Chat ID where update occurred"""
    
    timestamp: Optional[float] = None
    """Update timestamp"""
    
    @property
    def user_id(self) -> int:
        """Get participant user ID"""
        return self.participant.user_id