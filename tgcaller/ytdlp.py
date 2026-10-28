"""Compatibility imports for YouTube helpers.

The downloader lives in ``advanced.youtube_dl`` and the single streaming
implementation lives in ``streaming.youtube_streamer``.
"""

from .advanced.youtube_dl import YouTubeDownloader
from .streaming.youtube_streamer import YouTubeStreamer

__all__ = ["YouTubeDownloader", "YouTubeStreamer"]
