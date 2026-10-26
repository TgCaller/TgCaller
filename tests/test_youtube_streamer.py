import asyncio
import time

import pytest

import tgcaller.streaming.youtube_streamer as youtube_streamer


class FakeCaller:
    def __init__(self):
        self.sent_frames = []

    def is_connected(self, chat_id):
        return True

    async def join_call(self, *args):
        raise AssertionError("join_call should not be needed in this test")

    async def send_frame(self, chat_id, frame_data, frame_type):
        self.sent_frames.append((chat_id, frame_data, frame_type))


@pytest.fixture
def streamer(monkeypatch):
    # The tests exercise pipeline control flow, not yt-dlp network access.
    monkeypatch.setattr(youtube_streamer, "yt_dlp", object())
    return youtube_streamer.YouTubeStreamer(
        FakeCaller(),
        youtube_streamer.YouTubeStreamConfig(
            enable_audio=True,
            enable_video=False,
            use_hardware_acceleration=False,
        ),
    )


@pytest.mark.asyncio
async def test_stream_flag_is_set_before_pipeline_starts(streamer, monkeypatch):
    async def get_url(_url):
        return "https://media.example/audio"

    async def start_pipeline():
        # The source generator checks this flag on its first iteration.
        assert streamer.is_streaming is True
        return True

    monkeypatch.setattr(streamer, "_get_stream_url", get_url)
    monkeypatch.setattr(streamer, "_start_streaming_pipeline", start_pipeline)

    assert await streamer.stream_youtube_url(-100123, "https://youtube.com/watch?v=test")
    assert streamer.is_streaming is True
    assert streamer.stream_stats["start_time"] > 0


def test_ffmpeg_command_is_audio_only(streamer):
    streamer.stream_url = "https://media.example/audio"

    command = streamer._build_ffmpeg_command()

    assert "-vn" in command
    assert "-acodec" in command
    assert "pcm_s16le" in command
    assert "rawvideo" not in command
    assert "-vcodec" not in command


def test_ffmpeg_command_rejects_unimplemented_video(streamer):
    streamer.stream_url = "https://media.example/video"
    streamer.config.enable_video = True

    with pytest.raises(NotImplementedError, match="video output is not implemented"):
        streamer._build_ffmpeg_command()


@pytest.mark.asyncio
async def test_buffer_chunk_callback_sends_audio_to_caller(streamer):
    streamer.current_chat_id = -100123
    streamer.buffer = youtube_streamer.FastStreamBuffer(streamer.config.buffer_config)
    streamer._setup_buffer_callbacks()
    chunk = youtube_streamer.StreamChunk(
        data=b"\x00\x00" * 16,
        timestamp=time.time(),
        sequence=1,
        chunk_type="audio",
    )

    streamer.buffer.chunk_callbacks[0](chunk)
    for _ in range(10):
        if streamer.caller.sent_frames:
            break
        await asyncio.sleep(0)

    assert streamer.caller.sent_frames == [(-100123, chunk.data, "audio")]
    assert streamer.stream_stats["chunks_processed"] == 1

@pytest.mark.asyncio
async def test_audio_chunks_are_sent_in_source_order(streamer, monkeypatch):
    streamer.current_chat_id = -100123

    async def delayed_send(chat_id, frame_data, frame_type):
        if frame_data == b"first":
            await asyncio.sleep(0.02)
        streamer.caller.sent_frames.append((chat_id, frame_data, frame_type))

    monkeypatch.setattr(streamer.caller, "send_frame", delayed_send)
    first = youtube_streamer.StreamChunk(
        data=b"first", timestamp=time.time(), sequence=1, chunk_type="audio"
    )
    second = youtube_streamer.StreamChunk(
        data=b"second", timestamp=time.time(), sequence=2, chunk_type="audio"
    )

    await asyncio.gather(
        streamer._send_chunk_to_caller(first),
        streamer._send_chunk_to_caller(second),
    )

    assert streamer.caller.sent_frames == [
        (-100123, b"first", "audio"),
        (-100123, b"second", "audio"),
    ]
