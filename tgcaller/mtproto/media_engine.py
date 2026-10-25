"""Typing contract for a Telegram-compatible group-call media engine.

This protocol deliberately does not provide a fake or generic WebRTC engine.
Implementations must speak Telegram's group-call media protocol and own the
lifecycle of their ICE/DTLS/media resources.
"""
from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class TelegramMediaEngine(Protocol):
    """Required interface for the MTProto signaling adapter's media runtime.

    A conforming implementation must create real Telegram-compatible join
    parameters, consume server negotiation updates, and only report connected
    after its media transport is established. ``source_id`` must return the
    non-zero SSRC registered by the active main connection.
    """

    async def create_join_payload(
        self, chat_id: int, audio_config: Any = None, video_config: Any = None
    ) -> Dict[str, Any]: ...

    async def handle_join_updates(self, chat_id: int, updates: Any) -> None: ...

    async def is_connected(self, chat_id: int) -> bool: ...

    async def source_id(self, chat_id: int) -> int: ...

    async def close(self, chat_id: int) -> None: ...

    async def play_stream(self, chat_id: int, stream: Any) -> bool: ...

    async def stop_stream(self, chat_id: int) -> bool: ...

    async def send_frame(
        self, chat_id: int, frame_data: Any, frame_type: str
    ) -> bool: ...

    async def get_participants(self, chat_id: int, call_info: Any) -> List[Any]: ...
