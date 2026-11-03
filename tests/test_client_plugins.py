"""Tests for TgCaller plugin API and event integration."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.client import TgCaller


@pytest.mark.asyncio
async def test_client_exposes_plugin_lifecycle_methods():
    caller = object.__new__(TgCaller)
    caller._plugin_manager = Mock()
    caller._plugin_manager.register_plugin = AsyncMock()
    caller._plugin_manager.unregister_plugin = AsyncMock(return_value=True)
    caller._plugin_manager.get_plugin.return_value = object()
    caller._plugin_manager.is_plugin_loaded.return_value = True
    caller._plugin_manager.send_plugin_message = AsyncMock(return_value=True)

    plugin = object()
    await caller.register_plugin(plugin)
    assert await caller.unregister_plugin("sample") is True
    assert caller.get_plugin("sample") is not None
    assert caller.is_plugin_loaded("sample") is True
    assert await caller.send_plugin_message("sample", "hello") is True


@pytest.mark.asyncio
async def test_stream_start_event_is_forwarded_to_plugins():
    caller = object.__new__(TgCaller)
    caller._event_handlers = {}
    caller._event_system = Mock()
    caller._event_system._propagate = AsyncMock()
    caller._active_calls = {
        123: {"current_stream": SimpleNamespace(source="song.mp3")}
    }
    caller._plugin_manager = Mock()
    caller._plugin_manager.emit_event = AsyncMock()
    caller._logger = Mock()
    update = SimpleNamespace(chat_id=123)

    await caller._emit_event("stream_start", update)

    caller._plugin_manager.emit_event.assert_awaited_once_with(
        "on_stream_start", 123, "song.mp3"
    )
