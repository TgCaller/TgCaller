"""Tests for advanced capture adapters and honest capability boundaries."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from tgcaller.advanced.capture_mic import MicrophoneStreamer
from tgcaller.advanced.screen_sharing import ScreenShareStreamer


class _FakeAudioArray:
    def astype(self, dtype, copy=False):
        assert dtype == "int16"
        return self

    def tobytes(self):
        return b"\x00\x00\x00\x00"


@pytest.mark.asyncio
async def test_microphone_streamer_forwards_pcm_to_caller_loop():
    caller = Mock()
    caller.send_frame = AsyncMock(return_value=True)
    streamer = MicrophoneStreamer(caller, -100123)
    streamer._loop = asyncio.get_running_loop()
    streamer.is_streaming = True

    streamer._stream_audio(_FakeAudioArray())
    await asyncio.sleep(0.01)

    caller.send_frame.assert_awaited_once_with(-100123, b"\x00\x00\x00\x00", "audio")


@pytest.mark.asyncio
async def test_microphone_streamer_bounds_in_flight_audio_sends():
    caller = Mock()
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_send(*_args):
        started.set()
        await release.wait()
        return True

    caller.send_frame = AsyncMock(side_effect=slow_send)
    streamer = MicrophoneStreamer(caller, -100123)
    streamer._loop = asyncio.get_running_loop()
    streamer.is_streaming = True

    streamer._stream_audio(_FakeAudioArray())
    await asyncio.wait_for(started.wait(), timeout=1.0)
    streamer._stream_audio(_FakeAudioArray())
    await asyncio.sleep(0.01)

    assert caller.send_frame.await_count == 1

    release.set()
    await asyncio.sleep(0.01)
    streamer._stream_audio(_FakeAudioArray())
    await asyncio.sleep(0.01)

    assert caller.send_frame.await_count == 2
    await streamer.stop_streaming()


@pytest.mark.asyncio
async def test_screen_share_streamer_fails_closed_until_video_transport_exists():
    streamer = ScreenShareStreamer(Mock(), -100123)

    with pytest.raises(NotImplementedError, match="currently supports audio RTP"):
        await streamer.start_streaming()

    assert streamer.is_streaming is False
