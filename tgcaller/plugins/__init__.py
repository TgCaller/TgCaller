"""
TgCaller Plugin System
"""

from .base_plugin import BasePlugin
from .plugin_manager import PluginManager

__all__ = [
    "BasePlugin",
    "PluginManager",
]