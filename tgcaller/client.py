"""
TgCaller Main Client
"""

import asyncio
import logging
from typing import Optional, Union, Callable, Dict, Any, List
from pathlib import Path
from pyrogram import Client

from .types import AudioConfig, VideoConfig, MediaStream, CallUpdate, CallStatus
from .exceptions import TgCallerError, ConnectionError, MediaError, StreamError
from .handlers import EventHandler
from .handlers.event_system import EventHandlerSystem, Filters, BaseFilter
from .methods import CallMethods, StreamMethods
from .api import CustomAPIServer, on_custom_update
from .devices import MediaDevices
from .internal import ConnectionManager, CacheManager, StreamHandler, CallHandler, RetryManager
from .mtproto import Connection

logger = logging.getLogger(__name__)


class TgCaller:
    """
    TgCaller main client for Telegram group calls
    
    Example:
        ```python
        from pyrogram import Client
        from tgcaller import TgCaller
        
        app = Client("my_session")
        caller = TgCaller(app)
        
        @caller.on_stream_end
        async def on_stream_end(client, update):
            print(f"Stream ended in {update.chat_id}")
        
        async def main():
            await caller.start()
            await caller.join_call(-1001234567890)
            await caller.play(-1001234567890, "song.mp3")
        ```
    """
    
    def __init__(
        self,
        client: Client,
        log_level: int = logging.WARNING,
        connection_backend: Optional[Any] = None,
    ):
        """
        Initialize TgCaller
        
        Args:
            client: Pyrogram client instance
            log_level: Logging level (default: WARNING)
        """
        if not isinstance(client, Client):
            raise TypeError("client must be a Pyrogram Client instance")
            
        self._client = client
        # TgCaller uses its own Telegram signaling adapter and audio media engine
        # by default. Custom transports remain injectable for applications/tests.
        if connection_backend is None:
            from .mtproto import (
                AiortcTelegramMediaEngine,
                PyrogramGroupCallBackend,
                resolve_active_group_call,
            )

            media_engine = AiortcTelegramMediaEngine()
            connection_backend = PyrogramGroupCallBackend(
                client=client,
                resolve_call=lambda chat_id: resolve_active_group_call(client, chat_id),
                media_engine=media_engine,
            )
            self._owns_connection_backend = True
        else:
            self._owns_connection_backend = False
        self._connection = Connection(client, backend=connection_backend)
        self._active_calls: Dict[int, Any] = {}
        self._event_handlers: Dict[str, List[Callable]] = {
            'stream_end': [],
            'stream_start': [],
            'stream_paused': [],
            'stream_resumed': [],
            'stream_stopped': [],
            'call_joined': [],
            'call_left': [],
            'kicked': [],
            'error': [],
        }
        
        # Setup logging
        logging.basicConfig(level=log_level)
        self._logger = logger
        
        # Initialize components
        self._event_handler = EventHandler(self)
        
        # Initialize new systems
        self._event_system = EventHandlerSystem()
        self._custom_api_server: Optional[CustomAPIServer] = None
        
        # Initialize internal managers
        self._connection_manager = ConnectionManager(self)
        self._cache_manager = CacheManager()
        self._stream_handler = StreamHandler(self)
        self._call_handler = CallHandler(self)
        self._retry_manager = RetryManager()
        
        # Mix in methods
        self._setup_methods()
        
        # Connection state
        self._is_connected = False
        
    def _setup_methods(self):
        """Setup method mixins"""
        # Add call methods
        for method_name in dir(CallMethods):
            if not method_name.startswith('_') and callable(getattr(CallMethods, method_name)):
                method = getattr(CallMethods, method_name)
                setattr(self, method_name, method.__get__(self, self.__class__))
        
        # Add stream methods with explicit mapping to avoid conflicts
        for method_name in dir(StreamMethods):
            if not method_name.startswith('_') and callable(getattr(StreamMethods, method_name)):
                method = getattr(StreamMethods, method_name)
                # Map stop_stream to stop for backward compatibility
                if method_name == 'stop_stream':
                    setattr(self, 'stop_stream', method.__get__(self, self.__class__))
                else:
                    setattr(self, method_name, method.__get__(self, self.__class__))
    
    async def start(self) -> None:
        """
        Start TgCaller service
        
        Raises:
            ConnectionError: If failed to start
        """
        if self._is_connected:
            self._logger.warning("TgCaller is already running")
            return
            
        try:
            # Initialize client if not started
            if not self._client.is_connected:
                await self._client.start()
            
            # Start background maintenance tasks after an event loop is available
            await self._cache_manager.start()

            # Setup event handlers
            await self._event_handler.setup()
            
            self._is_connected = True
            self._logger.info("TgCaller started successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to start TgCaller: {e}")
            raise ConnectionError(f"Failed to start TgCaller: {e}")
    
    async def stop(self) -> None:
        """Stop TgCaller and attempt every cleanup step, even if one fails."""
        if not self._is_connected:
            self._logger.warning("TgCaller is not running")
            return

        errors = []
        try:
            # Try to leave every active call; leave_call handles per-call errors.
            for chat_id in list(self._active_calls.keys()):
                try:
                    if not await self.leave_call(chat_id):
                        errors.append(f"could not cleanly leave call {chat_id}")
                except Exception as exc:
                    errors.append(f"leave call {chat_id}: {exc}")

            # A failure in one manager must not prevent the others from stopping.
            cleanup_steps = (
                ("connection manager", self._connection_manager.cleanup_all),
                ("cache manager", self._cache_manager.cleanup),
                ("stream handler", self._stream_handler.cleanup_all),
                ("call handler", self._call_handler.cleanup_all),
                ("event handler", self._event_handler.cleanup),
            )
            for name, cleanup in cleanup_steps:
                try:
                    await cleanup()
                except Exception as exc:
                    errors.append(f"{name}: {exc}")
        finally:
            # The service must not remain marked as running after shutdown starts.
            self._is_connected = False

        if errors:
            self._logger.error("TgCaller stopped with cleanup errors: %s", "; ".join(errors))
        else:
            self._logger.info("TgCaller stopped successfully")
    
    def on_stream_end(self, func: Callable = None):
        """
        Decorator for stream end events
        
        Args:
            func: Event handler function
            
        Example:
            ```python
            @caller.on_stream_end
            async def on_stream_end(client, update):
                print(f"Stream ended in {update.chat_id}")
            ```
        """
        def decorator(f):
            self._add_handler('stream_end', f)
            return f
        return decorator(func) if func else decorator
    
    def on_stream_start(self, func: Callable = None):
        """Decorator for stream start events"""
        def decorator(f):
            self._add_handler('stream_start', f)
            return f
        return decorator(func) if func else decorator
    
    def on_stream_stopped(self, func: Callable = None):
        """Decorator for stream stopped events"""
        def decorator(f):
            self._add_handler('stream_stopped', f)
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
            self._add_handler('call_left', f)
            return f
        return decorator(func) if func else decorator
    
    def on_error(self, func: Callable = None):
        """Decorator for error events"""
        def decorator(f):
            self._add_handler('error', f)
            return f
        return decorator(func) if func else decorator
    
    def on_custom_update(self, func: Callable = None):
        """
        Decorator for custom API update handler
        
        Only one handler can be registered at a time.
        
        Example:
            ```python
            @caller.on_custom_update
            async def handle_custom_request(client, data):
                return {"message": "Request processed"}
            ```
        """
        def decorator(f):
            if self._custom_api_server:
                self._custom_api_server.set_custom_handler(f)
            f._is_custom_update_handler = True
            return f
        return decorator(func) if func else decorator
    
    def _add_handler(self, event_type: str, handler: Callable) -> None:
        """Add event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def add_handler(
        self,
        func: Callable,
        filters: Optional[BaseFilter] = None,
        priority: int = 0
    ):
        """
        Add event handler with optional filters
        
        Args:
            func: Handler function
            filters: Optional filter to apply
            priority: Handler priority (higher = called first)
        """
        self._event_system.add_handler(func, filters, priority)
    
    def remove_handler(self, func: Callable) -> bool:
        """
        Remove event handler
        
        Args:
            func: Handler function to remove
            
        Returns:
            True if handler was removed
        """
        return self._event_system.remove_handler(func)
    
    async def _emit_event(self, event_type: str, *args, **kwargs) -> None:
        """Emit event to handlers"""
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(self._client, *args, **kwargs)
                    else:
                        handler(self._client, *args, **kwargs)
                except Exception as e:
                    self._logger.error(f"Error in event handler {handler.__name__}: {e}")
                    await self._emit_event('error', e)
        
        # Also propagate through new event system
        if args:
            await self._event_system._propagate(args[0], self._client)
    
    def enable_custom_api(
        self, 
        host: str = "localhost", 
        port: int = 8080
    ) -> CustomAPIServer:
        """
        Enable custom HTTP API server
        
        Args:
            host: Server host
            port: Server port
            
        Returns:
            CustomAPIServer instance
        """
        if self._custom_api_server:
            raise ValueError("Custom API server already enabled")
        
        self._custom_api_server = CustomAPIServer(self, host, port)
        
        # Set handler if already registered
        for handler_list in self._event_handlers.values():
            for handler in handler_list:
                if hasattr(handler, '_is_custom_update_handler'):
                    self._custom_api_server.set_custom_handler(handler)
                    break
        
        return self._custom_api_server
    
    async def start_custom_api(self):
        """Start custom API server"""
        if not self._custom_api_server:
            raise ValueError("Custom API server not enabled. Call enable_custom_api() first")
        
        await self._custom_api_server.start()
    
    async def stop_custom_api(self):
        """Stop custom API server"""
        if self._custom_api_server:
            await self._custom_api_server.stop()
    
    async def _validate_media(self, stream: MediaStream):
        """Validate media stream"""
        if stream.is_file:
            if not Path(stream.source).exists():
                raise MediaError(f"File not found: {stream.source}")
        elif not stream.is_url:
            raise MediaError(f"Invalid media source: {stream.source}")
    
    @property
    def client(self) -> Client:
        """Get Pyrogram client instance"""
        return self._client
    
    def get_active_calls(self) -> List[int]:
        """
        Get list of active call chat IDs
        
        Returns:
            List of chat IDs with active calls
        """
        return list(self._active_calls.keys())
    
    def is_connected(self, chat_id: Optional[int] = None) -> bool:
        """
        Check connection status
        
        Args:
            chat_id: Specific chat ID to check (optional)
            
        Returns:
            True if connected
        """
        if chat_id is None:
            return self._is_connected
        return chat_id in self._active_calls
    
    @property
    def is_running(self) -> bool:
        """Check if TgCaller service is running"""
        return self._is_connected
    
    @property
    def media_devices(self) -> MediaDevices:
        """Get media devices interface"""
        return MediaDevices
    
    @property
    def filters(self) -> Filters:
        """Get filters interface"""
        return Filters
    
    @property
    def connection_manager(self) -> ConnectionManager:
        """Get connection manager"""
        return self._connection_manager
    
    @property
    def cache_manager(self) -> CacheManager:
        """Get cache manager"""
        return self._cache_manager
    
    @property
    def stream_handler(self) -> StreamHandler:
        """Get stream handler"""
        return self._stream_handler
    
    @property
    def call_handler(self) -> CallHandler:
        """Get call handler"""
        return self._call_handler
    
    @property
    def retry_manager(self) -> RetryManager:
        """Get retry manager"""
        return self._retry_manager