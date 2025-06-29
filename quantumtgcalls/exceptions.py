"""
QuantumTgCalls Exceptions
"""


class QuantumError(Exception):
    """Base exception for QuantumTgCalls"""
    pass


class ConnectionError(QuantumError):
    """Connection related errors"""
    pass


class MediaError(QuantumError):
    """Media processing errors"""
    pass


class CallError(QuantumError):
    """Call related errors"""
    pass


class StreamError(QuantumError):
    """Stream related errors"""
    pass


class PluginError(QuantumError):
    """Plugin related errors"""
    pass


class ConfigurationError(QuantumError):
    """Configuration errors"""
    pass