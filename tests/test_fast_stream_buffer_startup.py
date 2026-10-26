import asyncio

import pytest

from tgcaller.streaming.fast_stream_buffer import BufferConfig, FastStreamBuffer


@pytest.mark.asyncio
async def test_consumer_waits_for_minimum_startup_buffer():
    first_yielded = asyncio.Event()
    allow_second = asyncio.Event()
    consumed = []

    async def source():
        first_yielded.set()
        yield b"first"
        await allow_second.wait()
        yield b"second"

    buffer = FastStreamBuffer(
        BufferConfig(
            min_buffer_size=2,
            target_buffer_size=2,
            max_buffer_size=4,
            adaptive_quality=False,
            use_threading=False,
        )
    )
    buffer.add_chunk_callback(lambda chunk: consumed.append(chunk.data))

    assert await buffer.start_buffering(source())
    await asyncio.wait_for(first_yielded.wait(), timeout=1)
    # Give the producer time to add its first chunk. It must not be consumed
    # before the configured startup buffer has been primed.
    await asyncio.sleep(0.02)
    assert consumed == []

    allow_second.set()
    for _ in range(100):
        if len(consumed) == 2:
            break
        await asyncio.sleep(0.005)

    assert consumed == [b"first", b"second"]
    await buffer.stop_buffering()


@pytest.mark.asyncio
async def test_consumer_drains_short_source_below_minimum_buffer():
    consumed = []

    async def source():
        yield b"only-chunk"

    buffer = FastStreamBuffer(
        BufferConfig(
            min_buffer_size=3,
            target_buffer_size=3,
            max_buffer_size=4,
            adaptive_quality=False,
            use_threading=False,
        )
    )
    buffer.add_chunk_callback(lambda chunk: consumed.append(chunk.data))

    assert await buffer.start_buffering(source())
    for _ in range(100):
        if consumed:
            break
        await asyncio.sleep(0.005)

    assert consumed == [b"only-chunk"]
    await buffer.stop_buffering()
