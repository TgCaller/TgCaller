"""Minimal raw-stream helper for advanced audio/video transport."""

from __future__ import annotations

import asyncio
from typing import Any, Optional


class RawStreamer:
    """Stream raw payloads to a callback without enforcing a transport layer."""

    def __init__(self, callback=None):
        self.callback = callback
        self.running = False
        self._task = None

    async def start(self) -> bool:
        self.running = True
        if self.callback is not None and self._task is None:
            self._task = asyncio.create_task(self._run())
        return True

    async def stop(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _run(self) -> None:
        while self.running:
            await asyncio.sleep(0.05)
            if self.callback is not None:
                self.callback({"running": True})

    async def send(self, payload: Any) -> Any:
        if self.callback is not None:
            return await self.callback(payload)
        return payload
