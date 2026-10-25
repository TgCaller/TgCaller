"""Utilities for converting a raw stream into a FIFO-friendly byte format."""

from __future__ import annotations

import asyncio
import io
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FIFOConverter:
    """Convert arbitrary bytes-like payloads into a stream-friendly format.

    This keeps the public API usable without requiring a full OS-level FIFO stack.
    """

    def __init__(self, buffer_size: int = 4096):
        self.buffer_size = max(1, int(buffer_size))
        self._buffer = io.BytesIO()

    def convert(self, payload: Any) -> bytes:
        if payload is None:
            return b""
        if isinstance(payload, bytes):
            return payload
        if isinstance(payload, bytearray):
            return bytes(payload)
        return str(payload).encode("utf-8")

    async def convert_async(self, payload: Any) -> bytes:
        return self.convert(payload)

    def reset(self) -> None:
        self._buffer = io.BytesIO()

    def push(self, payload: Any) -> bytes:
        data = self.convert(payload)
        self._buffer.write(data)
        return data

    def read(self, size: Optional[int] = None) -> bytes:
        if size is None:
            size = self.buffer_size
        chunk = self._buffer.getvalue()[:size]
        remainder = self._buffer.getvalue()[size:]
        self._buffer = io.BytesIO(remainder.encode("utf-8") if isinstance(remainder, str) else b"")
        return chunk
