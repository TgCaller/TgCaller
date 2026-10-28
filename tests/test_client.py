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
from tgcaller.mtproto import AiortcTelegramMediaEngine, PyrogramGroupCallBackend


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

    async def pause_stream(self, chat_id):
        self.pause_calls = getattr(self, "pause_calls", 0) + 1
        return True

    async def resume_stream(self, chat_id):
        self.resume_calls = getattr(self, "resume_calls", 0) + 1
        return True

    async def mute(self, chat_id):
        return True

    async def unmute(self, chat_id):
        return True

    async def set_volume(self, chat_id, volume):
        self.last_volume = volume
        return True

    async def seek(self, chat_id, position):
        self.last_position = position
        return True

    async def get_position(self, chat_id):
        return getattr(self, "reported_position", None)

    async def start_recording(self, chat_id, output_path, audio_config):
        return True

    async def stop_recording(self, chat_id):
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
    
    def test_default_transport_uses_builtin_telegram_audio_engine(self, mock_client):
        caller = TgCaller(mock_client)

        assert isinstance(caller._connection.backend, PyrogramGroupCallBackend)
        assert isinstance(
            caller._connection.backend.media_engine, AiortcTelegramMediaEngine
        )
        assert caller._owns_connection_backend is True

    @pytest.mark.asyncio
    async def test_join_call_fails_when_telegram_call_cannot_be_resolved(self, mock_client):
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
        assert caller._connection.backend.pause_calls == 1
        assert await caller.get_call_status(chat_id) == CallStatus.PAUSED.value

        # A second pause is not reported as a successful transport action.
        assert await caller.pause(chat_id) is False
        assert caller._connection.backend.pause_calls == 1

        # Resume
        result = await caller.resume(chat_id)
        assert result is True
        assert caller._connection.backend.resume_calls == 1
        assert await caller.get_call_status(chat_id) == CallStatus.PLAYING.value
    
    @pytest.mark.asyncio
    async def test_pause_resume_fail_when_transport_does_not_support_them(
        self, caller, mock_client, temp_audio_file
    ):
        await caller.start()
        chat_id = -1001234567890
        await caller.play(chat_id, temp_audio_file)
        backend = caller._connection.backend

        # Unsupported transport operations must not produce false success.
        backend.pause_stream = None
        assert await caller.pause(chat_id) is False
        assert await caller.get_call_status(chat_id) == CallStatus.PLAYING.value

        caller._active_calls[chat_id]["status"] = CallStatus.PAUSED
        backend.resume_stream = None
        assert await caller.resume(chat_id) is False
        assert await caller.get_call_status(chat_id) == CallStatus.PAUSED.value
        await caller.stop()

    @pytest.mark.asyncio
    async def test_volume_seek_and_mute_fail_closed_without_transport_support(
        self, caller, mock_client, temp_audio_file
    ):
        await caller.start()
        chat_id = -1001234567890
        await caller.play(chat_id, temp_audio_file)
        backend = caller._connection.backend

        backend.set_volume = None
        assert await caller.set_volume(chat_id, 0.5) is False
        assert "volume" not in caller._active_calls[chat_id]

        backend.seek = None
        assert await caller.seek(chat_id, 15) is False
        assert caller._active_calls[chat_id].get("position", 0.0) == 0.0

        backend.mute = None
        assert await caller.mute(chat_id) is False
        assert caller._active_calls[chat_id].get("muted", False) is False
        await caller.stop()

    @pytest.mark.asyncio
    async def test_recording_fails_closed_without_transport_support(
        self, caller, mock_client
    ):
        await caller.start()
        chat_id = -1001234567890
        await caller.join_call(chat_id)
        caller._connection.backend.start_recording = None
        assert await caller.record(chat_id, "/tmp/tgcaller-test-recording.wav") is False
        assert "recording" not in caller._active_calls[chat_id]
        await caller.stop()

    @pytest.mark.asyncio
    async def test_playback_position_uses_transport_and_returns_none_when_unsupported(
        self, caller, mock_client, temp_audio_file
    ):
        await caller.start()
        chat_id = -1001234567890
        await caller.play(chat_id, temp_audio_file)
        backend = caller._connection.backend

        # Unknown position must not be reported as a fabricated 0.0 seconds.
        assert await caller.get_position(chat_id) is None
        assert await caller.get_time(chat_id) is None

        backend.reported_position = 12.5
        assert await caller.get_position(chat_id) == 12.5
        assert await caller.get_time(chat_id) == 12.5

        backend.get_position = None
        assert await caller.get_position(chat_id) is None

        backend.get_position = AsyncMock(
            side_effect=[float("nan"), float("inf"), -1, True, 10**1000]
        )
        for _ in range(5):
            assert await caller.get_position(chat_id) is None

        for invalid_position in (
            float("nan"),
            float("inf"),
            float("-inf"),
            10**1000,
        ):
            with pytest.raises(ValueError):
                await caller.seek(chat_id, invalid_position)
        await caller.stop()

    @pytest.mark.asyncio
    async def test_volume_control(self, caller, mock_client):
        """Test volume control"""
        await caller.start()
        
        chat_id = -1001234567890
        await caller.join_call(chat_id)
        
        # Set volume
        result = await caller.set_volume(chat_id, 0.8)
        assert result is True
        
        # Reject out-of-range, non-finite, boolean, and non-numeric values.
        for invalid_volume in (
            -0.1,
            1.5,
            float("nan"),
            float("inf"),
            float("-inf"),
            True,
            "0.5",
            10**1000,
        ):
            with pytest.raises(ValueError):
                await caller.set_volume(chat_id, invalid_volume)

        # Invalid input must not reach the backend.
        assert caller._connection.backend.last_volume == 0.8
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

    @pytest.mark.asyncio
    async def test_cancelled_join_removes_provisional_call_session(self, caller):
        await caller.start()
        caller._connection_manager.connect_call = AsyncMock(
            side_effect=asyncio.CancelledError()
        )

        with pytest.raises(asyncio.CancelledError):
            await caller.join_call(-1001234567890)

        assert caller.get_active_calls() == []
        await caller.stop()

