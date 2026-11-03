import asyncio
from types import SimpleNamespace

import pytest

from tgcaller.exceptions import ConnectionError
from tgcaller.mtproto.engine.aiortc_engine import (
    AiortcTelegramMediaEngine,
    _PCMTrack,
    _build_remote_answer_sdp,
    _candidate_line,
    _signed_ssrc,
)


def _valid_transport():
    return {
        "ufrag": "remote-ufrag",
        "pwd": "remote-password",
        "fingerprints": [
            {
                "hash": "sha-256",
                "fingerprint": "AA:BB:CC",
                "setup": "active",
            }
        ],
        "candidates": [
            {
                "port": "3478",
                "protocol": "udp",
                "network": "1",
                "generation": "0",
                "id": "candidate-1",
                "component": "1",
                "foundation": "foundation-1",
                "priority": "12345",
                "ip": "192.0.2.10",
                "type": "relay",
                "rel-addr": "10.0.0.1",
                "rel-port": "5000",
            }
        ],
    }


def _local_offer():
    return "\r\n".join(
        [
            "v=0",
            "o=- 1 1 IN IP4 0.0.0.0",
            "s=-",
            "t=0 0",
            "a=group:BUNDLE 0",
            "a=msid-semantic:WMS *",
            "m=audio 9 UDP/TLS/RTP/SAVPF 96",
            "c=IN IP4 0.0.0.0",
            "a=sendrecv",
            "a=mid:0",
            "a=ice-ufrag:local-ufrag",
            "a=ice-pwd:local-password",
            "a=fingerprint:sha-256 11:22:33",
            "a=setup:actpass",
            "a=rtcp-mux",
            "a=rtpmap:96 opus/48000/2",
            "a=ssrc:123 cname:local-track",
            "a=ssrc:123 msid:stream track",
            "",
        ]
    )


def test_signed_ssrc_preserves_32_bit_wire_value():
    assert _signed_ssrc(1) == 1
    assert _signed_ssrc(0xFFFFFFFF) == -1
    assert _signed_ssrc(0x80000000) == -(2**31)
    with pytest.raises(ValueError):
        _signed_ssrc(0)
    with pytest.raises(ValueError):
        _signed_ssrc(True)


def test_candidate_conversion_keeps_relay_information():
    line = _candidate_line(_valid_transport()["candidates"][0])

    assert line.startswith("a=candidate:foundation-1 1 udp 12345 192.0.2.10 3478 typ relay")
    assert "raddr 10.0.0.1 rport 5000" in line
    assert line.endswith("generation 0")


def test_remote_answer_uses_telegram_transport_and_drops_local_ssrc():
    sdp = _build_remote_answer_sdp(_local_offer(), _valid_transport())

    assert "a=ice-ufrag:remote-ufrag" in sdp
    assert "a=ice-pwd:remote-password" in sdp
    assert "a=fingerprint:sha-256 AA:BB:CC" in sdp
    assert "a=setup:active" in sdp
    assert "a=rtpmap:96 opus/48000/2" in sdp
    assert "a=candidate:foundation-1 1 udp 12345 192.0.2.10 3478 typ relay" in sdp
    assert "a=ssrc:" not in sdp
    assert "a=setup:actpass" not in sdp


def test_remote_answer_complements_offer_media_direction():
    local_offer = _local_offer().replace("a=sendrecv", "a=recvonly")

    sdp = _build_remote_answer_sdp(local_offer, _valid_transport())

    assert "a=sendonly" in sdp
    assert "a=recvonly" not in sdp


def test_remote_answer_rejects_unsupported_dtls_setup():
    transport = _valid_transport()
    transport["fingerprints"][0]["setup"] = "actpass"

    with pytest.raises(ValueError, match="setup must be active or passive"):
        _build_remote_answer_sdp(_local_offer(), transport)


@pytest.mark.asyncio
async def test_pcm_track_turns_stereo_s16le_into_an_audio_frame():
    track = _PCMTrack()
    await track.push(b"\x01\x00\x02\x00" * 960)

    frame = await track.recv()

    assert frame.samples == 960
    assert frame.sample_rate == 48_000
    assert frame.pts == 0
    assert frame.time_base.numerator == 1
    assert frame.time_base.denominator == 48_000
    track.stop()


