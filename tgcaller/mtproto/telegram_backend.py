"""Independent Pyrogram MTProto signaling adapter.

This adapter requires a separately implemented Telegram-compatible media engine.
It does not generate fake WebRTC parameters and cannot work with a generic
aiortc peer connection unless that engine implements Telegram group-call negotiation.
"""
import inspect
import json
from typing import Any, Callable, Dict

from ..exceptions import ConnectionError
from .media_engine import TelegramMediaEngine


async def _resolve(value):
    return await value if inspect.isawaitable(value) else value


def _validate_join_payload(payload, video_config=None):
    """Reject incomplete or placeholder Telegram group-call negotiation data."""
    if not isinstance(payload, dict) or not payload:
        raise ConnectionError(
            "Media engine returned no valid Telegram group-call join payload"
        )

    ssrc = payload.get("ssrc")
    if isinstance(ssrc, bool) or not isinstance(ssrc, int) or ssrc <= 0:
        raise ConnectionError("Join payload must contain a non-zero integer audio ssrc")

    for key in ("ufrag", "pwd"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ConnectionError(f"Join payload must contain a non-empty {key}")

    fingerprints = payload.get("fingerprints")
    if not isinstance(fingerprints, list) or not fingerprints:
        raise ConnectionError("Join payload must contain at least one DTLS fingerprint")
    for item in fingerprints:
        if not isinstance(item, dict) or not all(
            isinstance(item.get(key), str) and item[key].strip()
            for key in ("hash", "fingerprint", "setup")
        ):
            raise ConnectionError(
                "Each DTLS fingerprint must include hash, fingerprint, and setup"
            )

    if video_config is not None:
        groups = payload.get("ssrc-groups")
        if not isinstance(groups, list) or not groups:
            raise ConnectionError(
                "Video join payload must contain non-empty ssrc-groups"
            )
    return payload


class PyrogramGroupCallBackend:
    """Bridge TgCaller transport calls to Pyrogram raw group-call RPCs.

    resolve_call maps chat_id to a Pyrogram InputGroupCall raw TL object.
    media_engine must implement create_join_payload, handle_join_updates,
    is_connected, source_id, close, play_stream, stop_stream, send_frame,
    and get_participants. It must implement Telegram's real call protocol.
    """

    def __init__(
        self, client: Any, resolve_call: Callable, media_engine: TelegramMediaEngine
    ):
        if client is None:
            raise TypeError("client is required")
        if not callable(resolve_call):
            raise TypeError("resolve_call must be callable")
        if media_engine is None:
            raise TypeError(
                "media_engine is required; join payloads must come from a "
                "real Telegram-compatible media engine"
            )
        self.client = client
        self.resolve_call = resolve_call
        self.media_engine = media_engine
        self._calls: Dict[int, Any] = {}

    async def _rpc_types(self):
        try:
            from pyrogram.raw.functions.phone import JoinGroupCall, LeaveGroupCall, GetGroupCall
            from pyrogram.raw.types import DataJSON, InputPeerSelf
        except ImportError as exc:
            raise ConnectionError(
                "This Pyrogram version does not expose required raw group-call APIs"
            ) from exc
        return JoinGroupCall, LeaveGroupCall, GetGroupCall, DataJSON, InputPeerSelf

    async def connect_call(self, chat_id, audio_config=None, video_config=None):
        if chat_id in self._calls and await self.is_healthy(chat_id):
            return True

        JoinGroupCall, _, _, DataJSON, InputPeerSelf = await self._rpc_types()
        call = await _resolve(self.resolve_call(chat_id))
        if call is None:
            raise ConnectionError(
                f"No active Telegram group call could be resolved for chat {chat_id}"
            )

        # Payload creation may allocate ICE/DTLS resources before it returns.
        # Keep it inside the cleanup boundary so invalid data or engine errors
        # cannot leak partially initialized media resources.
        joined_on_server = False
        try:
            payload = await _resolve(
                self.media_engine.create_join_payload(chat_id, audio_config, video_config)
            )
            _validate_join_payload(payload, video_config)
            updates = await self.client.invoke(
                JoinGroupCall(
                    call=call,
                    join_as=InputPeerSelf(),
                    params=DataJSON(data=json.dumps(payload, separators=(",", ":"))),
                    muted=bool(audio_config is None),
                    video_stopped=bool(video_config is None),
                )
            )
            joined_on_server = True
            await _resolve(self.media_engine.handle_join_updates(chat_id, updates))
            self._calls[chat_id] = call

            if not await self.is_healthy(chat_id):
                raise ConnectionError(
                    "Telegram accepted the join request, but the media engine "
                    "did not establish a healthy call connection"
                )
            return True
        except Exception:
            self._calls.pop(chat_id, None)
            # If Telegram accepted the join but local negotiation/health checks
            # failed, compensate with a leave RPC before tearing down the engine.
            # Cleanup failures must never hide the original connection error.
            if joined_on_server:
                try:
                    _, LeaveGroupCall, _, _, _ = await self._rpc_types()
                    source_id = await _resolve(self.media_engine.source_id(chat_id))
                    await self.client.invoke(LeaveGroupCall(call=call, source=source_id))
                except Exception:
                    pass
            # Failed payload creation, validation, signaling or negotiation must
            # not leak ICE/DTLS/media resources.
            try:
                await _resolve(self.media_engine.close(chat_id))
            except Exception:
                pass
            raise

    async def disconnect_call(self, chat_id):
        call = self._calls.get(chat_id)
        if call is None:
            # Local call state can be missing after a partial failure while the
            # engine still owns ICE/DTLS resources. Cleanup must remain idempotent.
            await _resolve(self.media_engine.close(chat_id))
            return True
        try:
            _, LeaveGroupCall, _, _, _ = await self._rpc_types()
            source_id = await _resolve(self.media_engine.source_id(chat_id))
            await self.client.invoke(LeaveGroupCall(call=call, source=source_id))
        except BaseException:
            # Preserve the original RPC/cancellation error if cleanup also fails.
            self._calls.pop(chat_id, None)
            try:
                await _resolve(self.media_engine.close(chat_id))
            except BaseException:
                pass
            raise
        else:
            # State must be cleared before shutdown, even when shutdown fails.
            self._calls.pop(chat_id, None)
            await _resolve(self.media_engine.close(chat_id))
            return True

    async def is_healthy(self, chat_id):
        return bool(await _resolve(self.media_engine.is_connected(chat_id)))

    async def check_call(self, chat_id):
        """Check whether Telegram still recognizes this call's media source.

        This is a server-side membership check, not a media-flow health check.
        Call it while the media engine is reconnecting; if the source is absent,
        the caller must rebuild the media connection and join payload.
        """
        call = self._calls.get(chat_id)
        if call is None:
            return False
        try:
            from pyrogram.raw.functions.phone import CheckGroupCall
        except ImportError as exc:
            raise ConnectionError(
                "This Pyrogram version does not expose phone.CheckGroupCall"
            ) from exc

        source_id = await _resolve(self.media_engine.source_id(chat_id))
        if isinstance(source_id, bool) or not isinstance(source_id, int) or source_id <= 0:
            raise ConnectionError("Media engine must provide a non-zero integer source ID")
        try:
            recognized = await self.client.invoke(
                CheckGroupCall(call=call, sources=[source_id])
            )
        except Exception:
            # Telegram instructs clients to rejoin when this check errors.
            # Clear state before cleanup so a shutdown error cannot leave a
            # stale call that connect_call() mistakes for an active session.
            self._calls.pop(chat_id, None)
            try:
                await _resolve(self.media_engine.close(chat_id))
            except Exception:
                pass
            return False

        if source_id in recognized:
            return True

        # The server no longer recognizes this source. Drop stale local state so
        # connect_call() can generate a fresh payload and perform a real rejoin.
        self._calls.pop(chat_id, None)
        try:
            await _resolve(self.media_engine.close(chat_id))
        except Exception:
            pass
        return False

    async def get_participants(self, chat_id):
        call = self._calls.get(chat_id)
        if call is None:
            raise ConnectionError(f"Not connected to Telegram call in chat {chat_id}")
        _, _, GetGroupCall, _, _ = await self._rpc_types()
        call_info = await self.client.invoke(GetGroupCall(call=call, limit=100))
        return await _resolve(self.media_engine.get_participants(chat_id, call_info))

    async def play_stream(self, chat_id, stream):
        if chat_id not in self._calls:
            raise ConnectionError(f"Not connected to Telegram call in chat {chat_id}")
        return bool(await _resolve(self.media_engine.play_stream(chat_id, stream)))

    async def stop_stream(self, chat_id):
        if chat_id not in self._calls:
            return False
        return bool(await _resolve(self.media_engine.stop_stream(chat_id)))

    async def send_frame(self, chat_id, frame_data, frame_type):
        if chat_id not in self._calls:
            raise ConnectionError(f"Not connected to Telegram call in chat {chat_id}")
        return bool(await _resolve(self.media_engine.send_frame(chat_id, frame_data, frame_type)))

async def resolve_active_group_call(client: Any, chat_id: int):
    """Resolve a chat's active Telegram group call to an InputGroupCall object.

    Supports basic groups and channels/supergroups using Pyrogram's raw API.
    The returned object is suitable for the backend resolve_call callback.
    It does not create a call or establish media.
    """
    try:
        from pyrogram.raw.functions.channels import GetFullChannel
        from pyrogram.raw.functions.messages import GetFullChat
        from pyrogram.raw.types import InputChannel, InputPeerChannel, InputPeerChat
    except ImportError as exc:
        raise ConnectionError(
            "This Pyrogram version does not expose raw full-chat group-call APIs"
        ) from exc

    try:
        peer = await client.resolve_peer(chat_id)
    except Exception as exc:
        raise ConnectionError(
            f"Could not resolve Telegram chat peer for {chat_id}"
        ) from exc

    try:
        if isinstance(peer, InputPeerChannel):
            response = await client.invoke(
                GetFullChannel(
                    channel=InputChannel(
                        channel_id=peer.channel_id,
                        access_hash=peer.access_hash,
                    )
                )
            )
        elif isinstance(peer, InputPeerChat):
            response = await client.invoke(GetFullChat(chat_id=peer.chat_id))
        else:
            raise ConnectionError(
                f"Chat {chat_id} is not a basic group, supergroup, or channel"
            )
    except ConnectionError:
        raise
    except Exception as exc:
        raise ConnectionError(
            f"Could not fetch full Telegram chat information for {chat_id}"
        ) from exc

    full_chat = getattr(response, "full_chat", None)
    call = getattr(full_chat, "call", None)
    if call is None:
        raise ConnectionError(
            f"No active Telegram group call is available for chat {chat_id}"
        )
    return call
