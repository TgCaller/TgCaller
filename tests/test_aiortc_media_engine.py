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