@pytest.mark.asyncio
async def test_pcm_track_rejects_misaligned_or_oversized_audio():
    track = _PCMTrack()
    with pytest.raises(ValueError, match="align to stereo s16le"):
        await track.push(b"\x00\x01\x02")
    with pytest.raises(ValueError, match="must not exceed 120 ms"):
        await track.push(b"\x00" * (48_000 * 2 * 2 * 0 + 48_000 * 2 * 2))
    track.stop()


@pytest.mark.asyncio
async def test_creates_real_local_join_payload_and_cleans_up():
    engine = AiortcTelegramMediaEngine(connect_timeout=1)
    payload = await engine.create_join_payload(chat_id=-100123)

    assert payload["ssrc"] != 0
    assert payload["ufrag"]
    assert payload["pwd"]
    assert payload["fingerprints"]
    assert payload["fingerprints"][0]["hash"] == "sha-256"
    assert await engine.source_id(-100123) == payload["ssrc"]
    await engine.close(-100123)
    assert not await engine.is_connected(-100123)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "audio_config, message",
    [
        (SimpleNamespace(sample_rate=24000, channels=2, codec="opus"), "sample_rate=48000"),
        (SimpleNamespace(sample_rate=48000, channels=1, codec="opus"), "channels=2"),
        (SimpleNamespace(sample_rate=48000, channels=2, codec="aac"), "Opus codec only"),
    ],
)
async def test_rejects_audio_formats_the_engine_cannot_encode(audio_config, message):
    engine = AiortcTelegramMediaEngine(connect_timeout=1)

    with pytest.raises(NotImplementedError, match=message):
        await engine.create_join_payload(-100125, audio_config=audio_config)

    assert -100125 not in engine._sessions


@pytest.mark.asyncio
async def test_accepts_supported_stereo_48khz_opus_audio_config():
    from tgcaller.types import AudioConfig

    engine = AiortcTelegramMediaEngine(connect_timeout=1)
    payload = await engine.create_join_payload(-100126, audio_config=AudioConfig())

    assert payload["ssrc"] != 0
    await engine.close(-100126)


@pytest.mark.asyncio
async def test_stream_mode_fails_closed_and_closes_prepared_session():
    engine = AiortcTelegramMediaEngine(connect_timeout=1)
    await engine.create_join_payload(chat_id=-100124)
    update = type(
        "UpdateGroupCallConnection",
        (),
        {"params": SimpleNamespace(data='{"stream":true}'), "presentation": False},
    )()

    with pytest.raises(ConnectionError, match="stream mode"):
        await engine.handle_join_updates(-100124, update)
    with pytest.raises(ConnectionError, match="No media session"):
        await engine.source_id(-100124)


@pytest.mark.asyncio
async def test_pcm_track_queue_full_fails_after_configured_timeout():
    track = _PCMTrack(queue_size=1, push_timeout=0.01)
    frame = bytes(3840)

    await track.push(frame)
    with pytest.raises(ConnectionError, match="queue remained full"):
        await track.push(frame)

    assert track.queue.qsize() == 1
    track.stop()


@pytest.mark.asyncio
async def test_pcm_track_blocked_push_can_be_cancelled_without_adding_a_frame():
    track = _PCMTrack(queue_size=1, push_timeout=1.0)
    frame = bytes(3840)

    await track.push(frame)
    pending = asyncio.create_task(track.push(frame))
    await asyncio.sleep(0)
    pending.cancel()

    with pytest.raises(asyncio.CancelledError):
        await pending

    assert track.queue.qsize() == 1
    track.stop()


def test_engine_rejects_invalid_queue_put_timeout():
    with pytest.raises(ValueError, match="queue_put_timeout must be positive"):
        AiortcTelegramMediaEngine(queue_put_timeout=0)


class _LifecycleTrack:
    def __init__(self):
        self.frames = []
        self.cleared = 0

    async def push(self, frame):
        self.frames.append(frame)

    def clear(self):
        self.cleared += 1


