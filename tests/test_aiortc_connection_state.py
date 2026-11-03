import asyncio
from types import SimpleNamespace

import pytest

from tgcaller.mtproto.engine.aiortc_engine import (
    AiortcTelegramMediaEngine,
    _Session,
)


def _session(state="connecting"):
    return _Session(
        pc=SimpleNamespace(connectionState=state),
        track=None,
        source_id=123,
        local_offer_sdp="",
        connected_event=asyncio.Event(),
        state_changed_event=asyncio.Event(),
        state=state,
    )


@pytest.mark.asyncio
async def test_connection_state_reports_current_aiortc_state():
    engine = AiortcTelegramMediaEngine()
    engine._sessions[100] = _session("disconnected")

    assert engine.get_connection_state(100) == "disconnected"
    assert await engine.is_connected(100) is False

    engine._sessions[100].pc.connectionState = "connected"
    assert engine.get_connection_state(100) == "connected"
    assert await engine.is_connected(100) is True


@pytest.mark.asyncio
async def test_wait_for_connection_state_observes_later_transition():
    engine = AiortcTelegramMediaEngine()
    session = _session("connecting")
    engine._sessions[100] = session

    async def transition():
        await asyncio.sleep(0)
        session.pc.connectionState = "connected"
        session.state_changed_event.set()

    transition_task = asyncio.create_task(transition())
    try:
        state = await engine.wait_for_connection_state(
            100, {"connected", "failed"}, timeout=1
        )
    finally:
        await transition_task

    assert state == "connected"


@pytest.mark.asyncio
async def test_wait_for_connection_state_returns_closed_after_session_removal():
    engine = AiortcTelegramMediaEngine()
    engine._sessions[100] = _session("connecting")

    async def remove_session():
        await asyncio.sleep(0)
        session = engine._sessions.pop(100)
        session.state_changed_event.set()

    removal_task = asyncio.create_task(remove_session())
    try:
        assert await engine.wait_for_connection_state(
            100, "closed", timeout=1
        ) == "closed"
    finally:
        await removal_task


@pytest.mark.asyncio
async def test_wait_for_connection_state_rejects_invalid_states_and_timeout():
    engine = AiortcTelegramMediaEngine()
    engine._sessions[100] = _session("connecting")

    with pytest.raises(ValueError, match="valid aiortc connection states"):
        await engine.wait_for_connection_state(100, "reconnecting")

    with pytest.raises(asyncio.TimeoutError):
        await engine.wait_for_connection_state(100, "connected", timeout=0.01)


def test_missing_session_is_reported_as_closed():
    engine = AiortcTelegramMediaEngine()
    assert engine.get_connection_state(999) == "closed"
