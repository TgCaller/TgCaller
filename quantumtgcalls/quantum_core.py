"""
QuantumTgCalls Core Implementation
Following pytgcalls architecture patterns
"""

import asyncio
import logging
from typing import Optional, Union, Callable, Dict, Any
from pyrogram import Client
from pyrogram.types import Message

from .types import AudioParameters, VideoParameters, MediaStream, CallUpdate
from .exceptions import QuantumError, ConnectionError, MediaError
from .handlers import EventHandler
from .media_devices import MediaDeviceManager
from .methods import CallMethods, StreamMethods

logger = logging.getLogger(__name__)


class QuantumTgCalls:
    """
    QuantumTgCalls main class - following pytgcalls patterns
    """
    
    def __init__(
        self,
        client: Client,
        log_mode: int = logging.WARNING,
        cache_duration: int = 120
    ):
        """
        Initialize QuantumTgCalls
        
        Args:
            client: Pyrogram client instance
            log_mode: Logging level
            cache_duration: Cache duration in seconds
        """
        self._client = client
        self._cache_duration = cache_duration
        self._active_calls: Dict[int, Any] = {}
        self._event_handlers: Dict[str, list] = {}
        
        # Setup logging
        logging.basicConfig(level=log_mode)
        self._logger = logger
        
        # Initialize components
        self._event_handler = EventHandler(self)
        self._media_manager = MediaDeviceManager()
        
        # Mix in methods (following pytgcalls pattern)
        self._setup_methods()
        
        # Connection state
        self._is_connected = False
        
    def _setup_methods(self):
        """Setup method mixins"""
        # Add call methods
        for method_name in dir(CallMethods):
            if not method_name.startswith('_'):
                method = getattr(CallMethods, method_name)
                if callable(method):
                    setattr(self, method_name, method.__get__(self, self.__class__))
        
        # Add stream methods  
        for method_name in dir(StreamMethods):
            if not method_name.startswith('_'):
                method = getattr(StreamMethods, method_name)
                if callable(method):
                    setattr(self, method_name, method.__get__(self, self.__class__))
    
    async def start(self):
        """Start QuantumTgCalls"""
        if self._is_connected:
            return
            
        try:
            # Initialize client if not started
            if not self._client.is_connected:
                await self._client.start()
            
            # Setup event handlers
            await self._event_handler.setup()
            
            self._is_connected = True
            self._logger.info("QuantumTgCalls started successfully")
            
        except Exception as e:
            raise ConnectionError(f"Failed to start QuantumTgCalls: {e}")
    
    async def stop(self):
        """Stop QuantumTgCalls"""
        if not self._is_connected:
            return
            
        try:
            # Leave all active calls
            for chat_id in list(self._active_calls.keys()):
                await self.leave_call(chat_id)
            
            # Cleanup
            await self._event_handler.cleanup()
            self._is_connected = False
            
            self._logger.info("QuantumTgCalls stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping QuantumTgCalls: {e}")
    
    def on_stream_end(self, func: Callable = None):
        """Decorator for stream end events"""
        def decorator(f):
            self._add_handler('stream_end', f)
            return f
        return decorator(func) if func else decorator
    
    def on_kicked(self, func: Callable = None):
        """Decorator for kicked events"""
        def decorator(f):
            self._add_handler('kicked', f)
            return f
        return decorator(func) if func else decorator
    
    def on_left(self, func: Callable = None):
        """Decorator for left events"""
        def decorator(f):
            self._add_handler('left', f)
            return f
        return decorator(func) if func else decorator
    
    def _add_handler(self, event_type: str, handler: Callable):
        """Add event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def _emit_event(self, event_type: str, *args, **kwargs):
        """Emit event to handlers"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self, *args, **kwargs)
                    else:
                        handler(self, *args, **kwargs)
                except Exception as e:
                    self._logger.error(f"Error in event handler {handler.__name__}: {e}")
    
    @property
    def client(self) -> Client:
        """Get Pyrogram client"""
        return self._client
    
    @property
    def active_calls(self) -> Dict[int, Any]:
        """Get active calls"""
        return self._active_calls.copy()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._is_connected