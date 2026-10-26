"""Regression tests for stable public package imports."""

import importlib


def test_core_package_imports_without_loading_advanced_features():
    package = importlib.import_module("tgcaller")
    assert package.TgCaller is not None
    assert "ExternalCapture" not in package.__all__
    assert "FIFOConverter" not in package.__all__


def test_advanced_package_exports_only_implemented_modules():
    advanced = importlib.import_module("tgcaller.advanced")
    assert "MicrophoneCapture" in advanced.__all__
    assert "ScreenShare" in advanced.__all__
    assert "YouTubeStreamer" in advanced.__all__
    assert "ExternalCapture" not in advanced.__all__
    assert "FIFOConverter" not in advanced.__all__


def test_advanced_control_api_uses_the_named_control_module():
    from tgcaller.advanced import CustomAPIHandler

    assert CustomAPIHandler.__module__ == "tgcaller.advanced.control_api"


def test_advanced_and_streaming_paths_share_one_youtube_streamer():
    from tgcaller.advanced import YouTubeStreamer as AdvancedStreamer
    from tgcaller.advanced.youtube_dl import YouTubeStreamer as LegacyPathStreamer
    from tgcaller.streaming import YouTubeStreamer as StreamingStreamer

    assert AdvancedStreamer is StreamingStreamer
    assert LegacyPathStreamer is StreamingStreamer


def test_documented_advanced_youtube_import_resolves():
    from tgcaller.advanced import YouTubeStreamer, YouTubeDownloader

    assert YouTubeStreamer is not None
    assert YouTubeDownloader is not None


def test_legacy_module_paths_reexport_canonical_implementations():
    from tgcaller import TgCaller
    from tgcaller.tgcaller import TgCaller as LegacyTgCaller
    from tgcaller.ffmpeg import ProcessorConfig, StreamProcessor
    from tgcaller.streaming import ProcessorConfig as CanonicalProcessorConfig
    from tgcaller.streaming import StreamProcessor as CanonicalStreamProcessor
    from tgcaller.ytdlp import YouTubeStreamer as LegacyYouTubeStreamer
    from tgcaller.streaming import YouTubeStreamer as CanonicalYouTubeStreamer
    from tgcaller.plugins import BasePlugin, PluginManager

    assert LegacyTgCaller is TgCaller
    assert StreamProcessor is CanonicalStreamProcessor
    assert ProcessorConfig is CanonicalProcessorConfig
    assert LegacyYouTubeStreamer is CanonicalYouTubeStreamer
    assert BasePlugin is not None
    assert PluginManager is not None


def test_missing_advanced_symbols_are_not_reported_as_available():
    package = importlib.import_module("tgcaller")
    assert not hasattr(package, "ExternalCapture")
    assert not hasattr(package, "FIFOConverter")
    assert not hasattr(package, "FrameSender")


def test_advanced_youtube_streaming_exports_resolve():
    from tgcaller import AdvancedYouTubeStreamer, PerformanceMonitor
    from tgcaller.streaming import BufferPriority

    assert AdvancedYouTubeStreamer is not None
    assert PerformanceMonitor is not None
    assert BufferPriority.HIGH.value == 3
