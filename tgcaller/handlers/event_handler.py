"""
Event Handler
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TgCaller

logger = logging.getLogger(__name__)


class EventHandler:
    """Handle Telegram events and call updates"""
    
    def __init__(self, caller: 'TgCaller'):
        self.caller = caller
        self._client = caller.client
        self._logger = logger
    
    async def setup(self):
        """Setup event handlers"""
        try:
            self._logger.info("Event handlers setup complete")
            
        except Exception as e:
            self._logger.error(f"Failed to setup event handlers: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup event handlers"""
        try:
            self._logger.info("Event handlers cleaned up")
            
        except Exception as e:
            self._logger.error(f"Error cleaning up handlers: {e}")