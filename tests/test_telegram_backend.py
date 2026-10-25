"""Tests for the independent Pyrogram signaling adapter boundary."""

import pytest

from tgcaller.exceptions import ConnectionError
from tgcaller.mtproto import PyrogramGroupCallBackend
from tgcaller.mtproto.telegram_backend import _validate_join_payload


def test_backend_requires_real_media_engine():
    with pytest.raises(TypeError, match="media_engine is required"):
        PyrogramGroupCallBackend(object(), lambda chat_id: None, None)


@pytest.mark.asyncio
async def test_backend_refuses_to_join_when_no_active_call_is_resolved():
    class Engine:
        async def create_join_payload(self, chat_id, audio_config, video_config):
            return {"ssrc": 123}

    class Client:
        async def invoke(self, request):
            raise AssertionError("RPC must not be invoked without a resolved call")

    backend = PyrogramGroupCallBackend(
        Client(),
        resolve_call=lambda chat_id: None,
        media_engine=Engine(),
    )
    with pytest.raises(ConnectionError, match="No active Telegram group call"):
        await backend.connect_call(-100123)


@pytest.mark.asyncio
async def test_backend_rejects_empty_join_payload():
    class Engine:
        async def create_join_payload(self, chat_id, audio_config, video_config):
            return {}

    class Client:
        async def invoke(self, request):
            raise AssertionError("RPC must not be invoked with an empty payload")

    backend = PyrogramGroupCallBackend(
        Client(),
        resolve_call=lambda chat_id: object(),
        media_engine=Engine(),
    )
    with pytest.raises(ConnectionError, match="no valid Telegram group-call join payload"):
        await backend.connect_call(-100123)


@pytest.mark.asyncio
async def test_join_negotiation_failure_closes_engine_and_clears_call(monkeypatch):
    import sys
    import types

    class Request:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DataJSON:
        def __init__(self, data):
            self.data = data

    class InputPeerSelf:
        pass

    pyrogram = types.ModuleType("pyrogram")
    raw = types.ModuleType("pyrogram.raw")
    functions = types.ModuleType("pyrogram.raw.functions")
    phone = types.ModuleType("pyrogram.raw.functions.phone")
    raw_types = types.ModuleType("pyrogram.raw.types")
    phone.JoinGroupCall = Request
    phone.LeaveGroupCall = Request
    phone.GetGroupCall = Request
    raw_types.DataJSON = DataJSON
    raw_types.InputPeerSelf = InputPeerSelf
    monkeypatch.setitem(sys.modules, "pyrogram", pyrogram)
    monkeypatch.setitem(sys.modules, "pyrogram.raw", raw)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions", functions)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions.phone", phone)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.types", raw_types)

    class Engine:
        closed = False

        async def create_join_payload(self, chat_id, audio_config, video_config):
            return {
                "ssrc": 123,
                "ufrag": "ice-user",
                "pwd": "ice-password",
                "fingerprints": [
                    {"hash": "sha-256", "fingerprint": "AA:BB", "setup": "passive"}
                ],
            }

        async def handle_join_updates(self, chat_id, updates):
            raise RuntimeError("bad negotiation update")

        async def close(self, chat_id):
            self.closed = True

    class Client:
        async def invoke(self, request):
            return object()

    engine = Engine()
    backend = PyrogramGroupCallBackend(
        Client(), resolve_call=lambda chat_id: object(), media_engine=engine
    )
    with pytest.raises(RuntimeError, match="bad negotiation update"):
        await backend.connect_call(-100123)
    assert engine.closed is True
    assert -100123 not in backend._calls


@pytest.mark.asyncio
async def test_disconnect_always_closes_engine_after_rpc_error(monkeypatch):
    import sys
    import types

    class Request:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DataJSON:
        def __init__(self, data):
            self.data = data

    class InputPeerSelf:
        pass

    pyrogram = types.ModuleType("pyrogram")
    raw = types.ModuleType("pyrogram.raw")
    functions = types.ModuleType("pyrogram.raw.functions")
    phone = types.ModuleType("pyrogram.raw.functions.phone")
    raw_types = types.ModuleType("pyrogram.raw.types")
    phone.JoinGroupCall = Request
    phone.LeaveGroupCall = Request
    phone.GetGroupCall = Request
    raw_types.DataJSON = DataJSON
    raw_types.InputPeerSelf = InputPeerSelf
    monkeypatch.setitem(sys.modules, "pyrogram", pyrogram)
    monkeypatch.setitem(sys.modules, "pyrogram.raw", raw)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions", functions)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions.phone", phone)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.types", raw_types)

    class Engine:
        closed = False

        async def source_id(self, chat_id):
            return 123

        async def close(self, chat_id):
            self.closed = True

    class Client:
        async def invoke(self, request):
            raise RuntimeError("leave rpc failed")

    engine = Engine()
    backend = PyrogramGroupCallBackend(
        Client(), resolve_call=lambda chat_id: object(), media_engine=engine
    )
    backend._calls[-100123] = object()
    with pytest.raises(RuntimeError, match="leave rpc failed"):
        await backend.disconnect_call(-100123)
    assert engine.closed is True
    assert -100123 not in backend._calls