@pytest.mark.asyncio
async def test_concurrent_source_replacement_closes_old_async_iterator():
    engine = AiortcTelegramMediaEngine()
    session = SimpleNamespace(
        pc=SimpleNamespace(connectionState="connected"),
        track=_LifecycleTrack(),
    )
    engine._sessions[777] = session
    old_closed = asyncio.Event()
    release_old = asyncio.Event()

    async def old_source():
        try:
            yield bytes(3840)
            await release_old.wait()
            yield bytes(3840)
        finally:
            old_closed.set()

    async def new_source():
        yield bytes([1]) * 3840
        await asyncio.Event().wait()

    first = asyncio.create_task(engine.play_stream(777, old_source()))
    await asyncio.sleep(0)
    second = asyncio.create_task(engine.play_stream(777, new_source()))

    assert await asyncio.wait_for(first, timeout=1) is True
    assert await asyncio.wait_for(second, timeout=1) is True
    await asyncio.wait_for(old_closed.wait(), timeout=1)

    active = engine._stream_tasks.get(777)
    assert active is not None and not active.done()
    assert session.track.frames == [bytes(3840), bytes([1]) * 3840]

    await engine.stop_stream(777)
    assert 777 not in engine._stream_tasks


class _BlockingStdout:
    def __init__(self):
        self.read_started = asyncio.Event()
        self.release = asyncio.Event()

    async def read(self, size):
        self.read_started.set()
        await self.release.wait()
        return b""


class _FakePipeTransport:
    def __init__(self):
        self.close_calls = 0

    def close(self):
        self.close_calls += 1


class _FakeSubprocessTransport:
    def __init__(self):
        self.stdout_pipe = _FakePipeTransport()

    def get_pipe_transport(self, fd):
        return self.stdout_pipe if fd == 1 else None


class _FakeProcess:
    def __init__(self, *, hang_after_terminate=False):
        self.returncode = None
        self.stdout = _BlockingStdout()
        self._transport = _FakeSubprocessTransport()
        self.hang_after_terminate = hang_after_terminate
        self.exited = asyncio.Event()
        self.terminate_calls = 0
        self.kill_calls = 0
        self.wait_calls = 0

    def terminate(self):
        self.terminate_calls += 1
        if not self.hang_after_terminate:
            self.returncode = -15
            self.exited.set()

    def kill(self):
        self.kill_calls += 1
        self.returncode = -9
        self.exited.set()

    async def wait(self):
        self.wait_calls += 1
        await self.exited.wait()
        return self.returncode


@pytest.mark.asyncio
async def test_stop_process_terminates_and_reaps_process():
    engine = AiortcTelegramMediaEngine()
    process = _FakeProcess()

    await engine._stop_process(process)

    assert process.terminate_calls == 1
    assert process.kill_calls == 0
    assert process.wait_calls >= 1
    assert process.returncode == -15
    assert process._transport.stdout_pipe.close_calls == 1


@pytest.mark.asyncio
async def test_stop_process_kills_process_when_terminate_times_out(monkeypatch):
    engine = AiortcTelegramMediaEngine()
    process = _FakeProcess(hang_after_terminate=True)

    async def immediate_timeout(awaitable, timeout):
        # Close the timed-out coroutine to avoid an un-awaited coroutine warning.
        awaitable.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "wait_for", immediate_timeout)

    await engine._stop_process(process)

    assert process.terminate_calls == 1
    assert process.kill_calls == 1
    # Only the post-kill reap coroutine is actually awaited by this test double.
    assert process.wait_calls == 1
    assert process.returncode == -9
    assert process._transport.stdout_pipe.close_calls == 1


@pytest.mark.asyncio
async def test_stop_process_closes_stdout_for_already_exited_process():
    engine = AiortcTelegramMediaEngine()
    process = _FakeProcess()
    process.returncode = 0
    process.exited.set()

    await engine._stop_process(process)

    assert process.terminate_calls == 0
    assert process.wait_calls == 1
    assert process._transport.stdout_pipe.close_calls == 1


@pytest.mark.asyncio
async def test_natural_ffmpeg_eof_closes_stdout_and_clears_tracking():
    engine = AiortcTelegramMediaEngine()
    process = _FakeProcess()
    process.returncode = 0
    process.exited.set()
    process.stdout.release.set()
    engine._stream_processes[779] = process

    task = asyncio.create_task(engine._pump_ffmpeg_process(779, process))
    engine._stream_tasks[779] = task
    await task

    assert process.terminate_calls == 0
    assert process._transport.stdout_pipe.close_calls == 1
    assert 779 not in engine._stream_processes
    assert 779 not in engine._stream_tasks


@pytest.mark.asyncio
async def test_cancelled_ffmpeg_pump_reaps_process_and_clears_tracking():
    engine = AiortcTelegramMediaEngine()
    process = _FakeProcess()
    engine._stream_processes[778] = process

    task = asyncio.create_task(engine._pump_ffmpeg_process(778, process))
    engine._stream_tasks[778] = task
    await asyncio.wait_for(process.stdout.read_started.wait(), timeout=1)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert process.terminate_calls == 1
    assert process.returncode == -15
    assert process._transport.stdout_pipe.close_calls == 1
    assert 778 not in engine._stream_processes
    assert 778 not in engine._stream_tasks

