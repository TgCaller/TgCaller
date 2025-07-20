"""
Test Event Handler System
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from tgcaller.handlers.event_system import (
    EventHandlerSystem, 
    Filters, 
    and_filter, 
    or_filter,
    HandlerInfo
)
from tgcaller.types import CallUpdate, CallStatus


class TestEventHandlerSystem:
    """Test Event Handler System"""
    
    @pytest.fixture
    def event_system(self):
        """Create event system instance"""
        return EventHandlerSystem()
    
    @pytest.fixture
    def mock_update(self):
        """Create mock update"""
        return CallUpdate(
            chat_id=-1001234567890,
            status=CallStatus.CONNECTED,
            message="Test update"
        )
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client"""
        return Mock()
    
    def test_add_handler(self, event_system):
        """Test adding handler"""
        def test_handler(client, update):
            pass
        
        event_system.add_handler(test_handler, priority=5)
        
        assert event_system.get_handlers_count() == 1
        assert event_system.handlers[0].func == test_handler
        assert event_system.handlers[0].priority == 5
    
    def test_handler_priority_order(self, event_system):
        """Test handler priority ordering"""
        def handler1(client, update):
            pass
        
        def handler2(client, update):
            pass
        
        def handler3(client, update):
            pass
        
        # Add handlers with different priorities
        event_system.add_handler(handler1, priority=1)
        event_system.add_handler(handler3, priority=10)
        event_system.add_handler(handler2, priority=5)
        
        # Check order (highest priority first)
        assert event_system.handlers[0].func == handler3  # priority 10
        assert event_system.handlers[1].func == handler2  # priority 5
        assert event_system.handlers[2].func == handler1  # priority 1
    
    def test_remove_handler(self, event_system):
        """Test removing handler"""
        def test_handler(client, update):
            pass
        
        event_system.add_handler(test_handler)
        assert event_system.get_handlers_count() == 1
        
        success = event_system.remove_handler(test_handler)
        assert success is True
        assert event_system.get_handlers_count() == 0
        
        # Try removing non-existent handler
        success = event_system.remove_handler(test_handler)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_propagate_sync_handler(self, event_system, mock_update, mock_client):
        """Test propagating to synchronous handler"""
        called = False
        
        def sync_handler(client, update):
            nonlocal called
            called = True
            assert client == mock_client
            assert update == mock_update
        
        event_system.add_handler(sync_handler)
        await event_system._propagate(mock_update, mock_client)
        
        assert called is True
    
    @pytest.mark.asyncio
    async def test_propagate_async_handler(self, event_system, mock_update, mock_client):
        """Test propagating to asynchronous handler"""
        called = False
        
        async def async_handler(client, update):
            nonlocal called
            called = True
            assert client == mock_client
            assert update == mock_update
        
        event_system.add_handler(async_handler)
        await event_system._propagate(mock_update, mock_client)
        
        assert called is True
    
    @pytest.mark.asyncio
    async def test_filter_chat_id(self, event_system, mock_client):
        """Test chat ID filter"""
        called = False
        
        async def filtered_handler(client, update):
            nonlocal called
            called = True
        
        # Add handler with chat filter
        chat_filter = Filters.chat_id(-1001234567890)
        event_system.add_handler(filtered_handler, filters=chat_filter)
        
        # Test with matching chat ID
        update1 = CallUpdate(chat_id=-1001234567890, status=CallStatus.CONNECTED)
        await event_system._propagate(update1, mock_client)
        assert called is True
        
        # Reset and test with non-matching chat ID
        called = False
        update2 = CallUpdate(chat_id=-1009876543210, status=CallStatus.CONNECTED)
        await event_system._propagate(update2, mock_client)
        assert called is False
    
    @pytest.mark.asyncio
    async def test_filter_status(self, event_system, mock_client):
        """Test status filter"""
        called = False
        
        async def status_handler(client, update):
            nonlocal called
            called = True
        
        # Add handler with status filter
        status_filter = Filters.status("playing")
        event_system.add_handler(status_handler, filters=status_filter)
        
        # Test with matching status
        update1 = CallUpdate(chat_id=-1001234567890, status=CallStatus.PLAYING)
        await event_system._propagate(update1, mock_client)
        assert called is True
        
        # Reset and test with non-matching status
        called = False
        update2 = CallUpdate(chat_id=-1001234567890, status=CallStatus.CONNECTED)
        await event_system._propagate(update2, mock_client)
        assert called is False
    
    @pytest.mark.asyncio
    async def test_and_filter(self, event_system, mock_client):
        """Test AND filter combination"""
        called = False
        
        async def and_handler(client, update):
            nonlocal called
            called = True
        
        # Add handler with AND filter
        combined_filter = and_filter(
            Filters.chat_id(-1001234567890),
            Filters.status("connected")
        )
        event_system.add_handler(and_handler, filters=combined_filter)
        
        # Test with both conditions true
        update1 = CallUpdate(chat_id=-1001234567890, status=CallStatus.CONNECTED)
        await event_system._propagate(update1, mock_client)
        assert called is True
        
        # Reset and test with one condition false
        called = False
        update2 = CallUpdate(chat_id=-1001234567890, status=CallStatus.PLAYING)
        await event_system._propagate(update2, mock_client)
        assert called is False
    
    @pytest.mark.asyncio
    async def test_or_filter(self, event_system, mock_client):
        """Test OR filter combination"""
        called_count = 0
        
        async def or_handler(client, update):
            nonlocal called_count
            called_count += 1
        
        # Add handler with OR filter
        combined_filter = or_filter(
            Filters.chat_id(-1001234567890),
            Filters.chat_id(-1009876543210)
        )
        event_system.add_handler(or_handler, filters=combined_filter)
        
        # Test with first condition true
        update1 = CallUpdate(chat_id=-1001234567890, status=CallStatus.CONNECTED)
        await event_system._propagate(update1, mock_client)
        assert called_count == 1
        
        # Test with second condition true
        update2 = CallUpdate(chat_id=-1009876543210, status=CallStatus.CONNECTED)
        await event_system._propagate(update2, mock_client)
        assert called_count == 2
        
        # Test with neither condition true
        update3 = CallUpdate(chat_id=-1005566778899, status=CallStatus.CONNECTED)
        await event_system._propagate(update3, mock_client)
        assert called_count == 2  # Should not increment
    
    def test_clear_handlers(self, event_system):
        """Test clearing all handlers"""
        def handler1(client, update):
            pass
        
        def handler2(client, update):
            pass
        
        event_system.add_handler(handler1)
        event_system.add_handler(handler2)
        assert event_system.get_handlers_count() == 2
        
        event_system.clear_handlers()
        assert event_system.get_handlers_count() == 0