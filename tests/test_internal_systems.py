"""
Test Internal Systems
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from tgcaller.internal import ConnectionManager, CacheManager, StreamHandler, CallHandler, RetryManager
from tgcaller.types import CallUpdate, CallStatus, MediaStream, AudioConfig


class TestConnectionManager:
    """Test Connection Manager"""
    
    @pytest.fixture
    def mock_caller(self):
        caller = Mock()
        caller._active_calls = {}
        caller._emit_event = AsyncMock()
        caller._logger = Mock()
        return caller
    
    @pytest.fixture
    def connection_manager(self, mock_caller):
        return ConnectionManager(mock_caller)
    
    @pytest.mark.asyncio
    async def test_connect_call(self, connection_manager):
        """Test call connection"""
        chat_id = -1001234567890
        
        success = await connection_manager.connect_call(chat_id)
        assert success is True
        assert connection_manager.is_connected(chat_id) is True
    
    @pytest.mark.asyncio
    async def test_disconnect_call(self, connection_manager):
        """Test call disconnection"""
        chat_id = -1001234567890
        
        # Connect first
        await connection_manager.connect_call(chat_id)
        assert connection_manager.is_connected(chat_id) is True
        
        # Then disconnect
        success = await connection_manager.disconnect_call(chat_id)
        assert success is True
        assert connection_manager.is_connected(chat_id) is False


class TestCacheManager:
    """Test Cache Manager"""
    
    @pytest.fixture
    def cache_manager(self):
        return CacheManager(max_size=10, default_ttl=1.0)
    
    def test_cache_operations(self, cache_manager):
        """Test basic cache operations"""
        # Set value
        cache_manager.set("test_key", "test_value")
        
        # Get value
        value = cache_manager.get("test_key")
        assert value == "test_value"
        
        # Delete value
        success = cache_manager.delete("test_key")
        assert success is True
        
        # Get deleted value
        value = cache_manager.get("test_key")
        assert value is None
    
    def test_peer_caching(self, cache_manager):
        """Test peer caching functionality"""
        chat_id = -1001234567890
        peer_data = {"id": 123, "access_hash": 456}
        
        # Cache peer
        cache_manager.cache_user_peer(chat_id, peer_data)
        
        # Retrieve peer
        cached_peer = cache_manager.get_user_peer(chat_id)
        assert cached_peer == peer_data
    
    def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        # Add some data
        cache_manager.set("key1", "value1")
        cache_manager.get("key1")  # Hit
        cache_manager.get("key2")  # Miss
        
        stats = cache_manager.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1


class TestStreamHandler:
    """Test Stream Handler"""
    
    @pytest.fixture
    def mock_caller(self):
        caller = Mock()
        caller._emit_event = AsyncMock()
        caller._logger = Mock()
        return caller
    
    @pytest.fixture
    def stream_handler(self, mock_caller):
        return StreamHandler(mock_caller)
    
    @pytest.mark.asyncio
    async def test_start_stream(self, stream_handler):
        """Test starting stream"""
        chat_id = -1001234567890
        stream = MediaStream("test.mp3")
        
        success = await stream_handler.start_stream(chat_id, stream)
        assert success is True
        assert stream_handler.is_streaming(chat_id) is True
    
    @pytest.mark.asyncio
    async def test_stop_stream(self, stream_handler):
        """Test stopping stream"""
        chat_id = -1001234567890
        stream = MediaStream("test.mp3")
        
        # Start stream first
        await stream_handler.start_stream(chat_id, stream)
        assert stream_handler.is_streaming(chat_id) is True
        
        # Stop stream
        success = await stream_handler.stop_stream(chat_id)
        assert success is True
        assert stream_handler.is_streaming(chat_id) is False


class TestRetryManager:
    """Test Retry Manager"""
    
    @pytest.fixture
    def retry_manager(self):
        return RetryManager()
    
    @pytest.mark.asyncio
    async def test_successful_operation(self, retry_manager):
        """Test successful operation without retries"""
        async def successful_operation():
            return "success"
        
        result = await retry_manager.retry_operation(
            successful_operation,
            "test_op"
        )
        
        assert result == "success"
        assert retry_manager.get_retry_count("test_op") == 0
    
    @pytest.mark.asyncio
    async def test_retry_operation(self, retry_manager):
        """Test operation that succeeds after retries"""
        call_count = 0
        
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        from tgcaller.internal.retry_manager import RetryConfig
        config = RetryConfig(max_attempts=5, base_delay=0.1)
        
        result = await retry_manager.retry_operation(
            failing_then_success,
            "test_retry",
            config
        )
        
        assert result == "success"
        assert call_count == 3