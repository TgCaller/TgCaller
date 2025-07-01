"""
Plugin Manager
"""

import logging
from typing import Dict, List, Any, Optional
from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """Manage TgCaller plugins"""
    
    def __init__(self, caller):
        """
        Initialize plugin manager
        
        Args:
            caller: TgCaller instance
        """
        self.caller = caller
        self.plugins: Dict[str, BasePlugin] = {}
        self.logger = logger
    
    async def register_plugin(self, plugin: BasePlugin):
        """Register a plugin"""
        if not isinstance(plugin, BasePlugin):
            raise TypeError("Plugin must inherit from BasePlugin")
        
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin {plugin.name} already registered")
        
        # Check dependencies
        for dep in plugin.dependencies:
            if dep not in self.plugins:
                raise ValueError(f"Plugin dependency {dep} not found")
        
        # Set caller reference
        plugin.set_caller(self.caller)
        
        # Load plugin
        await plugin.on_load()
        
        # Register plugin
        self.plugins[plugin.name] = plugin
        
        self.logger.info(f"Registered plugin: {plugin.name}")
    
    async def unregister_plugin(self, plugin_name: str):
        """Unregister a plugin"""
        if plugin_name not in self.plugins:
            return False
        
        plugin = self.plugins[plugin_name]
        
        # Check if other plugins depend on this one
        for other_plugin in self.plugins.values():
            if plugin_name in other_plugin.dependencies:
                raise ValueError(
                    f"Cannot unregister {plugin_name}: "
                    f"required by {other_plugin.name}"
                )
        
        # Unload plugin
        await plugin.on_unload()
        
        # Remove plugin
        del self.plugins[plugin_name]
        
        self.logger.info(f"Unregistered plugin: {plugin_name}")
        return True
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get plugin by name"""
        return self.plugins.get(plugin_name)
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if plugin is loaded"""
        return plugin_name in self.plugins
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugin names"""
        return list(self.plugins.keys())
    
    async def process_audio(self, audio_frame):
        """Process audio through all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    audio_frame = await plugin.process_audio(audio_frame)
                except Exception as e:
                    self.logger.error(f"Error in plugin {plugin.name}: {e}")
        
        return audio_frame
    
    async def process_video(self, video_frame):
        """Process video through all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    video_frame = await plugin.process_video(video_frame)
                except Exception as e:
                    self.logger.error(f"Error in plugin {plugin.name}: {e}")
        
        return video_frame
    
    async def emit_event(self, event_name: str, *args, **kwargs):
        """Emit event to all plugins"""
        for plugin in self.plugins.values():
            if plugin.is_enabled():
                try:
                    handler = getattr(plugin, event_name, None)
                    if handler and callable(handler):
                        await handler(*args, **kwargs)
                except Exception as e:
                    self.logger.error(
                        f"Error in plugin {plugin.name} "
                        f"handling event {event_name}: {e}"
                    )
    
    async def send_plugin_message(
        self, 
        target_plugin: str, 
        message: Any, 
        sender: str = None
    ):
        """Send message to specific plugin"""
        if target_plugin not in self.plugins:
            return False
        
        plugin = self.plugins[target_plugin]
        if plugin.is_enabled():
            try:
                await plugin.on_plugin_message(sender, message)
                return True
            except Exception as e:
                self.logger.error(
                    f"Error sending message to plugin {target_plugin}: {e}"
                )
        
        return False
    
    async def cleanup(self):
        """Cleanup all plugins"""
        for plugin_name in list(self.plugins.keys()):
            await self.unregister_plugin(plugin_name)