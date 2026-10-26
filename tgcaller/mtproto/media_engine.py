"""Telegram group-call media-engine contract and connection-update helpers.

This module deliberately does not provide a fake or generic WebRTC engine.
Implementations must speak Telegram's group-call media protocol and own the
lifecycle of their ICE/DTLS/media resources.
"""

import json
from typing import Any, Dict, List, Protocol, runtime_checkable


def classify_group_call_connection_params(params: Any) -> str:
    """Classify Telegram connection parameters as WebRTC, stream, or RTMP.

    Telegram's stream-mode responses are not WebRTC negotiation documents and
    must be dispatched to a compatible streaming implementation.
    """
    if not isinstance(params, dict):
        raise ValueError("Telegram connection params must be a JSON object")

    stream = params.get("stream", False)
    rtmp = params.get("rtmp", False)
    if not isinstance(stream, bool) or not isinstance(rtmp, bool):
        raise ValueError("stream and rtmp mode flags must be booleans")
    if rtmp and not stream:
        raise ValueError("rtmp mode requires stream mode")

    if stream and rtmp:
        return "rtmp"
    if stream:
        return "stream"
    return "webrtc"


def extract_group_call_connection_params(
    updates: Any, presentation: bool = False
) -> Dict[str, Any]:
    """Extract a Telegram UpdateGroupCallConnection's DataJSON parameters.

    When Telegram returns both the main and presentation connection updates,
    select the requested connection. The parsed object is classified separately
    so stream-mode responses are never accidentally sent to a WebRTC negotiator.

    Raises:
        ValueError: If the requested update is absent or its JSON is malformed.
    """
    items = getattr(updates, "updates", None)
    if items is None:
        items = updates if isinstance(updates, (list, tuple)) else (updates,)

    for update in items:
        if type(update).__name__ != "UpdateGroupCallConnection":
            continue
        if bool(getattr(update, "presentation", False)) != presentation:
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
        classify_group_call_connection_params(parsed)
        return parsed

    if presentation:
        raise ValueError(
            "Telegram join response has no UpdateGroupCallConnection for the presentation connection"
        )
    raise ValueError(
        "Telegram join response contains no UpdateGroupCallConnection"
    )


@runtime_checkable
class TelegramMediaEngine(Protocol):
    """Required interface for a Telegram-compatible media runtime.

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
