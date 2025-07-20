"""
Retry Manager - Handle operation retries with exponential backoff
"""

import asyncio
import logging
from typing import Dict, Callable, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    """Retry strategy types"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_factor: float = 2.0
    jitter: bool = True


class RetryManager:
    """Manage operation retries with various strategies"""
    
    def __init__(self):
        self.retry_counts: Dict[str, int] = {}
        self.logger = logger
    
    async def retry_operation(
        self,
        operation: Callable,
        operation_id: str,
        config: Optional[RetryConfig] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Retry operation with specified strategy
        
        Args:
            operation: Function to retry
            operation_id: Unique identifier for operation
            config: Retry configuration
            *args: Arguments for operation
            **kwargs: Keyword arguments for operation
            
        Returns:
            Operation result
            
        Raises:
            Exception: Last exception if all retries failed
        """
        if config is None:
            config = RetryConfig()
        
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                # Track retry count
                self.retry_counts[operation_id] = attempt
                
                # Execute operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                # Success - clear retry count
                self.retry_counts.pop(operation_id, None)
                
                if attempt > 0:
                    self.logger.info(f"Operation {operation_id} succeeded on attempt {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, config)
                    
                    self.logger.warning(
                        f"Operation {operation_id} failed (attempt {attempt + 1}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        f"Operation {operation_id} failed after {config.max_attempts} attempts: {e}"
                    )
        
        # All retries failed
        self.retry_counts.pop(operation_id, None)
        raise last_exception
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.backoff_factor ** attempt)
        else:
            delay = config.base_delay
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            import random
            jitter_factor = random.uniform(0.8, 1.2)
            delay *= jitter_factor
        
        return delay
    
    def get_retry_count(self, operation_id: str) -> int:
        """Get current retry count for operation"""
        return self.retry_counts.get(operation_id, 0)
    
    def is_retrying(self, operation_id: str) -> bool:
        """Check if operation is currently retrying"""
        return operation_id in self.retry_counts
    
    def cancel_retries(self, operation_id: str) -> bool:
        """Cancel retries for operation"""
        if operation_id in self.retry_counts:
            del self.retry_counts[operation_id]
            return True
        return False
    
    def get_active_retries(self) -> Dict[str, int]:
        """Get all active retry operations"""
        return self.retry_counts.copy()
    
    def clear_all_retries(self) -> None:
        """Clear all retry tracking"""
        self.retry_counts.clear()


# Convenience functions for common retry patterns
async def retry_connection(operation: Callable, *args, **kwargs) -> Any:
    """Retry connection operations with connection-specific config"""
    config = RetryConfig(
        max_attempts=5,
        base_delay=2.0,
        max_delay=30.0,
        strategy=RetryStrategy.EXPONENTIAL
    )
    
    retry_manager = RetryManager()
    return await retry_manager.retry_operation(
        operation, 
        f"connection_{id(operation)}", 
        config, 
        *args, 
        **kwargs
    )


async def retry_stream_operation(operation: Callable, *args, **kwargs) -> Any:
    """Retry stream operations with stream-specific config"""
    config = RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        strategy=RetryStrategy.LINEAR
    )
    
    retry_manager = RetryManager()
    return await retry_manager.retry_operation(
        operation, 
        f"stream_{id(operation)}", 
        config, 
        *args, 
        **kwargs
    )


async def retry_api_call(operation: Callable, *args, **kwargs) -> Any:
    """Retry API calls with API-specific config"""
    config = RetryConfig(
        max_attempts=4,
        base_delay=0.5,
        max_delay=15.0,
        strategy=RetryStrategy.EXPONENTIAL,
        backoff_factor=1.5
    )
    
    retry_manager = RetryManager()
    return await retry_manager.retry_operation(
        operation, 
        f"api_{id(operation)}", 
        config, 
        *args, 
        **kwargs
    )