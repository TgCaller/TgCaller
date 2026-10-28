import asyncio

import pytest

from tgcaller.streaming.fast_stream_buffer import BufferState, FastStreamBuffer


@pytest.mark.asyncio
async def test_producer_preserves_source_order():
    buffer = FastStreamBuffer()
    buffer.state = BufferState.FILLING
    processed = []

    async def source():
        for item in (b"first", b"second", b"third"):
            yield item

    async def record(raw_data):
        # Simulate variable work time: ordering must not depend on task timing.
        if raw_data == b"first":
            await asyncio.sleep(0.01)
        processed.append(raw_data)

    buffer._process_raw_chunk = record

    await buffer._producer_loop(source())

    assert processed == [b"first", b"second", b"third"]
