"""Audio-only Telegram group-call media engine built on aiortc.

This implementation owns ICE/DTLS/RTP through aiortc and translates Telegram's
join payload/response boundary. It intentionally rejects stream/RTMP mode and
video until those paths have their own protocol implementation and tests.

Passing unit tests is not proof of Telegram interoperability; a live group-call
integration test is still required before this engine can be called production
ready.
"""

import asyncio
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.mediastreams import MediaStreamError, MediaStreamTrack
from av import AudioFrame

from ...exceptions import ConnectionError
from ..media_engine import (
    classify_group_call_connection_params,
    extract_group_call_connection_params,
    extract_webrtc_transport_description,
)

_SAMPLE_RATE = 48_000
_CHANNELS = 2
_BYTES_PER_SAMPLE = 2
_BYTES_PER_PCM_FRAME = _CHANNELS * _BYTES_PER_SAMPLE
_MAX_FRAME_DURATION_SECONDS = 0.12


def _signed_ssrc(value: int) -> int:
    """Represent a 32-bit RTP SSRC as Telegram's signed JSON int32."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("SSRC must be an integer")
    value &= 0xFFFFFFFF
    if value == 0:
        raise ValueError("SSRC must be non-zero")
    return value if value < 0x80000000 else value - 0x100000000


def _sdp_attribute(sdp: str, name: str) -> str:
    match = re.search(rf"(?m)^a={re.escape(name)}:(.+)$", sdp)
    if not match:
        raise ValueError(f"Local aiortc SDP is missing a={name}")
    return match.group(1).strip()


def _local_audio_ssrc(sdp: str) -> int:
    in_audio = False
    for line in sdp.splitlines():
        if line.startswith("m="):
            in_audio = line.startswith("m=audio ")
        if in_audio:
            match = re.match(r"a=ssrc:(\d+)\s", line)
            if match:
                value = int(match.group(1))
                if value:
                    return _signed_ssrc(value)
    raise ValueError("Local aiortc SDP did not declare an audio SSRC")


def _candidate_line(candidate: Dict[str, Any]) -> str:
    """Convert a validated Telegram ICE candidate into an SDP candidate line."""
    fields = [
        str(candidate["foundation"]),
        str(candidate["component"]),
        str(candidate["protocol"]).lower(),
        str(candidate["priority"]),
        str(candidate["ip"]),
        str(candidate["port"]),
        "typ",
        str(candidate["type"]),
    ]
    if candidate.get("rel-addr") is not None:
        fields.extend(("raddr", str(candidate["rel-addr"])))
    if candidate.get("rel-port") is not None:
        fields.extend(("rport", str(candidate["rel-port"])))
    if candidate.get("tcptype") is not None:
        fields.extend(("tcptype", str(candidate["tcptype"])))
    fields.extend(("generation", str(candidate["generation"])))
    return "a=candidate:" + " ".join(fields)


def _build_remote_answer_sdp(local_offer_sdp: str, transport: Dict[str, Any]) -> str:
    """Build an audio-only SDP answer from Telegram's remote transport fields.

    The local offer supplies the negotiated audio codec/m-line. Telegram's
    response supplies remote ICE credentials, DTLS fingerprint/setup and ICE
    candidates. Local SSRC/MSID attributes are not copied into the remote answer.
    """
    fingerprints = transport.get("fingerprints")
    if not isinstance(fingerprints, list) or not fingerprints:
        raise ValueError("Telegram transport has no DTLS fingerprint")
    fingerprint = fingerprints[0]
    if fingerprint.get("hash", "").lower() != "sha-256":
        raise ValueError("aiortc engine currently supports sha-256 DTLS fingerprints only")
    setup = fingerprint.get("setup")
    if setup not in ("active", "passive"):
        raise ValueError("Telegram DTLS setup must be active or passive")

    local_lines = local_offer_sdp.replace("\r\n", "\n").splitlines()
    remote_lines: List[str] = []
    in_audio = False
    saw_audio = False
    saw_mid = False
    direction_written = False

    remove_prefixes = (
        "a=ice-ufrag:", "a=ice-pwd:", "a=fingerprint:", "a=setup:",
        "a=candidate:", "a=end-of-candidates", "a=ssrc:", "a=ssrc-group:",
        "a=msid:",
    )
    directions = {"a=sendrecv", "a=sendonly", "a=recvonly", "a=inactive"}

    for line in local_lines:
        if line.startswith("m="):
            if in_audio:
                break
            in_audio = line.startswith("m=audio ")
            if in_audio:
                saw_audio = True
        # aiortc may place ICE/DTLS attributes at session level. Remove them
        # there too so the remote answer never inherits the local credentials.
        if line.startswith(remove_prefixes):
            continue
        if not in_audio:
            # Audio-only engine: do not carry any non-audio m-lines into answer.
            if line.startswith("m="):
                break
            remote_lines.append(line)
            continue
        if line in directions:
            if not direction_written:
                # SDP answers must complement the offer's media direction.
                answer_direction = {
                    "a=sendrecv": "a=sendrecv",
                    "a=sendonly": "a=recvonly",
                    "a=recvonly": "a=sendonly",
                    "a=inactive": "a=inactive",
                }[line]
                remote_lines.append(answer_direction)
                direction_written = True
            continue
        remote_lines.append(line)
        if line.startswith("a=mid:"):
            saw_mid = True

    if not saw_audio or not saw_mid:
        raise ValueError("Local aiortc offer has no usable audio media section")
    if not direction_written:
        remote_lines.append("a=sendrecv")

    remote_lines.extend([
        "a=ice-ufrag:" + transport["ufrag"],
        "a=ice-pwd:" + transport["pwd"],
        "a=fingerprint:" + fingerprint["hash"].lower() + " " + fingerprint["fingerprint"],
        "a=setup:" + setup,
    ])
    for candidate in transport["candidates"]:
        remote_lines.append(_candidate_line(candidate))
    remote_lines.append("a=end-of-candidates")
    return "\r\n".join(remote_lines) + "\r\n"


class _PCMTrack(MediaStreamTrack):
    """Paced 48 kHz stereo s16le source track; aiortc encodes it to negotiated RTP."""

    kind = "audio"

    def __init__(self, queue_size: int = 10):
        super().__init__()
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self._pts = 0
        self._next_due: Optional[float] = None

    async def push(self, data: bytes) -> None:
        if not isinstance(data, bytes) or not data:
            raise TypeError("audio frame must be non-empty bytes")
        if len(data) % _BYTES_PER_PCM_FRAME:
            raise ValueError("PCM data must align to stereo s16le sample frames")
        samples = len(data) // _BYTES_PER_PCM_FRAME
        if samples / _SAMPLE_RATE > _MAX_FRAME_DURATION_SECONDS:
            raise ValueError("PCM frame duration must not exceed 120 ms")
        await self.queue.put(data)

    def clear(self) -> None:
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break

    async def recv(self) -> AudioFrame:
        if self.readyState != "live":
            raise MediaStreamError
        try:
            data = await asyncio.wait_for(self.queue.get(), timeout=0.02)
            self.queue.task_done()
        except asyncio.TimeoutError:
            data = b"\x00" * (_BYTES_PER_PCM_FRAME * 960)

        samples = len(data) // _BYTES_PER_PCM_FRAME
        duration = samples / _SAMPLE_RATE
        loop = asyncio.get_running_loop()
        now = loop.time()
        if self._next_due is None or self._next_due < now - duration:
            self._next_due = now
        else:
            delay = self._next_due - now
            if delay > 0:
                await asyncio.sleep(delay)
        self._next_due += duration

        frame = AudioFrame(format="s16", layout="stereo", samples=samples)
        frame.planes[0].update(data)
        frame.sample_rate = _SAMPLE_RATE
        frame.pts = self._pts
        frame.time_base = Fraction(1, _SAMPLE_RATE)
        self._pts += samples
        return frame


@dataclass
class _Session:
    pc: RTCPeerConnection
    track: _PCMTrack
    source_id: int
    local_offer_sdp: str
    connected_event: asyncio.Event
    state: str = "preparing"


class AiortcTelegramMediaEngine:
    """Concrete audio-only engine for Telegram's WebRTC group-call mode.

    This is an initial implementation boundary. Telegram compatibility must be
    validated in a real test call; the engine deliberately fails closed on
    stream/RTMP responses and unsupported SDP/DTLS shapes.
    """

    def __init__(self, connect_timeout: float = 20.0, queue_size: int = 10):
        if connect_timeout <= 0:
            raise ValueError("connect_timeout must be positive")
        if queue_size < 1:
            raise ValueError("queue_size must be at least 1")
        self.connect_timeout = float(connect_timeout)
        self.queue_size = int(queue_size)
        self._sessions: Dict[int, _Session] = {}

    async def create_join_payload(
        self, chat_id: int, audio_config: Any = None, video_config: Any = None
    ) -> Dict[str, Any]:
        if video_config is not None:
            raise NotImplementedError("Telegram video publishing is not implemented yet")
        await self.close(chat_id)
        pc = RTCPeerConnection()
        track = _PCMTrack(queue_size=self.queue_size)
        pc.addTrack(track)
        connected_event = asyncio.Event()

        @pc.on("connectionstatechange")
        def on_connection_state_change() -> None:
            if pc.connectionState in ("connected", "failed", "closed"):
                connected_event.set()

        try:
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)
            local_sdp = pc.localDescription.sdp
            ufrag = _sdp_attribute(local_sdp, "ice-ufrag")
            pwd = _sdp_attribute(local_sdp, "ice-pwd")
            fingerprint_line = _sdp_attribute(local_sdp, "fingerprint")
            fingerprint_hash, fingerprint_value = fingerprint_line.split(" ", 1)
            source_id = _local_audio_ssrc(local_sdp)
            self._sessions[chat_id] = _Session(
                pc=pc,
                track=track,
                source_id=source_id,
                local_offer_sdp=local_sdp,
                connected_event=connected_event,
            )
            return {
                "ssrc": source_id,
                "ufrag": ufrag,
                "pwd": pwd,
                "fingerprints": [{
                    "hash": fingerprint_hash.lower(),
                    "fingerprint": fingerprint_value,
                    "setup": "passive",
                }],
            }
        except BaseException:
            track.stop()
            await pc.close()
            raise

    async def handle_join_updates(self, chat_id: int, updates: Any) -> None:
        session = self._sessions.get(chat_id)
        if session is None:
            raise ConnectionError("No prepared aiortc session exists for this chat")
        session.state = "negotiating"
        try:
            params = extract_group_call_connection_params(updates)
            mode = classify_group_call_connection_params(params)
            if mode != "webrtc":
                raise ConnectionError(
                    f"Telegram returned {mode} mode; this engine currently supports WebRTC only"
                )
            transport = extract_webrtc_transport_description(params)
            remote_sdp = _build_remote_answer_sdp(session.local_offer_sdp, transport)
            await session.pc.setRemoteDescription(
                RTCSessionDescription(sdp=remote_sdp, type="answer")
            )
            if session.pc.connectionState != "connected":
                await asyncio.wait_for(
                    session.connected_event.wait(), timeout=self.connect_timeout
                )
            if session.pc.connectionState != "connected":
                raise ConnectionError(
                    "aiortc ICE/DTLS transport did not reach connected state "
                    f"(state={session.pc.connectionState})"
                )
            session.state = "connected"
        except BaseException:
            session.state = "failed"
            await self.close(chat_id)
            raise

    async def is_connected(self, chat_id: int) -> bool:
        session = self._sessions.get(chat_id)
        return bool(session and session.pc.connectionState == "connected")

    async def source_id(self, chat_id: int) -> int:
        session = self._sessions.get(chat_id)
        if session is None:
            raise ConnectionError(f"No media session exists for chat {chat_id}")
        return session.source_id

    async def close(self, chat_id: int) -> None:
        session = self._sessions.pop(chat_id, None)
        if session is None:
            return
        session.state = "closing"
        session.track.stop()
        session.track.clear()
        try:
            await session.pc.close()
        finally:
            session.state = "closed"

    async def play_stream(self, chat_id: int, stream: Any) -> bool:
        if isinstance(stream, bytes):
            return await self.send_frame(chat_id, stream, "audio")
        if not hasattr(stream, "__aiter__"):
            raise TypeError("stream must be PCM bytes or an async iterable of PCM byte frames")
        sent_any = False
        async for chunk in stream:
            await self.send_frame(chat_id, chunk, "audio")
            sent_any = True
        return sent_any

    async def stop_stream(self, chat_id: int) -> bool:
        session = self._sessions.get(chat_id)
        if session is None:
            return False
        session.track.clear()
        return True

    async def send_frame(self, chat_id: int, frame_data: Any, frame_type: str) -> bool:
        session = self._sessions.get(chat_id)
        if session is None or session.pc.connectionState != "connected":
            raise ConnectionError(f"No connected Telegram media session for chat {chat_id}")
        if frame_type != "audio":
            raise NotImplementedError("This media engine currently supports audio frames only")
        await session.track.push(frame_data)
        return True

    async def get_participants(self, chat_id: int, call_info: Any) -> List[Any]:
        if chat_id not in self._sessions:
            raise ConnectionError(f"No media session exists for chat {chat_id}")
        participants = getattr(call_info, "participants", None)
        return list(participants) if participants is not None else []