def test_join_payload_requires_real_transport_parameters():
    valid = {
        "ssrc": 123,
        "ufrag": "ice-user",
        "pwd": "ice-password",
        "fingerprints": [
            {"hash": "sha-256", "fingerprint": "AA:BB", "setup": "passive"}
        ],
    }
    assert _validate_join_payload(valid) is valid


@pytest.mark.parametrize(
    "payload",
    [
        {"ssrc": 0, "ufrag": "u", "pwd": "p", "fingerprints": [{"hash": "sha-256", "fingerprint": "x", "setup": "passive"}]},
        {"ssrc": 123, "ufrag": "", "pwd": "p", "fingerprints": [{"hash": "sha-256", "fingerprint": "x", "setup": "passive"}]},
        {"ssrc": 123, "ufrag": "u", "pwd": "p", "fingerprints": []},
    ],
)
def test_join_payload_rejects_missing_or_placeholder_transport_parameters(payload):
    with pytest.raises(ConnectionError):
        _validate_join_payload(payload)


def test_video_join_payload_requires_source_groups():
    valid_audio = {
        "ssrc": 123,
        "ufrag": "ice-user",
        "pwd": "ice-password",
        "fingerprints": [
            {"hash": "sha-256", "fingerprint": "AA:BB", "setup": "passive"}
        ],
    }
    with pytest.raises(ConnectionError, match="ssrc-groups"):
        _validate_join_payload(valid_audio, video_config={"enabled": True})



@pytest.mark.asyncio
@pytest.mark.parametrize(("recognized", "expected"), [([123], True), ([], False)])
async def test_check_call_reports_server_membership(monkeypatch, recognized, expected):
    import sys
    import types

    class CheckGroupCall:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    pyrogram = types.ModuleType("pyrogram")
    raw = types.ModuleType("pyrogram.raw")
    functions = types.ModuleType("pyrogram.raw.functions")
    phone = types.ModuleType("pyrogram.raw.functions.phone")
    phone.CheckGroupCall = CheckGroupCall
    monkeypatch.setitem(sys.modules, "pyrogram", pyrogram)
    monkeypatch.setitem(sys.modules, "pyrogram.raw", raw)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions", functions)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions.phone", phone)

    class Engine:
        closed = False

        async def source_id(self, chat_id):
            return 123

        async def close(self, chat_id):
            self.closed = True

    class Client:
        async def invoke(self, request):
            assert request.kwargs["sources"] == [123]
            return recognized

    engine = Engine()
    backend = PyrogramGroupCallBackend(
        Client(), resolve_call=lambda chat_id: object(), media_engine=engine
    )
    call = object()
    backend._calls[-100123] = call

    assert await backend.check_call(-100123) is expected
    if expected:
        assert -100123 in backend._calls
        assert engine.closed is False
    else:
        assert -100123 not in backend._calls
        assert engine.closed is True



@pytest.mark.asyncio
async def test_check_call_rpc_error_clears_stale_state(monkeypatch):
    import sys
    import types

    class CheckGroupCall:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    pyrogram = types.ModuleType("pyrogram")
    raw = types.ModuleType("pyrogram.raw")
    functions = types.ModuleType("pyrogram.raw.functions")
    phone = types.ModuleType("pyrogram.raw.functions.phone")
    phone.CheckGroupCall = CheckGroupCall
    monkeypatch.setitem(sys.modules, "pyrogram", pyrogram)
    monkeypatch.setitem(sys.modules, "pyrogram.raw", raw)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions", functions)
    monkeypatch.setitem(sys.modules, "pyrogram.raw.functions.phone", phone)

    class Engine:
        closed = False

        async def source_id(self, chat_id):
            return 123

        async def close(self, chat_id):
            self.closed = True

    class Client:
        async def invoke(self, request):
            raise RuntimeError("GROUPCALL_JOIN_MISSING")

    engine = Engine()
    backend = PyrogramGroupCallBackend(
        Client(), resolve_call=lambda chat_id: object(), media_engine=engine
    )
    backend._calls[-100123] = object()

    assert await backend.check_call(-100123) is False
    assert engine.closed is True
    assert -100123 not in backend._calls

@pytest.mark.asyncio
async def test_disconnect_cleans_engine_when_local_call_state_is_missing():
    class Engine:
        closed = False

        async def close(self, chat_id):
            self.closed = True

    class Client:
        async def invoke(self, request):
            raise AssertionError("No leave RPC should be sent without a stored call")

    engine = Engine()
    backend = PyrogramGroupCallBackend(
        Client(), resolve_call=lambda chat_id: object(), media_engine=engine
    )

    assert await backend.disconnect_call(-100123) is True
    assert engine.closed is True
    assert -100123 not in backend._calls
