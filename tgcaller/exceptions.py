"""
TgCaller Exceptions
"""


class TgCallerError(Exception):
    """Base exception for TgCaller"""
    pass


class ConnectionError(TgCallerError):
    """Connection related errors"""
    pass


class MediaError(TgCallerError):
    """Media processing errors"""
    pass


class CallError(TgCallerError):
    """Call related errors"""
    pass


class StreamError(TgCallerError):
    """Stream related errors"""
    pass


class ConfigurationError(TgCallerError):
    """Configuration errors"""
    pass