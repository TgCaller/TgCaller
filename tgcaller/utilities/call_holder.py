"""
Call Holder - Manage call state and lifecycle
"""

import asyncio
import logging
from typing import Dict, Optional, Set, Any
from enum import Enum
from dataclasses import dataclass, field
import time

from ..types import CallStatus, AudioConfig, VideoConfig

logger = logging.getLogger(__name__)


class CallState(Enum):
    """Call state enumeration"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ACTIVE = "active"
    PAUSED = "paused"
    ENDING = "ending"
    ENDED = "ended"
    ERROR = "error"


@dataclass
class CallSession:
    """Call session data"""
    chat_id: int
    state: CallState = CallState.IDLE
    audio_config: Optional[AudioConfig] = None
    video_config: Optional[VideoConfig] = None
    
    # Timing
    created_at: float = field(default_factory=time.time)
    connected_at: Optional[float] = None
    ended_at: Optional[float] = None
    
    # Stream info
    current_stream: Optional[str] = None
    stream_position: float = 0.0
    volume: float = 1.0
    muted: bool = False
    video_enabled: bool = False
    
    # Participants
    participants: Dict[int, Any] = field(default_factory=dict)
    
    # Statistics
    bytes_sent: int = 0
    bytes_received: int = 0
    frames_sent: int = 0
    frames_received: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get call duration"""
        if self.connected_at:
            end_time = self.ended_at or time.time()
            return end_time - self.connected_at
        return 0.0
    
    @property
    def is_active(self) -> bool:
        """Check if call is active"""
        return self.state in [CallState.CONNECTED, CallState.ACTIVE]
    
    @property
    def has_video(self) -> bool:
        """Check if call has video"""
        return self.video_config is not None and self.video_enabled


