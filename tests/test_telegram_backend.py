"""Tests for the independent Pyrogram signaling adapter boundary."""

import pytest

from tgcaller.exceptions import ConnectionError
from tgcaller.mtproto import PyrogramGroupCallBackend


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
