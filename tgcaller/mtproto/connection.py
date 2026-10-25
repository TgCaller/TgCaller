"""Transport boundary for TgCaller call connections.

A concrete backend must implement Telegram group-call signaling and media transport.
This class fails closed when no backend is configured instead of simulating success.
"""
import inspect
from typing import Any, Optional

from ..exceptions import ConnectionError


class Connection:
    """Delegate call lifecycle and media operations to a concrete backend."""

    def __init__(self, client: Any, backend: Optional[Any] = None):
        self.client = client
        self.backend = backend

    async def _invoke(self, name: str, *args):
        if self.backend is None:
            raise ConnectionError(
                "No real Telegram group-call transport is configured. "
                "TgCaller will not simulate a successful call."
            )
        method = getattr(self.backend, name, None)
        if method is None or not callable(method):
            raise ConnectionError(
                f"Configured call transport does not implement required method {name}()."
            )
        result = method(*args)
        return await result if inspect.isawaitable(result) else result

    async def connect_call(self, chat_id: int, audio_config=None, video_config=None) -> bool:
        return bool(await self._invoke("connect_call", chat_id, audio_config, video_config))

    async def disconnect_call(self, chat_id: int) -> bool:
        if self.backend is None:
            return False
        method = getattr(self.backend, "disconnect_call", None)
        if method is None:
            return False
        result = method(chat_id)
        return bool(await result if inspect.isawaitable(result) else result)

    async def is_healthy(self, chat_id: int) -> bool:
        return bool(await self._invoke("is_healthy", chat_id))

    async def get_participants(self, chat_id: int):
        return await self._invoke("get_participants", chat_id)

    async def play_stream(self, chat_id: int, stream):
        return bool(await self._invoke("play_stream", chat_id, stream))

    async def stop_stream(self, chat_id: int) -> bool:
        if self.backend is None:
            return False
        method = getattr(self.backend, "stop_stream", None)
        if method is None:
            return False
        result = method(chat_id)
        return bool(await result if inspect.isawaitable(result) else result)

    async def send_frame(self, chat_id: int, frame_data: bytes, frame_type: str = "audio") -> bool:
        return bool(await self._invoke("send_frame", chat_id, frame_data, frame_type))
