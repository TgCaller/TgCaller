"""Typing contract and protocol helpers for Telegram group-call media engines.

This module deliberately does not provide a fake or generic WebRTC engine.
Implementations must speak Telegram's group-call media protocol and own the
lifecycle of their ICE/DTLS/media resources.
"""

import json
from typing import Any, Dict, List, Protocol, runtime_checkable


def extract_group_call_connection_params(updates: Any) -> Dict[str, Any]:
    """Extract Telegram's local-engine response from join RPC updates.

    Telegram returns an UpdateGroupCallConnection whose params field contains
    a DataJSON object. For WebRTC calls, its JSON is the local engine's
    negotiation response. {"stream": true} and {"stream": true, "rtmp": true}
    are distinct stream-mode responses; callers must not pass either to a
    WebRTC negotiator.

    Raises:
        ValueError: If the update collection has no usable connection update
            or the returned JSON is malformed.
    """
    items = getattr(updates, "updates", None)
    if items is None:
        items = updates if isinstance(updates, (list, tuple)) else (updates,)

    for update in items:
        if type(update).__name__ != "UpdateGroupCallConnection":
            continue
        params = getattr(update, "params", None)
        data = getattr(params, "data", None)
        if not isinstance(data, str) or not data.strip():
            raise ValueError(
                "Telegram group-call connection update has no JSON params"
            )
        try:
            parsed = json.loads(data)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Telegram group-call connection params are not valid JSON"
            ) from exc
        if not isinstance(parsed, dict):
            raise ValueError(
                "Telegram group-call connection params must be a JSON object"
            )
        return parsed

    raise ValueError(
        "Telegram join response contains no UpdateGroupCallConnection"
    )


@runtime_checkable
class TelegramMediaEngine(Protocol):
    """Required interface for the MTProto signaling adapter's media runtime.

    A conforming implementation must create real Telegram-compatible join
    parameters, consume server negotiation updates, and only report connected
    after its media transport is established. source_id must return the
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