@pytest.mark.asyncio
async def test_close_waits_for_inflight_stream_lifecycle_operation():
    engine = AiortcTelegramMediaEngine()
    lock = engine._stream_lock(778)
    await lock.acquire()
    close_task = asyncio.create_task(engine.close(778))
    await asyncio.sleep(0)

    assert not close_task.done()

    lock.release()
    await asyncio.wait_for(close_task, timeout=1)
    assert engine.get_connection_state(778) == "closed"

@pytest.mark.asyncio
async def test_real_ffmpeg_file_source_decodes_into_engine_pcm(tmp_path):
    import math
    import shutil
    import struct
    import wave

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg executable is not installed")

    source = tmp_path / "tone.wav"
    sample_rate = 16_000
    sample_count = sample_rate // 2
    samples = b"".join(
        struct.pack("<h", int(12_000 * math.sin(2 * math.pi * 440 * index / sample_rate)))
        for index in range(sample_count)
    )
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples)

    engine = AiortcTelegramMediaEngine()
    track = _LifecycleTrack()
    engine._sessions[991] = SimpleNamespace(
        pc=SimpleNamespace(connectionState="connected"),
        track=track,
    )

    assert await engine.play_stream(991, SimpleNamespace(source=str(source))) is True
    task = engine._stream_tasks[991]
    await asyncio.wait_for(task, timeout=10)

    assert 991 not in engine._stream_tasks
    assert 991 not in engine._stream_processes
    assert len(track.frames) >= 2
    assert all(frame and len(frame) % 4 == 0 for frame in track.frames)
    decoded = b"".join(track.frames)
    assert len(decoded) >= 48_000 * 2 * 2 // 4
    assert any(decoded)



@pytest.mark.asyncio
async def test_local_aiortc_peer_receives_encoded_pcm_over_opus_rtp():
    """Exercise the engine PCM track through real aiortc/Opus/RTP loopback."""
    from aiortc import RTCPeerConnection, RTCSessionDescription

    engine = AiortcTelegramMediaEngine(connect_timeout=5)
    chat_id = 992
    payload = await engine.create_join_payload(chat_id)
    session = engine._sessions[chat_id]
    remote = RTCPeerConnection()
    received_tracks = asyncio.Queue()

    @remote.on("track")
    def on_track(track):
        if track.kind == "audio":
            received_tracks.put_nowait(track)

    try:
        offer = RTCSessionDescription(sdp=session.local_offer_sdp, type="offer")
        await remote.setRemoteDescription(offer)
        answer = await remote.createAnswer()
        await remote.setLocalDescription(answer)
        await session.pc.setRemoteDescription(
            RTCSessionDescription(
                sdp=remote.localDescription.sdp,
                type=remote.localDescription.type,
            )
        )

        await asyncio.wait_for(
            asyncio.gather(
                engine.wait_for_connection_state(chat_id, "connected", timeout=5),
                _wait_for_peer_connected(remote, timeout=5),
            ),
            timeout=6,
        )
        inbound = await asyncio.wait_for(received_tracks.get(), timeout=2)

        # Non-silent samples prove that the encoded RTP payload carries source
        # audio, rather than merely establishing ICE/DTLS successfully.
        pcm = b"".join(
            int(8_000 * math.sin(2 * math.pi * 440 * index / 48_000)).to_bytes(
                2, "little", signed=True
            ) * 2
            for index in range(960)
        )
        await engine.send_frame(chat_id, pcm, "audio")
        decoded = await asyncio.wait_for(inbound.recv(), timeout=3)
        assert decoded.samples > 0
        assert decoded.sample_rate == 48_000
        assert any(bytes(plane) for plane in decoded.planes)
        assert payload["ssrc"] == session.source_id
    finally:
        await remote.close()
        await engine.close(chat_id)


async def _wait_for_peer_connected(peer, timeout):
    async def wait():
        while peer.connectionState != "connected":
            if peer.connectionState in {"failed", "closed"}:
                raise AssertionError(
                    f"Local RTP loopback peer entered {peer.connectionState}"
                )
            await asyncio.sleep(0.01)
    await asyncio.wait_for(wait(), timeout=timeout)
