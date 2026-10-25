import asyncio

import pytest

import tgcaller.streaming.youtube_streamer as youtube_streamer


class FakeCaller:
    def is_connected(self, chat_id):
        return True

    async def join_call(self, *args):
        raise AssertionError("join_call should not be needed in this test")


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
