"""
Cache Management - Handle caching for performance optimization
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() - self.timestamp > self.ttl
    
    def access(self):
        """Mark cache entry as accessed"""
        self.access_count += 1


class CacheManager:
    """Manage caching for TgCaller operations"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 300.0):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.logger = logger
        
        # Cache statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        # Peer and user caches
        self.user_peer_cache: Dict[int, Any] = {}
        self.chat_peer_cache: Dict[int, Any] = {}
        self.participant_cache: Dict[int, Dict[int, Any]] = {}
        
        # Call-specific caches
        self.call_configs: Dict[int, Any] = {}
        self.stream_sources: Dict[int, Dict[str, Any]] = {}
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache"""
        if key not in self.cache:
            self.misses += 1
            return default
        
        entry = self.cache[key]
        
        if entry.is_expired:
            del self.cache[key]
            self.misses += 1
            return default
        
        entry.access()
        self.hits += 1
        return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        # Check if we need to evict entries
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = CacheEntry(
            data=value,
            timestamp=time.time(),
            ttl=ttl
        )
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.user_peer_cache.clear()
        self.chat_peer_cache.clear()
        self.participant_cache.clear()
        self.call_configs.clear()
        self.stream_sources.clear()
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Find entry with lowest access count and oldest timestamp
        lru_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].access_count, self.cache[k].timestamp)
        )
        
        del self.cache[lru_key]
        self.evictions += 1
    
    async def _cleanup_loop(self):
        """Periodic cleanup of expired entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Cleanup every minute
                
                expired_keys = [
                    key for key, entry in self.cache.items()
                    if entry.is_expired
                ]
                
                for key in expired_keys:
                    del self.cache[key]
                
                if expired_keys:
                    self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {e}")
    
    # Peer caching methods
    def cache_user_peer(self, chat_id: int, peer: Any) -> None:
        """Cache user peer for chat"""
        self.user_peer_cache[chat_id] = peer
    
    def get_user_peer(self, chat_id: int) -> Optional[Any]:
        """Get cached user peer"""
        return self.user_peer_cache.get(chat_id)
    
    def cache_chat_peer(self, chat_id: int, peer: Any) -> None:
        """Cache chat peer"""
        self.chat_peer_cache[chat_id] = peer
    
    def get_chat_peer(self, chat_id: int) -> Optional[Any]:
        """Get cached chat peer"""
        return self.chat_peer_cache.get(chat_id)
    
    # Participant caching
    def cache_participants(self, chat_id: int, participants: Dict[int, Any]) -> None:
        """Cache call participants"""
        self.participant_cache[chat_id] = participants
    
    def get_participants(self, chat_id: int) -> Dict[int, Any]:
        """Get cached participants"""
        return self.participant_cache.get(chat_id, {})
    
    def add_participant(self, chat_id: int, user_id: int, participant: Any) -> None:
        """Add participant to cache"""
        if chat_id not in self.participant_cache:
            self.participant_cache[chat_id] = {}
        self.participant_cache[chat_id][user_id] = participant
    
    def remove_participant(self, chat_id: int, user_id: int) -> None:
        """Remove participant from cache"""
        if chat_id in self.participant_cache:
            self.participant_cache[chat_id].pop(user_id, None)
    
    # Call configuration caching
    def cache_call_config(self, chat_id: int, config: Any) -> None:
        """Cache call configuration"""
        self.call_configs[chat_id] = config
    
    def get_call_config(self, chat_id: int) -> Optional[Any]:
        """Get cached call configuration"""
        return self.call_configs.get(chat_id)
    
    # Stream source caching
    def cache_stream_sources(self, chat_id: int, sources: Dict[str, Any]) -> None:
        """Cache stream sources"""
        self.stream_sources[chat_id] = sources
    
    def get_stream_sources(self, chat_id: int) -> Dict[str, Any]:
        """Get cached stream sources"""
        return self.stream_sources.get(chat_id, {})
    
    def clear_chat_cache(self, chat_id: int) -> None:
        """Clear all cache entries for specific chat"""
        # Remove from all chat-specific caches
        self.user_peer_cache.pop(chat_id, None)
        self.chat_peer_cache.pop(chat_id, None)
        self.participant_cache.pop(chat_id, None)
        self.call_configs.pop(chat_id, None)
        self.stream_sources.pop(chat_id, None)
        
        # Remove from general cache (chat-specific keys)
        chat_keys = [key for key in self.cache.keys() if str(chat_id) in key]
        for key in chat_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'evictions': self.evictions,
            'user_peers': len(self.user_peer_cache),
            'chat_peers': len(self.chat_peer_cache),
            'participants': sum(len(p) for p in self.participant_cache.values()),
            'call_configs': len(self.call_configs),
            'stream_sources': len(self.stream_sources)
        }
    
    async def cleanup(self):
        """Cleanup cache manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        self.clear()