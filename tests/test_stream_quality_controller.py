"""Regression tests for safe adaptive stream quality handling."""

import pytest

from tgcaller.streaming.fast_stream_buffer import (
    BufferConfig,
    FastStreamBuffer,
    QualityController,
    StreamChunk,
)


@pytest.mark.asyncio
async def test_quality_adjustment_never_truncates_media_bytes():
    buffer = FastStreamBuffer(BufferConfig(use_threading=False))
    controller = QualityController(buffer)
    controller.current_quality = "low"
    original = bytes(range(256)) * 4
    chunk = StreamChunk(
        data=original,
        timestamp=1.0,
        sequence=1,
        metadata={},
    )

    adjusted = await controller._apply_quality_adjustments(chunk)

    assert adjusted.data == original
    assert adjusted.metadata["quality_level"] == "low"
    assert adjusted.metadata["bitrate_factor"] == 0.4


@pytest.mark.asyncio
@pytest.mark.parametrize("level", [0.0, 0.1, 0.5, 1.0])
async def test_legacy_compression_helper_is_safe_identity(level):
    buffer = FastStreamBuffer(BufferConfig(use_threading=False))
    controller = QualityController(buffer)
    media_bytes = b"\x00\x01\x02\x03" * 64

    assert await controller._compress_chunk_data(media_bytes, level) == media_bytes


@pytest.mark.asyncio
async def test_legacy_compression_helper_rejects_invalid_level():
    buffer = FastStreamBuffer(BufferConfig(use_threading=False))
    controller = QualityController(buffer)

    with pytest.raises(ValueError):
        await controller._compress_chunk_data(b"media", 1.5)


from tgcaller.streaming.stream_processor import ProcessorConfig, StreamProcessor


@pytest.mark.parametrize("output_format", ["raw", "opus", "aac"])
def test_audio_processor_builds_supported_output_commands(output_format):
    processor = StreamProcessor(ProcessorConfig(use_hardware_acceleration=False))
    command = processor._build_processing_command(output_format)

    assert command[0] == "ffmpeg"
    assert "pipe:0" in command
    assert "pipe:1" in command


@pytest.mark.parametrize("output_format", ["h264", "mp4", "video", "unknown"])
def test_audio_processor_rejects_unsupported_formats(output_format):
    processor = StreamProcessor()

    with pytest.raises(ValueError, match="Unsupported audio output format"):
        processor._build_processing_command(output_format)


class _FakeFFmpegProcess:
    def __init__(self, stdout=b"processed-audio", stderr=b"", returncode=0):
        self.stdout_data = stdout
        self.stderr_data = stderr
        self.returncode = returncode
        self.received_input = None
        self.killed = False

    async def communicate(self, input=None):
        self.received_input = input
        return self.stdout_data, self.stderr_data

    def kill(self):
        self.killed = True

    async def wait(self):
        return self.returncode


@pytest.mark.asyncio
async def test_processor_returns_complete_subprocess_output(monkeypatch):
    from tgcaller.streaming import stream_processor as module

    fake_process = _FakeFFmpegProcess(stdout=b"complete-output")
    async def fake_create_subprocess_exec(*args, **kwargs):
        assert kwargs["stdin"] is module.asyncio.subprocess.PIPE
        assert kwargs["stdout"] is module.asyncio.subprocess.PIPE
        return fake_process

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    processor = StreamProcessor()
    assert await processor._start_ffmpeg_processor("raw")
    chunk = StreamChunk(
        data=b"input-pcm",
        timestamp=2.0,
        sequence=7,
        metadata={},
    )

    result = await processor._process_single_chunk(chunk)

    assert fake_process.received_input == b"input-pcm"
    assert result is not None
    assert result.data == b"complete-output"
    assert result.sequence == 7
    assert result.metadata["processed_size"] == len(b"complete-output")


@pytest.mark.asyncio
async def test_processor_records_ffmpeg_nonzero_exit_as_error(monkeypatch):
    from tgcaller.streaming import stream_processor as module

    fake_process = _FakeFFmpegProcess(
        stdout=b"",
        stderr=b"invalid input",
        returncode=1,
    )
    async def fake_create_subprocess_exec(*args, **kwargs):
        return fake_process

    monkeypatch.setattr(module.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    processor = StreamProcessor()
    assert await processor._start_ffmpeg_processor("raw")
    chunk = StreamChunk(
        data=b"bad-pcm",
        timestamp=3.0,
        sequence=8,
        metadata={},
    )

    result = await processor._process_single_chunk(chunk)

    assert result is None
    assert processor.processing_stats["errors"] == 1
