"""Thin yt-dlp wrapper for YouTube downloads used by the advanced API."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yt_dlp
except ImportError:  # pragma: no cover - optional dependency guard.
    yt_dlp = None

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Download a YouTube URL using yt-dlp with a small, safe API."""

    def __init__(self, output_dir: str = "."):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def download(self, url: str, *, format: str = "best", filename: Optional[str] = None) -> Dict[str, Any]:
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is required for YouTube downloads")

        target = self.output_dir / (filename or "download")
        opts = {
            "format": format,
            "outtmpl": str(target),
            "quiet": True,
            "noplaylist": True,
        }

        def _run() -> Dict[str, Any]:
            with yt_dlp.YoutubeDL(opts) as downloader:
                info = downloader.extract_info(url, download=True)
            return {"url": url, "info": info, "path": str(target)}

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)

    async def get_info(self, url: str) -> Dict[str, Any]:
        if yt_dlp is None:
            raise RuntimeError("yt-dlp is required for YouTube metadata fetches")

        def _run() -> Dict[str, Any]:
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True}) as downloader:
                return downloader.extract_info(url, download=False)

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _run)
