"""
Test TgCaller Client
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from tgcaller import TgCaller
from tgcaller.types import AudioConfig, VideoConfig, CallStatus


class TestTgCaller:
    """Test TgCaller main client"""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Pyrogram client"""
        client = Mock()
        client.is_connected = False
        client.start = AsyncMock()
        client.stop = AsyncMock()
        return client
    
    @pytest.fixture
    def caller(self, mock_client):
        """Create TgCaller instance"""
        return TgCaller(mock_client)
    
    @pytest.mark.asyncio
    async def test_start_stop(self, caller, mock_client):
        """Test starting and stopping TgCaller"""
        # Test start
        await caller.start()
        assert caller.is_running
        mock_client.start.assert_called_once()
        
        # Test stop
        await caller.stop()
        assert not caller.is_running
    
    @pytest.mark.asyncio
    async def test_join_call(self, caller, mock_client):
        """Test joining a call"""
        await caller.start()
        
        chat_id = -1001234567890
        result = await caller.join_call(chat_id)
        
        assert result is True
        assert caller.is_connected(chat_id)
        assert chat_id in caller.get_active_calls()
    
    @pytest.mark.asyncio
    async def test_leave_call(self, caller, mock_client):
        """Test leaving a call"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Join first
        await caller.join_call(chat_id)
        assert caller.is_connected(chat_id)
        
        # Then leave
        result = await caller.leave_call(chat_id)
        assert result is True
        assert not caller.is_connected(chat_id)
    
    @pytest.mark.asyncio
    async def test_play_media(self, caller, mock_client):
        """Test playing media"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Test playing audio
        result = await caller.play(chat_id, "test.mp3")
        assert result is True
        assert caller.is_connected(chat_id)
    
    @pytest.mark.asyncio
    async def test_pause_resume(self, caller, mock_client):
        """Test pause and resume"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Start playing
        await caller.play(chat_id, "test.mp3")
        
        # Pause
        result = await caller.pause(chat_id)
        assert result is True
        
        # Resume
        result = await caller.resume(chat_id)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_volume_control(self, caller, mock_client):
        """Test volume control"""
        await caller.start()
        
        chat_id = -1001234567890
        await caller.join_call(chat_id)
        
        # Set volume
        result = await caller.set_volume(chat_id, 0.8)
        assert result is True
        
        # Test invalid volume
        with pytest.raises(ValueError):
            await caller.set_volume(chat_id, 1.5)
    
    def test_event_handlers(self, caller):
        """Test event handler decorators"""
        
        @caller.on_stream_end
        async def on_stream_end(client, update):
            pass
        
        @caller.on_error
        async def on_error(client, error):
            pass
        
        assert len(caller._event_handlers['stream_end']) == 1
        assert len(caller._event_handlers['error']) == 1