"""
Bridged Calls - Connect multiple chats
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set
from ..types import AudioConfig, VideoConfig, CallUpdate, CallStatus

logger = logging.getLogger(__name__)


class BridgedCallManager:
    """Manage bridged calls between multiple chats"""
    
    def __init__(self, caller):
        self.caller = caller
        self.bridges: Dict[str, Set[int]] = {}
        self.active_bridges: Dict[str, bool] = {}
        self.logger = logger
    
    async def create_bridge(
        self, 
        bridge_name: str, 
        chat_ids: List[int],
        audio_config: Optional[AudioConfig] = None
    ) -> bool:
        """
        Create a bridge between multiple chats
        
        Args:
            bridge_name: Unique bridge identifier
            chat_ids: List of chat IDs to bridge
            audio_config: Audio configuration for bridge
            
        Returns:
            True if bridge created successfully
        """
        if bridge_name in self.bridges:
            raise ValueError(f"Bridge {bridge_name} already exists")
        
        if len(chat_ids) < 2:
            raise ValueError("At least 2 chats required for bridge")
        
        try:
            # Join all chats
            for chat_id in chat_ids:
                if not self.caller.is_connected(chat_id):
                    await self.caller.join_call(chat_id, audio_config=audio_config)
            
            # Create bridge
            self.bridges[bridge_name] = set(chat_ids)
            self.active_bridges[bridge_name] = True
            
            # Start audio bridging
            asyncio.create_task(self._bridge_audio(bridge_name))
            
            self.logger.info(f"Created bridge {bridge_name} with {len(chat_ids)} chats")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create bridge {bridge_name}: {e}")
            return False
    
    async def destroy_bridge(self, bridge_name: str) -> bool:
        """Destroy a bridge"""
        if bridge_name not in self.bridges:
            return False
        
        try:
            # Stop bridging
            self.active_bridges[bridge_name] = False
            
            # Leave calls (optional)
            chat_ids = self.bridges[bridge_name]
            for chat_id in chat_ids:
                await self.caller.leave_call(chat_id)
            
            # Remove bridge
            del self.bridges[bridge_name]
            del self.active_bridges[bridge_name]
            
            self.logger.info(f"Destroyed bridge {bridge_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to destroy bridge {bridge_name}: {e}")
            return False
    
    async def add_chat_to_bridge(self, bridge_name: str, chat_id: int) -> bool:
        """Add chat to existing bridge"""
        if bridge_name not in self.bridges:
            return False
        
        try:
            if not self.caller.is_connected(chat_id):
                await self.caller.join_call(chat_id)
            
            self.bridges[bridge_name].add(chat_id)
            self.logger.info(f"Added chat {chat_id} to bridge {bridge_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add chat to bridge: {e}")
            return False
    
    async def remove_chat_from_bridge(self, bridge_name: str, chat_id: int) -> bool:
        """Remove chat from bridge"""
        if bridge_name not in self.bridges:
            return False
        
        try:
            self.bridges[bridge_name].discard(chat_id)
            await self.caller.leave_call(chat_id)
            
            self.logger.info(f"Removed chat {chat_id} from bridge {bridge_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove chat from bridge: {e}")
            return False
    
    async def _bridge_audio(self, bridge_name: str):
        """Bridge audio between chats"""
        while self.active_bridges.get(bridge_name, False):
            try:
                chat_ids = list(self.bridges[bridge_name])
                
                # Simulate audio bridging
                for i, source_chat in enumerate(chat_ids):
                    for j, target_chat in enumerate(chat_ids):
                        if i != j:
                            # Forward audio from source to target
                            await self._forward_audio(source_chat, target_chat)
                
                await asyncio.sleep(0.02)  # 50 FPS
                
            except Exception as e:
                self.logger.error(f"Error in audio bridging: {e}")
                await asyncio.sleep(1)
    
    async def _forward_audio(self, source_chat: int, target_chat: int):
        """Forward audio from source to target chat"""
        # This would capture audio from source_chat and send to target_chat
        # Implementation depends on actual audio processing
        pass
    
    def get_bridge_info(self, bridge_name: str) -> Optional[Dict]:
        """Get bridge information"""
        if bridge_name not in self.bridges:
            return None
        
        return {
            'name': bridge_name,
            'chat_ids': list(self.bridges[bridge_name]),
            'active': self.active_bridges[bridge_name],
            'chat_count': len(self.bridges[bridge_name])
        }
    
    def list_bridges(self) -> List[str]:
        """List all bridge names"""
        return list(self.bridges.keys())