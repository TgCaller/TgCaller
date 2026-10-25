"""Compatibility wrappers for TgCaller advanced stream helpers.

These modules provide the public API expected by the package while keeping the
implementations dependency-aware and lightweight enough for local import checks.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ExternalCapture:
    """Small helper for capturing frames or external media sources.

    The class does not replace a real media stack; it exposes a stable runtime
    contract for advanced integrations and allows callers to register a callback.
    """

    def __init__(self, source: Optional[str] = None, callback: Optional[Callable[[Any], None]] = None):
        self.source = source
        self.callback = callback
        self.running = False
        self._task = None

    async def start(self) -> bool:
        if self.running:
            return True
        self.running = True
        if self.callback is not None:
            self._task = asyncio.create_task(self._emit_loop())
        return True

    async def stop(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _emit_loop(self) -> None:
        while self.running:
            await asyncio.sleep(0.1)
            if self.callback is not None:
                self.callback({"source": self.source, "running": self.running})

    def capture(self, *, source: Optional[str] = None) -> dict:
        return {"source": source or self.source, "running": self.running}
