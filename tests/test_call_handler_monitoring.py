"""Tests for real call-health and participant monitoring."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.internal.call_handler import CallHandler
from tgcaller.types import CallStatus


@pytest.mark.asyncio
async def test_call_health_marks_session_error_when_media_transport_is_down():
    caller = Mock()
    caller._active_calls = {123: {"status": CallStatus.CONNECTED}}
    caller._connection.is_healthy = AsyncMock(return_value=False)
    caller._emit_event = AsyncMock()
    handler = CallHandler(caller)

    await handler._check_call_health(123)

    assert caller._active_calls[123]["status"] is CallStatus.ERROR
    caller._emit_event.assert_awaited_once()
    assert caller._emit_event.await_args.args[0] == "error"


@pytest.mark.asyncio
async def test_participant_monitor_adds_and_removes_real_telegram_participants():
    caller = Mock()
    caller._active_calls = {123: {"status": CallStatus.CONNECTED}}
    raw = SimpleNamespace(
        peer=SimpleNamespace(user_id=456),
        muted=True,
        muted_by_admin=True,
        video=None,
        presentation=None,
        date=1700000000,
        source=77,
    )
    caller.get_participants = AsyncMock(side_effect=[[raw], []])
    caller._emit_event = AsyncMock()
    handler = CallHandler(caller)

    await handler._update_participants(123)
    participant = handler.call_participants[123][456]
    assert participant.muted is True
    assert participant.muted_by_admin is True
    assert handler.is_muted_by_admin(123) is True

    await handler._update_participants(123)
    assert handler.get_participant_count(123) == 0
    assert handler.is_muted_by_admin(123) is False
    assert caller._emit_event.await_count == 2
