"""Regression tests for finite FastStreamBuffer source lifecycle."""

import asyncio

import pytest

from tgcaller.streaming.fast_stream_buffer import BufferConfig, BufferState, FastStreamBuffer


@pytest.mark.asyncio
async def test_consumer_exits_after_finite_source_is_fully_drained():
    buffer = FastStreamBuffer(
        BufferConfig(
            min_buffer_size=3,
            target_buffer_size=4,
            max_buffer_size=8,
            use_threading=False,
        )
    )
    received = []

    async def source():
        yield b"first"
        yield b"second"

    async def receive(chunk):
        received.append(chunk.data)

    buffer.add_chunk_callback(receive)
    assert await buffer.start_buffering(source()) is True

    await asyncio.wait_for(buffer.consumer_task, timeout=1.0)
    await asyncio.wait_for(buffer.producer_task, timeout=1.0)

    assert received == [b"first", b"second"]
    assert buffer.stats["chunks_consumed"] == 2
    assert buffer.state is BufferState.IDLE

    await buffer.stop_buffering()
