"""
TgCaller Main Client
"""

import asyncio
import logging
from typing import Optional, Union, Callable, Dict, Any
from pyrogram import Client

from .types import AudioConfig, VideoConfig, MediaStream, CallUpdate, CallStatus
from .exceptions import TgCallerError, ConnectionError, MediaError
from .handlers import EventHandler
from .methods import CallMethods, StreamMethods

logger = logging.getLogger(__name__)


class TgCaller:
    """
    TgCaller main client for Telegram group calls
    """
    
    def __init__(
        self,
        client: Client,
        log_level: int = logging.WARNING
    ):
        """
        Initialize TgCaller
        
        Args:
            client: Pyrogram client instance
            log_level: Logging level
        """
        self._client = client
        self._active_calls: Dict[int, Any] = {}
        self._event_handlers: Dict[str, list] = {}
        
        # Setup logging
        logging.basicConfig(level=log_level)
        self._logger = logger
        
        # Initialize components
        self._event_handler = EventHandler(self)
        
        # Mix in methods
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
        """Start TgCaller"""
        if self._is_connected:
            return
            
        try:
            # Initialize client if not started
            if not self._client.is_connected:
                await self._client.start()
            
            # Setup event handlers
            await self._event_handler.setup()
            
            self._is_connected = True
            self._logger.info("TgCaller started successfully")
            
        except Exception as e:
            raise ConnectionError(f"Failed to start TgCaller: {e}")
    
    async def stop(self):
        """Stop TgCaller"""
        if not self._is_connected:
            return
            
        try:
            # Leave all active calls
            for chat_id in list(self._active_calls.keys()):
                await self.leave_call(chat_id)
            
            # Cleanup
            await self._event_handler.cleanup()
            self._is_connected = False
            
            self._logger.info("TgCaller stopped")
            
        except Exception as e:
            self._logger.error(f"Error stopping TgCaller: {e}")
    
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
    
    def on_error(self, func: Callable = None):
        """Decorator for error events"""
        def decorator(f):
            self._add_handler('error', f)
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
    
    def get_active_calls(self) -> Dict[int, Any]:
        """Get active calls"""
        return self._active_calls.copy()
    
    def is_connected(self, chat_id: Optional[int] = None) -> bool:
        """Check if connected to call"""
        if chat_id is None:
            return self._is_connected
        return chat_id in self._active_calls
    
    @property
    def is_running(self) -> bool:
        """Check if TgCaller is running"""
        return self._is_connected