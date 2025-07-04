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
from .methods import CallMethods, StreamMethods

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
        log_level: int = logging.WARNING
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
        self._active_calls: Dict[int, Any] = {}
        self._event_handlers: Dict[str, List[Callable]] = {
            'stream_end': [],
            'stream_start': [],
            'stream_paused': [],
            'stream_resumed': [],
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
        
        # Add stream methods  
        for method_name in dir(StreamMethods):
            if not method_name.startswith('_') and callable(getattr(StreamMethods, method_name)):
                method = getattr(StreamMethods, method_name)
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
            
            # Setup event handlers
            await self._event_handler.setup()
            
            self._is_connected = True
            self._logger.info("TgCaller started successfully")
            
        except Exception as e:
            self._logger.error(f"Failed to start TgCaller: {e}")
            raise ConnectionError(f"Failed to start TgCaller: {e}")
    
    async def stop(self) -> None:
        """
        Stop TgCaller service and cleanup resources
        """
        if not self._is_connected:
            self._logger.warning("TgCaller is not running")
            return
            
        try:
            # Leave all active calls
            for chat_id in list(self._active_calls.keys()):
                await self.leave_call(chat_id)
            
            # Cleanup
            await self._event_handler.cleanup()
            self._is_connected = False
            
            self._logger.info("TgCaller stopped successfully")
            
        except Exception as e:
            self._logger.error(f"Error stopping TgCaller: {e}")
    
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
    
    def _add_handler(self, event_type: str, handler: Callable) -> None:
        """Add event handler"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
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
    
    async def _validate_media(self, stream: MediaStream):
        """Validate media stream"""
        if stream.is_file:
            if not Path(stream.source).exists():
                raise MediaError(f"File not found: {stream.source}")
        elif not stream.is_url:
            raise MediaError(f"Invalid media source: {stream.source}")
    
    async def _simulate_playback(self, chat_id: int, stream: MediaStream):
        """Simulate media playback"""
        try:
            duration = stream.duration or 10.0
            
            for i in range(int(duration)):
                if chat_id not in self._active_calls:
                    break
                
                call_session = self._active_calls[chat_id]
                
                if call_session.get('status') != CallStatus.PLAYING:
                    break
                
                call_session['position'] = i + 1
                await asyncio.sleep(1)
            
            # Stream ended
            if chat_id in self._active_calls:
                call_session = self._active_calls[chat_id]
                
                if stream.repeat:
                    await self.play(chat_id, stream)
                else:
                    call_session['status'] = CallStatus.CONNECTED
                    call_session.pop('current_stream', None)
                    
                    update = CallUpdate(
                        chat_id=chat_id,
                        status=CallStatus.CONNECTED,
                        message="Stream ended"
                    )
                    await self._emit_event('stream_end', update)
                    
        except Exception as e:
            self._logger.error(f"Playback error in chat {chat_id}: {e}")
    
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