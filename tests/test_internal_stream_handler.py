"""Regression tests for StreamHandler transport delegation."""

from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.internal.stream_handler import StreamHandler, StreamState


@pytest.mark.asyncio
async def test_stream_handler_delegates_playback_instead_of_generating_mock_frames():
    caller = Mock()
    caller.play = AsyncMock(return_value=True)
    caller.pause = AsyncMock(return_value=True)
    caller.resume = AsyncMock(return_value=True)
    caller.seek = AsyncMock(return_value=True)
    caller.stop_stream = AsyncMock(return_value=True)
    caller._emit_event = AsyncMock()
    handler = StreamHandler(caller)
    stream = Mock(source="sample.mp3")

    assert await handler.start_stream(123, stream, device=Mock()) is True
    caller.play.assert_awaited_once_with(123, stream)
    assert handler.get_stream_state(123) is StreamState.PLAYING
    assert not hasattr(handler, "_generate_mock_frame")

    assert await handler.pause_stream(123) is True
    assert handler.get_stream_state(123) is StreamState.PAUSED
    assert await handler.resume_stream(123) is True
    assert handler.get_stream_state(123) is StreamState.PLAYING
    assert await handler.seek_stream(123, 12.5) is True
    assert handler.get_stream_position(123) == 12.5
    assert await handler.stop_stream(123) is True
    caller.stop_stream.assert_awaited_once_with(123)
    caller._emit_event.assert_awaited_once()
    assert handler.get_stream_state(123) is None


@pytest.mark.asyncio
async def test_stream_handler_does_not_mark_playing_when_transport_rejects():
    caller = Mock()
    caller.play = AsyncMock(return_value=False)
    handler = StreamHandler(caller)

    assert await handler.start_stream(456, Mock(source="sample.mp3")) is False
    assert handler.get_stream_state(456) is None
