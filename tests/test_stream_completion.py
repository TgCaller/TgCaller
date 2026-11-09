"""Tests for natural media stream completion propagation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from tgcaller.client import TgCaller
from tgcaller.mtproto.engine.aiortc_engine import AiortcTelegramMediaEngine
from tgcaller.types import CallStatus


@pytest.mark.asyncio
async def test_engine_notifies_client_after_async_source_finishes():
    engine = AiortcTelegramMediaEngine()
    engine.send_frame = AsyncMock(return_value=True)
    engine.on_stream_end = AsyncMock()

    async def source():
        yield b"first"
        yield b"second"

    await engine._pump_async_iterable(123, source())

    assert engine.send_frame.await_count == 2
    engine.on_stream_end.assert_awaited_once_with(123, None)


@pytest.mark.asyncio
async def test_client_clears_playing_state_and_emits_stream_end():
    caller = object.__new__(TgCaller)
    caller._active_calls = {
        123: {
            "current_stream": SimpleNamespace(source="song.mp3"),
            "status": CallStatus.PLAYING,
        }
    }
    caller._emit_event = AsyncMock()

    await caller._handle_media_stream_end(123)

    assert caller._active_calls[123]["status"] is CallStatus.CONNECTED
    assert "current_stream" not in caller._active_calls[123]
    caller._emit_event.assert_awaited_once()
    event_name, update = caller._emit_event.await_args.args
    assert event_name == "stream_end"
    assert update.chat_id == 123
    assert update.status is CallStatus.CONNECTED
    assert update.message == "Stream ended"


@pytest.mark.asyncio
async def test_client_emits_error_and_stream_end_after_decode_failure():
    caller = object.__new__(TgCaller)
    caller._active_calls = {
        123: {
            "current_stream": SimpleNamespace(source="song.mp3"),
            "status": CallStatus.PLAYING,
        }
    }
    caller._emit_event = AsyncMock()
    failure = RuntimeError("decoder failed")

    await caller._handle_media_stream_end(123, failure)

    assert [call.args[0] for call in caller._emit_event.await_args_list] == [
        "error",
        "stream_end",
    ]
    assert caller._active_calls[123]["status"] is CallStatus.CONNECTED
    assert "current_stream" not in caller._active_calls[123]
