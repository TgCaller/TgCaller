"""Regression tests for public import and package stability."""

from tgcaller import TgCaller
from tgcaller.advanced import (
    AdvancedYouTubeStreamer,
    AudioFilters,
    BridgedCallManager,
    CustomAPIHandler,
    MicrophoneCapture,
    PerformanceMonitor,
    ScreenShare,
    VideoFilters,
    YouTubeDownloader,
)
from tgcaller.api import CustomAPIServer, on_custom_update
from tgcaller.handlers import (
    EventHandlerSystem,
    Filters,
    and_filter,
    or_filter,
)


def test_package_exports_are_importable():
    assert callable(TgCaller)
    assert callable(CustomAPIServer)
    assert callable(on_custom_update)
    assert callable(EventHandlerSystem)
    assert callable(Filters.chat_id)
    assert callable(and_filter)
    assert callable(or_filter)


def test_advanced_exports_are_importable():
    assert callable(BridgedCallManager)
    assert callable(MicrophoneCapture)
    assert callable(CustomAPIHandler)
    assert callable(AudioFilters)
    assert callable(VideoFilters)
    assert callable(ScreenShare)
    assert callable(YouTubeDownloader)
    assert callable(AdvancedYouTubeStreamer)
    assert callable(PerformanceMonitor)
