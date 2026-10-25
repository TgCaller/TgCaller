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
