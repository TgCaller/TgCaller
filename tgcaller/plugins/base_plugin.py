"""
Base Plugin Class
"""

import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """Base class for all TgCaller plugins"""
    
    name: str = "base_plugin"
    version: str = "1.0.0"
    description: str = "Base plugin"
    dependencies: list = []
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin
        
        Args:
            config: Plugin configuration
        """
        self.config = config or {}
        self.enabled = True
        self.caller = None
        self.logger = logging.getLogger(f"tgcaller.plugins.{self.name}")
        self.storage = {}
    
    async def on_load(self):
        """Called when plugin is loaded"""
        self.logger.info(f"Loading plugin: {self.name}")
    
    async def on_unload(self):
        """Called when plugin is unloaded"""
        self.logger.info(f"Unloading plugin: {self.name}")
    
    async def process_audio(self, audio_frame):
        """Process audio frame"""
        return audio_frame
    
    async def process_video(self, video_frame):
        """Process video frame"""
        return video_frame
    
    async def on_stream_start(self, chat_id: int, source: str):
        """Called when stream starts"""
        pass
    
    async def on_stream_end(self, chat_id: int):
        """Called when stream ends"""
        pass
    
    async def on_user_joined(self, chat_id: int, user_id: int):
        """Called when user joins call"""
        pass
    
    async def on_user_left(self, chat_id: int, user_id: int):
        """Called when user leaves call"""
        pass
    
    async def on_call_start(self, chat_id: int):
        """Called when call starts"""
        pass
    
    async def on_call_end(self, chat_id: int):
        """Called when call ends"""
        pass
    
    async def on_plugin_message(self, sender: str, message: Any):
        """Called when receiving message from another plugin"""
        pass
    
    def set_caller(self, caller):
        """Set TgCaller instance"""
        self.caller = caller
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.enabled
    
    def enable(self):
        """Enable plugin"""
        self.enabled = True
    
    def disable(self):
        """Disable plugin"""
        self.enabled = False