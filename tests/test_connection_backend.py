"""Tests for the real-transport boundary used by TgCaller."""

import pytest

from tgcaller.exceptions import ConnectionError
from tgcaller.mtproto import Connection


class AsyncBackend:
    async def connect_call(self, chat_id, audio_config, video_config):
        return chat_id == -100123

    async def disconnect_call(self, chat_id):
        return True

    async def is_healthy(self, chat_id):
        return True

    async def get_participants(self, chat_id):
        return [{"chat_id": chat_id}]

    async def play_stream(self, chat_id, stream):
        return stream == "track.mp3"

    async def stop_stream(self, chat_id):
        return True

    async def send_frame(self, chat_id, frame_data, frame_type):
        return bool(frame_data) and frame_type in {"audio", "video"}


@pytest.mark.asyncio
async def test_connection_fails_closed_without_backend():
    connection = Connection(client=object())

    with pytest.raises(ConnectionError, match="No real Telegram group-call transport"):
        await connection.connect_call(-100123)

    with pytest.raises(ConnectionError, match="No real Telegram group-call transport"):
        await connection.is_healthy(-100123)


@pytest.mark.asyncio
async def test_connection_delegates_to_backend():
    connection = Connection(client=object(), backend=AsyncBackend())

    assert await connection.connect_call(-100123) is True
    assert await connection.disconnect_call(-100123) is True
    assert await connection.is_healthy(-100123) is True
    assert await connection.get_participants(-100123) == [{"chat_id": -100123}]
    assert await connection.play_stream(-100123, "track.mp3") is True
    assert await connection.stop_stream(-100123) is True
    assert await connection.send_frame(-100123, b"frame", "video") is True


@pytest.mark.asyncio
async def test_connection_rejects_incomplete_backend():
    class IncompleteBackend:
        async def connect_call(self, chat_id, audio_config, video_config):
            return True

    connection = Connection(client=object(), backend=IncompleteBackend())

    with pytest.raises(ConnectionError, match="does not implement required method is_healthy"):
        await connection.is_healthy(-100123)
