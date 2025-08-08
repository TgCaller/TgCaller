"""
TgCaller API Hooks Module
"""

from .webhooks import Webhooks
from .external_control import ExternalControl

__all__ = [
    "Webhooks",
    "ExternalControl",
]