"""
Peer Resolver - Resolve and cache Telegram peers
"""

import asyncio
import logging
from typing import Dict, Optional, Union, Any
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class PeerInfo:
    """Peer information"""
    peer_id: int
    access_hash: Optional[int]
    peer_type: str  # "user", "chat", "channel"
    title: Optional[str] = None
    username: Optional[str] = None
    cached_at: float = None
    
    def __post_init__(self):
        if self.cached_at is None:
            self.cached_at = time.time()
    
    @property
    def is_expired(self) -> bool:
        """Check if peer info is expired (24 hours)"""
        return time.time() - self.cached_at > 86400


class PeerResolver:
    """Resolve and cache Telegram peer information"""
    
    def __init__(self, client):
        self.client = client
        self.peer_cache: Dict[int, PeerInfo] = {}
        self.username_cache: Dict[str, int] = {}
        self.logger = logger
        
        # Resolution statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.resolution_errors = 0
    
    async def resolve_peer(self, peer: Union[int, str]) -> Optional[PeerInfo]:
        """
        Resolve peer information
        
        Args:
            peer: User ID, chat ID, or username
            
        Returns:
            PeerInfo object or None if resolution failed
        """
        try:
            # Handle different peer types
            if isinstance(peer, str):
                if peer.startswith('@'):
                    peer = peer[1:]  # Remove @ prefix
                
                # Check username cache first
                if peer in self.username_cache:
                    peer_id = self.username_cache[peer]
                    cached_info = self.peer_cache.get(peer_id)
                    
                    if cached_info and not cached_info.is_expired:
                        self.cache_hits += 1
                        return cached_info
                
                # Resolve username
                peer_info = await self._resolve_username(peer)
                
            elif isinstance(peer, int):
                # Check cache first
                cached_info = self.peer_cache.get(peer)
                if cached_info and not cached_info.is_expired:
                    self.cache_hits += 1
                    return cached_info
                
                # Resolve peer ID
                peer_info = await self._resolve_peer_id(peer)
            
            else:
                raise ValueError(f"Invalid peer type: {type(peer)}")
            
            # Cache the result
            if peer_info:
                self.peer_cache[peer_info.peer_id] = peer_info
                if peer_info.username:
                    self.username_cache[peer_info.username] = peer_info.peer_id
                
                self.cache_misses += 1
                return peer_info
            
            self.resolution_errors += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Error resolving peer {peer}: {e}")
            self.resolution_errors += 1
            return None
    
    async def _resolve_username(self, username: str) -> Optional[PeerInfo]:
        """Resolve username to peer info"""
        try:
            # Use Pyrogram's resolve_peer method
            peer = await self.client.resolve_peer(username)
            
            # Get additional info
            if hasattr(peer, 'user_id'):
                # User
                user = await self.client.get_users(peer.user_id)
                return PeerInfo(
                    peer_id=peer.user_id,
                    access_hash=peer.access_hash,
                    peer_type="user",
                    title=f"{user.first_name} {user.last_name or ''}".strip(),
                    username=user.username
                )
            elif hasattr(peer, 'channel_id'):
                # Channel/Supergroup
                chat = await self.client.get_chat(peer.channel_id)
                return PeerInfo(
                    peer_id=peer.channel_id,
                    access_hash=peer.access_hash,
                    peer_type="channel",
                    title=chat.title,
                    username=chat.username
                )
            elif hasattr(peer, 'chat_id'):
                # Group
                chat = await self.client.get_chat(peer.chat_id)
                return PeerInfo(
                    peer_id=peer.chat_id,
                    access_hash=None,
                    peer_type="chat",
                    title=chat.title
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error resolving username {username}: {e}")
            return None
    
    async def _resolve_peer_id(self, peer_id: int) -> Optional[PeerInfo]:
        """Resolve peer ID to peer info"""
        try:
            # Determine peer type based on ID
            if peer_id > 0:
                # User
                user = await self.client.get_users(peer_id)
                return PeerInfo(
                    peer_id=peer_id,
                    access_hash=getattr(user, 'access_hash', None),
                    peer_type="user",
                    title=f"{user.first_name} {user.last_name or ''}".strip(),
                    username=user.username
                )
            else:
                # Chat or Channel
                chat = await self.client.get_chat(peer_id)
                
                peer_type = "channel" if chat.type in ["supergroup", "channel"] else "chat"
                
                return PeerInfo(
                    peer_id=peer_id,
                    access_hash=getattr(chat, 'access_hash', None),
                    peer_type=peer_type,
                    title=chat.title,
                    username=getattr(chat, 'username', None)
                )
                
        except Exception as e:
            self.logger.error(f"Error resolving peer ID {peer_id}: {e}")
            return None
    
    async def get_chat_id(self, peer: Union[int, str]) -> Optional[int]:
        """Get chat ID from peer"""
        peer_info = await self.resolve_peer(peer)
        return peer_info.peer_id if peer_info else None
    
    async def get_access_hash(self, peer: Union[int, str]) -> Optional[int]:
        """Get access hash from peer"""
        peer_info = await self.resolve_peer(peer)
        return peer_info.access_hash if peer_info else None
    
    def cache_peer_info(self, peer_info: PeerInfo):
        """Manually cache peer info"""
        self.peer_cache[peer_info.peer_id] = peer_info
        if peer_info.username:
            self.username_cache[peer_info.username] = peer_info.peer_id
    
    def get_cached_peer(self, peer_id: int) -> Optional[PeerInfo]:
        """Get cached peer info"""
        cached_info = self.peer_cache.get(peer_id)
        if cached_info and not cached_info.is_expired:
            return cached_info
        return None
    
    def clear_cache(self):
        """Clear all cached peer information"""
        self.peer_cache.clear()
        self.username_cache.clear()
        self.logger.info("Peer cache cleared")
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        expired_peers = [
            peer_id for peer_id, info in self.peer_cache.items()
            if info.is_expired
        ]
        
        for peer_id in expired_peers:
            peer_info = self.peer_cache.pop(peer_id)
            if peer_info.username and peer_info.username in self.username_cache:
                del self.username_cache[peer_info.username]
        
        if expired_peers:
            self.logger.info(f"Cleared {len(expired_peers)} expired peer cache entries")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.peer_cache),
            'username_cache_size': len(self.username_cache),
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'resolution_errors': self.resolution_errors
        }
    
    async def preload_peers(self, peer_list: list):
        """Preload multiple peers into cache"""
        tasks = [self.resolve_peer(peer) for peer in peer_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if not isinstance(r, Exception) and r is not None)
        self.logger.info(f"Preloaded {successful}/{len(peer_list)} peers into cache")