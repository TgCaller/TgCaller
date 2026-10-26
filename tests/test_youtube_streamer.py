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

    await streamer.buffer.chunk_callbacks[0](chunk)
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

@pytest.mark.asyncio
async def test_ffmpeg_stderr_is_not_left_as_an_unread_pipe(streamer, monkeypatch):
    streamer.stream_url = "https://media.example/audio"
    captured = {}

    class ExitedProcess:
        stdout = None
        returncode = 1

        def poll(self):
            return self.returncode

    def fake_popen(command, **kwargs):
        captured.update(kwargs)
        return ExitedProcess()

    async def no_wait(_seconds):
        return None

    monkeypatch.setattr(youtube_streamer.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(youtube_streamer.asyncio, "sleep", no_wait)

    assert await streamer._start_ffmpeg_process() is False
    assert captured["stderr"] == youtube_streamer.subprocess.DEVNULL


@pytest.mark.asyncio
async def test_video_request_is_rejected_before_url_lookup_or_call_join(streamer, monkeypatch):
    streamer.config.enable_video = True

    async def unexpected_url_lookup(_url):
        raise AssertionError("unsupported video request must fail before URL lookup")

    monkeypatch.setattr(streamer, "_get_stream_url", unexpected_url_lookup)

    assert not await streamer.stream_youtube_url(
        -100123,
        "https://youtube.com/watch?v=test",
        video_config=object(),
    )


@pytest.mark.asyncio
async def test_url_fallback_selects_audio_format_not_last_video_format(streamer, monkeypatch):
    class FakeYoutubeDL:
        def __init__(self, _options):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def extract_info(self, _url, download=False):
            return {
                "formats": [
                    {
                        "url": "https://media.example/video-only",
                        "acodec": "none",
                        "vcodec": "avc1",
                        "tbr": 1200,
                    },
                    {
                        "url": "https://media.example/audio-low",
                        "acodec": "opus",
                        "vcodec": "none",
                        "abr": 64,
                    },
                    {
                        "url": "https://media.example/audio-high",
                        "acodec": "opus",
                        "vcodec": "none",
                        "abr": 128,
                    },
                ]
            }

    monkeypatch.setattr(
        youtube_streamer,
        "yt_dlp",
        type("FakeYtDlp", (), {"YoutubeDL": FakeYoutubeDL}),
    )

    assert await streamer._get_stream_url(
        "https://youtube.com/watch?v=test"
    ) == "https://media.example/audio-high"

@pytest.mark.asyncio
async def test_default_pcm_chunk_size_is_one_20ms_stereo_s16le_frame(streamer):
    # 48,000 samples/s * 0.020 s * 2 channels * 2 bytes/sample.
    assert streamer.config.chunk_size == 3840


@pytest.mark.asyncio
async def test_ffmpeg_reader_accumulates_short_pipe_reads(streamer):
    class FragmentedReader:
        def __init__(self):
            self.parts = [b"ab", b"cde", b"fghij"]
            self.remainder = b""

        def read(self, size):
            if not self.remainder and self.parts:
                self.remainder = self.parts.pop(0)
            result, self.remainder = self.remainder[:size], self.remainder[size:]
            return result

    class FakeProcess:
        stdout = FragmentedReader()

    streamer.config.chunk_size = 8
    streamer.ffmpeg_process = FakeProcess()

    chunk = await streamer._read_ffmpeg_chunk()

    assert chunk == b"abcdefgh"
    assert len(chunk) % 4 == 0

