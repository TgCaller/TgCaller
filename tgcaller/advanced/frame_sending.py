"""Frame-sending helper for advanced streaming integrations."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)


class FrameSender:
    """Queue raw frames and dispatch them to a callback or caller."""

    def __init__(self, callback: Optional[Callable[[Any], Any]] = None):
        self.callback = callback
        self._queue: List[Any] = []
        self._lock = asyncio.Lock()

    async def send(self, frame: Any) -> None:
        if self.callback is not None:
            await self.callback(frame)
            return
        async with self._lock:
            self._queue.append(frame)

    async def drain(self) -> list:
        async with self._lock:
            frames = list(self._queue)
            self._queue.clear()
            return frames

    def queued_count(self) -> int:
        return len(self._queue)
