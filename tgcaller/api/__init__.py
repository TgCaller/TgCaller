
"""Public API exports for TgCaller."""

from .decorators import on_custom_update

try:
    from .server import CustomAPIServer
except ImportError:
    CustomAPIServer = None

__all__ = [
    "CustomAPIServer",
    "on_custom_update",
]
