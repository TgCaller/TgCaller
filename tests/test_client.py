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


class FakeCallsBackend:
    """Deterministic fake for testing backend integration."""

    def __init__(self):
        self.play_calls = []
        self.volume_calls = []
        self.leave_calls = []
        self.pause_calls = []
        self.resume_calls = []
        self.mute_calls = []
        self.unmute_calls = []
        self.update_handler = None
        self.started = False

    async def start(self):
        self.started = True

    def on_update(self, filters=None):
        def register(handler):
            self.update_handler = handler
            return handler
        return register

    async def play(self, chat_id, stream=None):
        self.play_calls.append((chat_id, stream))

    async def leave_call(self, chat_id):
        self.leave_calls.append(chat_id)
        return True

    async def pause(self, chat_id):
        self.pause_calls.append(chat_id)
        return True

    async def resume(self, chat_id):
        self.resume_calls.append(chat_id)
        return True

    async def mute(self, chat_id):
        self.mute_calls.append(chat_id)
        return True

    async def unmute(self, chat_id):
        self.unmute_calls.append(chat_id)
        return True

    async def change_volume_call(self, chat_id, volume):
        self.volume_calls.append((chat_id, volume))

    async def time(self, chat_id):
        return 12.5

    async def get_participants(self, chat_id):
        return []


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
    def mock_calls_backend(self):
        return FakeCallsBackend()

    @pytest.fixture
    def caller(self, mock_client, mock_calls_backend):
        """Create TgCaller with a fake transport backend."""
        return TgCaller(mock_client, calls_backend=mock_calls_backend)

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
    async def test_start_stop(self, caller, mock_client, mock_calls_backend):
        """Test starting and stopping TgCaller"""
        # Test start
        await caller.start()
        assert caller.is_running
        assert mock_calls_backend.started is True
        mock_client.start.assert_called_once()
        
        # Test stop
        await caller.stop()
        assert not caller.is_running
    
    @pytest.mark.asyncio
    async def test_join_call(self, caller, mock_client, mock_calls_backend):
        """Test joining a call"""
        await caller.start()
        
        chat_id = -1001234567890
        result = await caller.join_call(chat_id)
        
        assert result is True
        assert caller.is_connected(chat_id)
        assert chat_id in caller.get_active_calls()
        assert (chat_id, None) in mock_calls_backend.play_calls
    
    @pytest.mark.asyncio
    async def test_leave_call(self, caller, mock_client, mock_calls_backend):
        """Test leaving a call"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Join first
        await caller.join_call(chat_id)
        assert caller.is_connected(chat_id)
        
        # Then leave
        result = await caller.leave_call(chat_id)
        assert result is True
        assert mock_calls_backend.leave_calls == [chat_id]
        assert not caller.is_connected(chat_id)
    
    @pytest.mark.asyncio
    async def test_play_media(self, caller, mock_client, temp_audio_file, mock_calls_backend):
        """Test playing media"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Test playing audio with temporary file
        result = await caller.play(chat_id, temp_audio_file)
        assert result is True
        assert caller.is_connected(chat_id)
        assert (chat_id, temp_audio_file) in mock_calls_backend.play_calls
    
    @pytest.mark.asyncio
    async def test_pause_resume(self, caller, mock_client, temp_audio_file, mock_calls_backend):
        """Test pause and resume"""
        await caller.start()
        
        chat_id = -1001234567890
        
        # Start playing
        await caller.play(chat_id, temp_audio_file)
        
        # Pause
        result = await caller.pause(chat_id)
        assert result is True
        assert mock_calls_backend.pause_calls == [chat_id]
        
        # Resume
        result = await caller.resume(chat_id)
        assert result is True
        assert mock_calls_backend.resume_calls == [chat_id]
    
    @pytest.mark.asyncio
    async def test_volume_control(self, caller, mock_client, mock_calls_backend):
        """Test volume control"""
        await caller.start()
        
        chat_id = -1001234567890
        await caller.join_call(chat_id)
        
        # Set volume
        result = await caller.set_volume(chat_id, 0.8)
        assert result is True
        assert (chat_id, 80) in mock_calls_backend.volume_calls
        
        # Test invalid volume
        with pytest.raises(ValueError):
            await caller.set_volume(chat_id, 1.5)
    
    @pytest.mark.asyncio
    async def test_backend_stream_end_update(self, caller, mock_calls_backend, temp_audio_file):
        """Backend stream-end updates should reach TgCaller's event bridge."""
        await caller.start()
        chat_id = -1001234567890
        await caller.play(chat_id, temp_audio_file)
        assert mock_calls_backend.update_handler is not None

        class StreamEnded:
            def __init__(self, chat_id):
                self.chat_id = chat_id

        await mock_calls_backend.update_handler(mock_calls_backend, StreamEnded(chat_id))
        assert "current_stream" not in caller._active_calls[chat_id]
        assert caller._active_calls[chat_id]["status"] == CallStatus.CONNECTED

        await caller.stop()

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