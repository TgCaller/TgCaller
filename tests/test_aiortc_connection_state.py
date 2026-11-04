import asyncio
from types import SimpleNamespace

import pytest

from tgcaller.exceptions import ConnectionError
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


class _RecordingTrack:
    def __init__(self):
        self.frames = []

    async def push(self, frame):
        self.frames.append(frame)


@pytest.mark.asyncio
async def test_send_frame_waits_through_transient_disconnect_without_queueing_stale_audio():
    engine = AiortcTelegramMediaEngine()
    session = _session("disconnected")
    session.track = _RecordingTrack()
    engine._sessions[100] = session

    send_task = asyncio.create_task(engine.send_frame(100, b"fresh-frame", "audio"))
    await asyncio.sleep(0)
    assert session.track.frames == []

    session.pc.connectionState = "connected"
    session.state_changed_event.set()

    assert await asyncio.wait_for(send_task, timeout=1) is True
    assert session.track.frames == [b"fresh-frame"]


@pytest.mark.asyncio
async def test_send_frame_aborts_when_transient_disconnect_becomes_failed():
    engine = AiortcTelegramMediaEngine()
    session = _session("disconnected")
    session.track = _RecordingTrack()
    engine._sessions[100] = session

    send_task = asyncio.create_task(engine.send_frame(100, b"must-not-send", "audio"))
    await asyncio.sleep(0)
    session.pc.connectionState = "failed"
    session.state_changed_event.set()

    with pytest.raises(ConnectionError, match="state=failed"):
        await asyncio.wait_for(send_task, timeout=1)
    assert session.track.frames == []


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["failed", "closed"])
async def test_send_frame_fails_closed_for_terminal_transport_states(state):
    engine = AiortcTelegramMediaEngine()
    session = _session(state)
    session.track = _RecordingTrack()
    engine._sessions[100] = session

    with pytest.raises(ConnectionError, match=f"state={state}"):
        await engine.send_frame(100, b"must-not-send", "audio")
    assert session.track.frames == []


@pytest.mark.asyncio
@pytest.mark.parametrize("state", ["disconnected", "failed"])
async def test_transport_loss_aborts_managed_stream_and_notifies_client(state):
    engine = AiortcTelegramMediaEngine()
    session = _session(state)
    engine._sessions[100] = session
    stopped = []
    notifications = []

    async def stop_stream(chat_id):
        stopped.append(chat_id)
        return True

    async def on_stream_end(chat_id, error):
        notifications.append((chat_id, str(error)))

    engine.stop_stream = stop_stream
    engine.on_stream_end = on_stream_end

    await engine._abort_stream_after_transport_loss(100, session, state)

    assert stopped == [100]
    assert notifications == [(
        100,
        f"Managed media stream stopped because WebRTC state became {state}",
    )]


@pytest.mark.asyncio
async def test_transport_loss_cleanup_ignores_replaced_session():
    engine = AiortcTelegramMediaEngine()
    old_session = _session("disconnected")
    engine._sessions[100] = _session("connected")
    stopped = []

    async def stop_stream(chat_id):
        stopped.append(chat_id)
        return True

    engine.stop_stream = stop_stream

    await engine._abort_stream_after_transport_loss(100, old_session, "disconnected")

    assert stopped == []
