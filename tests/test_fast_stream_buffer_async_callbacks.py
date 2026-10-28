import asyncio
import time

import pytest

from tgcaller.streaming.fast_stream_buffer import BufferConfig, FastStreamBuffer, StreamChunk


@pytest.mark.asyncio
async def test_buffer_awaits_async_chunk_callback():
    buffer = FastStreamBuffer(BufferConfig(adaptive_quality=False))
    delivered = []

    async def callback(chunk):
        await asyncio.sleep(0)
        delivered.append(chunk.sequence)

    buffer.add_chunk_callback(callback)
    chunk = StreamChunk(
        data=b"audio",
        timestamp=time.time(),
        sequence=7,
    )

    await buffer._process_chunk(chunk)

    assert delivered == [7]
