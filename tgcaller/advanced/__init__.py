"""
TgCaller Advanced Features.

Exports are loaded lazily so importing the core package does not require every
optional media dependency to be installed.
"""

from importlib import import_module

_EXPORTS = {
    "BridgedCallManager": ".bridged_calls",
    "MicrophoneCapture": ".capture_mic",
    "CustomAPIHandler": ".custom_api",
    "AudioFilters": ".custom_filters",
    "VideoFilters": ".custom_filters",
    "ScreenShare": ".screen_sharing",
    "WhisperTranscription": ".transcription",
    "YouTubeDownloader": ".youtube_dl",
    "AdvancedYouTubeStreamer": ".youtube_streaming",
    "PerformanceMonitor": ".youtube_streaming",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    """Load an implemented advanced feature only when it is requested."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name, __name__)
    try:
        value = getattr(module, name)
    except AttributeError as exc:
        raise AttributeError(
            f"advanced feature {name!r} is not available in this installation"
        ) from exc

    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
