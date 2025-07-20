"""
API Decorators
"""

from typing import Callable


def on_custom_update(func: Callable = None):
    """
    Decorator for custom API update handler
    
    Only one handler can be registered at a time.
    
    Example:
        ```python
        @caller.on_custom_update
        async def handle_custom_request(client, data):
            return {"message": "Request processed"}
        ```
    """
    def decorator(f):
        f._is_custom_update_handler = True
        return f
    
    return decorator(func) if func else decorator