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


def test_documented_advanced_youtube_import_resolves():
    advanced = importlib.import_module("tgcaller.advanced")
    from tgcaller.advanced import YouTubeStreamer, YouTubeDownloader

    assert YouTubeStreamer is not None
    assert YouTubeDownloader is not None
    assert advanced.YouTubeStreamer is YouTubeStreamer


def test_missing_advanced_symbols_are_not_reported_as_available():
    package = importlib.import_module("tgcaller")
    assert not hasattr(package, "ExternalCapture")
    assert not hasattr(package, "FIFOConverter")
    assert not hasattr(package, "FrameSender")
