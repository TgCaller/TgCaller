"""Typing contract and protocol helpers for Telegram group-call media engines.

This module deliberately does not provide a fake or generic WebRTC engine.
Implementations must speak Telegram's group-call media protocol and own the
lifecycle of their ICE/DTLS/media resources.
"""

import json
from typing import Any, Dict, List, Protocol, runtime_checkable


def extract_group_call_connection_params(
    updates: Any, presentation: bool = False
) -> Dict[str, Any]:
    """Extract the main or presentation connection parameters from join updates.

    Telegram returns an UpdateGroupCallConnection whose params field contains
    a DataJSON object. The update's presentation flag distinguishes the main
    connection from the separate screen-sharing connection. Stream and RTMP
    responses are preserved for the engine to dispatch to the right transport.

    Raises:
        ValueError: If the requested update is absent or its JSON is invalid.
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
            "Telegram join response contains no UpdateGroupCallConnection "
            "for the presentation connection"
        )
    raise ValueError(
        "Telegram join response contains no UpdateGroupCallConnection"
    )


def classify_group_call_connection_params(params: Any) -> str:
    """Classify Telegram connection params as WebRTC, stream, or RTMP.

    Telegram's stream mode is not a WebRTC negotiation response. Invalid or
    contradictory mode flags are rejected rather than passed to a peer
    connection and misreported as a successful join.
    """
    if not isinstance(params, dict):
        raise ValueError("Telegram connection params must be a JSON object")

    stream = params.get("stream", False)
    rtmp = params.get("rtmp", False)
    if not isinstance(stream, bool):
        raise ValueError("Telegram connection 'stream' flag must be a boolean")
    if not isinstance(rtmp, bool):
        raise ValueError("Telegram connection 'rtmp' flag must be a boolean")
    if rtmp and not stream:
        raise ValueError(
            "Telegram connection 'rtmp' flag requires stream mode"
        )
    if stream:
        return "rtmp" if rtmp else "stream"
    return "webrtc"


def extract_webrtc_transport_description(params: Any) -> Dict[str, Any]:
    """Validate and return the server's WebRTC transport description.

    Telegram's UpdateGroupCallConnection response wraps remote ICE/DTLS
    details under a transport object. This differs from the local join payload,
    which contains top-level ufrag, pwd and fingerprints fields. Stream/RTMP
    responses must be dispatched to their own playback path.
    """
    if classify_group_call_connection_params(params) != "webrtc":
        raise ValueError(
            "Telegram connection is in stream/RTMP mode, not WebRTC mode"
        )

    transport = params.get("transport")
    if not isinstance(transport, dict):
        raise ValueError(
            "Telegram WebRTC response must contain a transport object"
        )

    for key in ("ufrag", "pwd"):
        if not isinstance(transport.get(key), str) or not transport[key].strip():
            raise ValueError(
                f"Telegram WebRTC transport must contain non-empty {key}"
            )

    fingerprints = transport.get("fingerprints")
    if not isinstance(fingerprints, list) or not fingerprints:
        raise ValueError(
            "Telegram WebRTC transport must contain at least one fingerprint"
        )
    clean_fingerprints = []
    for index, item in enumerate(fingerprints):
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), str) and item[key].strip()
            for key in ("hash", "fingerprint", "setup")
        ):
            raise ValueError(
                f"Telegram WebRTC fingerprint at index {index} is invalid"
            )
        clean_fingerprints.append(
            {key: item[key] for key in ("hash", "fingerprint", "setup")}
        )

    candidates = transport.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError(
            "Telegram WebRTC transport must contain a candidates list"
        )
    # This engine does not implement trickle-ICE updates after the join RPC.
    # An empty list would therefore create an SDP answer that cannot establish
    # connectivity; reject it immediately instead of timing out as if connected.
    if not candidates:
        raise ValueError(
            "Telegram WebRTC transport must contain at least one ICE candidate"
        )
    candidate_fields = (
        "port", "protocol", "network", "generation", "id", "component",
        "foundation", "priority", "ip", "type",
    )
    optional_candidate_fields = ("tcptype", "rel-addr", "rel-port")
    clean_candidates = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict) or not all(
            isinstance(candidate.get(key), str) and candidate[key].strip()
            for key in candidate_fields
        ):
            raise ValueError(
                f"Telegram ICE candidate at index {index} is invalid"
            )
        clean_candidate = {key: candidate[key] for key in candidate_fields}
        for key in optional_candidate_fields:
            value = candidate.get(key)
            if value is not None:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"Telegram ICE candidate field {key} at index {index} is invalid"
                    )
                clean_candidate[key] = value
        clean_candidates.append(clean_candidate)

    return {
        "ufrag": transport["ufrag"],
        "pwd": transport["pwd"],
        "fingerprints": clean_fingerprints,
        "candidates": clean_candidates,
    }


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