class CallHolder:
    """Hold and manage call sessions"""
    
    def __init__(self, max_concurrent_calls: int = 10):
        self.sessions: Dict[int, CallSession] = {}
        self.max_concurrent_calls = max_concurrent_calls
        self.logger = logger
        
        # Call monitoring
        self.monitor_tasks: Dict[int, asyncio.Task] = {}
        self.monitor_interval = 10.0
        
        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
    
    async def create_call(
        self, 
        chat_id: int,
        audio_config: Optional[AudioConfig] = None,
        video_config: Optional[VideoConfig] = None
    ) -> bool:
        """Create new call session"""
        try:
            # Check concurrent call limit
            active_calls = len([s for s in self.sessions.values() if s.is_active])
            if active_calls >= self.max_concurrent_calls:
                self.logger.warning(f"Max concurrent calls limit reached: {self.max_concurrent_calls}")
                return False
            
            # Create session
            session = CallSession(
                chat_id=chat_id,
                state=CallState.INITIALIZING,
                audio_config=audio_config,
                video_config=video_config
            )
            
            self.sessions[chat_id] = session
            self.total_calls += 1
            
            # Start monitoring
            self.monitor_tasks[chat_id] = asyncio.create_task(
                self._monitor_call_session(chat_id)
            )
            
            self.logger.info(f"Created call session for chat {chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create call session for chat {chat_id}: {e}")
            return False
    
    async def connect_call(self, chat_id: int) -> bool:
        """Mark call as connected"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.state = CallState.CONNECTED
        session.connected_at = time.time()
        
        self.logger.info(f"Call connected for chat {chat_id}")
        return True
    
    async def activate_call(self, chat_id: int) -> bool:
        """Mark call as active (streaming)"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        if session.state != CallState.CONNECTED:
            return False
        
        session.state = CallState.ACTIVE
        self.logger.info(f"Call activated for chat {chat_id}")
        return True
    
    async def end_call(self, chat_id: int, success: bool = True) -> bool:
        """End call session"""
        if chat_id not in self.sessions:
            return False
        
        try:
            session = self.sessions[chat_id]
            session.state = CallState.ENDED
            session.ended_at = time.time()
            
            # Update statistics
            if success:
                self.successful_calls += 1
            else:
                self.failed_calls += 1
            
            # Stop monitoring
            if chat_id in self.monitor_tasks:
                self.monitor_tasks[chat_id].cancel()
                del self.monitor_tasks[chat_id]
            
            # Keep session for a while for statistics
            asyncio.create_task(self._cleanup_session_later(chat_id))
            
            self.logger.info(f"Call ended for chat {chat_id}, success: {success}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ending call for chat {chat_id}: {e}")
            return False
    
    async def _cleanup_session_later(self, chat_id: int, delay: float = 300.0):
        """Cleanup session after delay"""
        await asyncio.sleep(delay)
        self.sessions.pop(chat_id, None)
    
    async def _monitor_call_session(self, chat_id: int):
        """Monitor call session health"""
        while chat_id in self.sessions:
            try:
                session = self.sessions[chat_id]
                
                if session.state == CallState.ENDED:
                    break
                
                # Update session statistics
                await self._update_session_stats(chat_id)
                
                # Check for timeouts or issues
                await self._check_session_health(chat_id)
                
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error monitoring call session {chat_id}: {e}")
                await asyncio.sleep(self.monitor_interval)
    
    async def _update_session_stats(self, chat_id: int):
        """Update session statistics"""
        try:
            session = self.sessions[chat_id]
            
            # In real implementation, this would:
            # 1. Query actual network statistics
            # 2. Update bytes sent/received
            # 3. Update frame counts
            # 4. Check connection quality
            
            # Mock update for now
            if session.is_active:
                session.frames_sent += 30  # 30 FPS
                session.bytes_sent += 1024 * 30  # ~30KB per second
                
        except Exception as e:
            self.logger.error(f"Error updating session stats for chat {chat_id}: {e}")
    
    async def _check_session_health(self, chat_id: int):
        """Check session health and handle issues"""
        try:
            session = self.sessions[chat_id]
            
            # Check for long-running calls without activity
            if session.state == CallState.CONNECTED and session.duration > 3600:  # 1 hour
                self.logger.warning(f"Long-running call detected: {chat_id}")
            
            # Check for stuck states
            if session.state == CallState.CONNECTING and session.duration > 30:  # 30 seconds
                self.logger.warning(f"Call stuck in connecting state: {chat_id}")
                session.state = CallState.ERROR
                
        except Exception as e:
            self.logger.error(f"Error checking session health for chat {chat_id}: {e}")
    
    def get_session(self, chat_id: int) -> Optional[CallSession]:
        """Get call session"""
        return self.sessions.get(chat_id)
    
    def get_active_sessions(self) -> Dict[int, CallSession]:
        """Get all active call sessions"""
        return {
            chat_id: session for chat_id, session in self.sessions.items()
            if session.is_active
        }
    
    def get_session_count(self) -> int:
        """Get total number of sessions"""
        return len(self.sessions)
    
    def get_active_count(self) -> int:
        """Get number of active sessions"""
        return len([s for s in self.sessions.values() if s.is_active])
    
    def update_stream_info(
        self, 
        chat_id: int, 
        stream_source: str, 
        position: float = 0.0
    ) -> bool:
        """Update stream information"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.current_stream = stream_source
        session.stream_position = position
        
        return True
    
    def update_volume(self, chat_id: int, volume: float) -> bool:
        """Update call volume"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.volume = max(0.0, min(1.0, volume))
        
        return True
    
    def set_muted(self, chat_id: int, muted: bool) -> bool:
        """Set mute status"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.muted = muted
        
        return True
    
    def set_video_enabled(self, chat_id: int, enabled: bool) -> bool:
        """Set video enabled status"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.video_enabled = enabled
        
        return True
    
    def add_participant(self, chat_id: int, user_id: int, participant_data: Any) -> bool:
        """Add participant to call"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.participants[user_id] = participant_data
        
        return True
    
    def remove_participant(self, chat_id: int, user_id: int) -> bool:
        """Remove participant from call"""
        if chat_id not in self.sessions:
            return False
        
        session = self.sessions[chat_id]
        session.participants.pop(user_id, None)
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get call holder statistics"""
        active_sessions = self.get_active_sessions()
        
        total_duration = sum(session.duration for session in self.sessions.values())
        avg_duration = total_duration / max(self.total_calls, 1)
        
        success_rate = (self.successful_calls / max(self.total_calls, 1)) * 100
        
        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'success_rate': f"{success_rate:.1f}%",
            'active_sessions': len(active_sessions),
            'total_sessions': len(self.sessions),
            'average_duration': f"{avg_duration:.1f}s",
            'max_concurrent': self.max_concurrent_calls
        }
    
    async def cleanup_all(self):
        """Cleanup all call sessions"""
        for task in self.monitor_tasks.values():
            task.cancel()
        
        self.monitor_tasks.clear()
        self.sessions.clear()