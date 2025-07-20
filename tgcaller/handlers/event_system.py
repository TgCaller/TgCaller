"""
Internal Event Handler System with Filter Support
"""

import asyncio
import logging
from typing import List, Callable, Optional, Any, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HandlerInfo:
    """Information about registered handler"""
    func: Callable
    filters: Optional['BaseFilter']
    priority: int


class BaseFilter:
    """Base class for event filters"""
    
    async def check(self, update: Any, client: Any) -> bool:
        """Check if filter matches"""
        raise NotImplementedError


class ChatFilter(BaseFilter):
    """Filter by chat ID"""
    
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
    
    async def check(self, update: Any, client: Any) -> bool:
        return hasattr(update, 'chat_id') and update.chat_id == self.chat_id


class UserFilter(BaseFilter):
    """Filter by user ID"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
    
    async def check(self, update: Any, client: Any) -> bool:
        return hasattr(update, 'user_id') and update.user_id == self.user_id


class StatusFilter(BaseFilter):
    """Filter by status"""
    
    def __init__(self, status: str):
        self.status = status
    
    async def check(self, update: Any, client: Any) -> bool:
        return hasattr(update, 'status') and str(update.status) == self.status


class AndFilter(BaseFilter):
    """Combine filters with AND logic"""
    
    def __init__(self, *filters: BaseFilter):
        self.filters = filters
    
    async def check(self, update: Any, client: Any) -> bool:
        for filter_obj in self.filters:
            if not await filter_obj.check(update, client):
                return False
        return True


class OrFilter(BaseFilter):
    """Combine filters with OR logic"""
    
    def __init__(self, *filters: BaseFilter):
        self.filters = filters
    
    async def check(self, update: Any, client: Any) -> bool:
        for filter_obj in self.filters:
            if await filter_obj.check(update, client):
                return True
        return False


class Filters:
    """Built-in filter factory"""
    
    @staticmethod
    def chat_id(chat_id: int) -> ChatFilter:
        """Filter by chat ID"""
        return ChatFilter(chat_id)
    
    @staticmethod
    def user_id(user_id: int) -> UserFilter:
        """Filter by user ID"""
        return UserFilter(user_id)
    
    @staticmethod
    def status(status: str) -> StatusFilter:
        """Filter by status"""
        return StatusFilter(status)


def and_filter(*filters: BaseFilter) -> AndFilter:
    """Combine filters with AND logic"""
    return AndFilter(*filters)


def or_filter(*filters: BaseFilter) -> OrFilter:
    """Combine filters with OR logic"""
    return OrFilter(*filters)


class EventHandlerSystem:
    """Internal event handler system with filter support"""
    
    def __init__(self):
        """Initialize event handler system"""
        self.handlers: List[HandlerInfo] = []
        self.logger = logger
    
    def add_handler(
        self,
        func: Callable,
        filters: Optional[BaseFilter] = None,
        priority: int = 0
    ):
        """
        Add event handler with optional filters
        
        Args:
            func: Handler function
            filters: Optional filter to apply
            priority: Handler priority (higher = called first)
        """
        if not callable(func):
            raise TypeError("Handler must be callable")
        
        handler_info = HandlerInfo(
            func=func,
            filters=filters,
            priority=priority
        )
        
        # Insert in priority order (highest first)
        inserted = False
        for i, existing in enumerate(self.handlers):
            if priority > existing.priority:
                self.handlers.insert(i, handler_info)
                inserted = True
                break
        
        if not inserted:
            self.handlers.append(handler_info)
        
        self.logger.debug(f"Added handler {func.__name__} with priority {priority}")
    
    def remove_handler(self, func: Callable) -> bool:
        """
        Remove event handler
        
        Args:
            func: Handler function to remove
            
        Returns:
            True if handler was removed
        """
        for i, handler_info in enumerate(self.handlers):
            if handler_info.func == func:
                del self.handlers[i]
                self.logger.debug(f"Removed handler {func.__name__}")
                return True
        
        return False
    
    async def _propagate(self, update: Any, client: Any):
        """
        Propagate event to all matching handlers
        
        Args:
            update: Event update object
            client: Client instance
        """
        for handler_info in self.handlers:
            try:
                # Check filter if present
                if handler_info.filters:
                    if not await handler_info.filters.check(update, client):
                        continue
                
                # Call handler
                if asyncio.iscoroutinefunction(handler_info.func):
                    await handler_info.func(client, update)
                else:
                    handler_info.func(client, update)
                    
            except Exception as e:
                self.logger.error(
                    f"Error in handler {handler_info.func.__name__}: {e}"
                )
    
    def get_handlers_count(self) -> int:
        """Get number of registered handlers"""
        return len(self.handlers)
    
    def clear_handlers(self):
        """Clear all handlers"""
        self.handlers.clear()
        self.logger.debug("Cleared all handlers")