""""Typing contract and protocol helpers for Telegram group-call media engines.

This module deliberately does not provide a fake or generic WebRTC engine.
Implementations must speak Telegram's group-call media protocol and own the
lifecycle of their ICE/DTLS/media resources.
"""

import json
from typing import Any, Dict, List, Protocol, runtime_checkable


def extract_group_call_connection_params(
    updates: Any, presentation: bool = False
) -> Dict[str, Any]:
    """Extract the main or presentation connection response from join updates.

    Telegram returns an UpdateGroupCallConnection whose params field contains
    a DataJSON object. Main-call and presentation connections are separate;
    callers must select the matching update explicitly. For WebRTC calls, the
    JSON is the local engine's negotiation response. Stream-mode responses
    (for example {"stream": true}) must not be passed to a WebRTC negotiator.

    Args:
        updates: An Updates object, a sequence of updates, or one update.
        presentation: Select the presentation connection instead of the main
            connection.

    Raises:
        ValueError: If the requested connection update is absent or its JSON
            is malformed.
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
        return parsed

    kind = "presentation" if presentation else "main"
    raise ValueError(
        "Telegram join response contains no UpdateGroupCallConnection "
        f"for the {kind} connection"
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
