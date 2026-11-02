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
    await asyncio.sleep(0)

    caller.send_frame.assert_awaited_once_with(-100123, b"\x00\x00\x00\x00", "audio")


@pytest.mark.asyncio
async def test_screen_share_streamer_fails_closed_until_video_transport_exists():
    streamer = ScreenShareStreamer(Mock(), -100123)

    with pytest.raises(NotImplementedError, match="currently supports audio RTP"):
        await streamer.start_streaming()

    assert streamer.is_streaming is False
