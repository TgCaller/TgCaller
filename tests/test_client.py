"""
Test TgCaller Client
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock
import pyrogram  # <-- Add this import

from tgcaller import TgCaller
from tgcaller.types import AudioConfig, VideoConfig, CallStatus
from tgcaller.exceptions import CallError


class FakeTransport:
    """Test-only transport; this does not implement Telegram networking."""

    async def connect_call(self, chat_id, audio_config, video_config):
        return True

    async def disconnect_call(self, chat_id):
        return True

    async def is_healthy(self, chat_id):
        return True

    async def get_participants(self, chat_id):
        return []

    async def play_stream(self, chat_id, stream):
        return True

    async def stop_stream(self, chat_id):
        return True

    async def send_frame(self, chat_id, frame_data, frame_type):
        return True


class TestTgCaller:
    """Test TgCaller main client"""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Pyrogram client"""
        client = Mock(spec=pyrogram.Client)  # <-- Use spec
        client.is_connected = False
        client.start = AsyncMock()
        client.stop = AsyncMock()
        return client
    
    @pytest.fixture
    def caller(self, mock_client):
        """Create TgCaller instance"""
        return TgCaller(mock_client, connection_backend=FakeTransport())
    
    @pytest.fixture
    def temp_audio_file(self):
        """Create temporary audio file for testing"""
        # Create a temporary file with .mp3 extension
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            # Write some dummy content to make it a valid file
            temp_file.write(b'dummy audio content')
            temp_file_path = temp_file.name
        
        yield temp_file_path
        
        # Cleanup after test
        try:
            os.unlink(temp_file_path)
        except FileNotFoundError:
            pass
    
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
    async def test_join_call_fails_without_real_transport(self, mock_client):
        caller = TgCaller(mock_client)
        await caller.start()
        with pytest.raises(CallError, match="Could not join Telegram group call"):
            await caller.join_call(-1001234567890)
        assert caller.get_active_calls() == []
        await caller.stop()

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
    async def test_play_media(self, caller, mock_client, temp_audio_file):
        """Test playing media"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Test playing audio with temporary file
        result = await caller.play(chat_id, temp_audio_file)
        assert result is True
        assert caller.is_connected(chat_id)
    
    @pytest.mark.asyncio
    async def test_pause_resume(self, caller, mock_client, temp_audio_file):
        """Test pause and resume"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Start playing
        await caller.play(chat_id, temp_audio_file)
        
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

    @pytest.mark.asyncio
    async def test_stream_start_event_dispatch(self, caller):
        await caller.start()
        received = []

        @caller.on_stream_start
        async def on_stream_start(client, update):
            received.append(update)

        update = object()
        await caller._emit_event("stream_start", update)

        assert received == [update]
        await caller.stop()

    @pytest.mark.asyncio
    async def test_stream_stopped_event_dispatch(self, caller):
        await caller.start()
        received = []

        @caller.on_stream_stopped
        async def on_stream_stopped(client, update):
            received.append(update)

        update = object()
        await caller._emit_event("stream_stopped", update)

        assert received == [update]
        await caller.stop()

    @pytest.mark.asyncio
    async def test_on_left_uses_call_left_event(self, caller):
        received = []

        @caller.on_left
        async def on_left(client, update):
            received.append(update)

        update = object()
        await caller._emit_event("call_left", update)

        assert received == [update]

    @pytest.mark.asyncio
    async def test_stop_attempts_all_cleanup_steps_after_failure(self, caller):
        await caller.start()
        caller._connection_manager.cleanup_all = AsyncMock(
            side_effect=RuntimeError("connection cleanup failed")
        )
        cache_cleanup = AsyncMock()
        stream_cleanup = AsyncMock()
        call_cleanup = AsyncMock()
        event_cleanup = AsyncMock()
        caller._cache_manager.cleanup = cache_cleanup
        caller._stream_handler.cleanup_all = stream_cleanup
        caller._call_handler.cleanup_all = call_cleanup
        caller._event_handler.cleanup = event_cleanup

        await caller.stop()

        assert not caller.is_running
        cache_cleanup.assert_awaited_once()
        stream_cleanup.assert_awaited_once()
        call_cleanup.assert_awaited_once()
        event_cleanup.assert_awaited_once()

