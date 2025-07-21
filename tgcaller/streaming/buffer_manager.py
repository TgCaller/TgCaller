"""
Buffer Manager - Centralized buffer management for multiple streams
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .fast_stream_buffer import FastStreamBuffer, BufferConfig, StreamChunk

logger = logging.getLogger(__name__)


@dataclass
class BufferStats:
    """Buffer statistics aggregation"""
    
    total_buffers: int = 0
    """Total number of active buffers"""
    
    healthy_buffers: int = 0
    """Number of healthy buffers"""
    
    underrun_buffers: int = 0
    """Number of buffers in underrun state"""
    
    overflow_buffers: int = 0
    """Number of buffers in overflow state"""
    
    avg_health: float = 0.0
    """Average buffer health percentage"""
    
    avg_latency: float = 0.0
    """Average latency across all buffers"""
    
    total_throughput: float = 0.0
    """Total throughput in Mbps"""
    
    memory_usage_mb: float = 0.0
    """Estimated memory usage in MB"""


class BufferPriority(Enum):
    """Buffer priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class BufferManager:
    """
    Centralized manager for multiple FastStreamBuffer instances
    
    Features:
    - Multi-stream buffer coordination
    - Resource allocation and prioritization
    - Global performance monitoring
    - Automatic buffer optimization
    - Memory management
    """
    
    def __init__(self, max_buffers: int = 10):
        """
        Initialize buffer manager
        
        Args:
            max_buffers: Maximum number of concurrent buffers
        """
        self.max_buffers = max_buffers
        self.logger = logger
        
        # Buffer registry
        self.buffers: Dict[str, FastStreamBuffer] = {}
        self.buffer_priorities: Dict[str, BufferPriority] = {}
        self.buffer_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Global configuration
        self.global_config = BufferConfig()
        
        # Monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.monitor_interval = 2.0
        self.is_monitoring = False
        
        # Statistics
        self.global_stats = BufferStats()
        self.stats_callbacks: List[Callable[[BufferStats], None]] = []
        
        # Resource management
        self.memory_limit_mb = 500.0
        self.cpu_limit_percent = 80.0
        
        # Performance optimization
        self.auto_optimize = True
        self.optimization_interval = 30.0
        self.last_optimization = 0.0
    
    async def create_buffer(
        self,
        buffer_id: str,
        config: Optional[BufferConfig] = None,
        priority: BufferPriority = BufferPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[FastStreamBuffer]:
        """
        Create new buffer instance
        
        Args:
            buffer_id: Unique buffer identifier
            config: Buffer configuration
            priority: Buffer priority level
            metadata: Additional buffer metadata
            
        Returns:
            FastStreamBuffer instance or None if creation failed
        """
        if len(self.buffers) >= self.max_buffers:
            self.logger.warning(f"Maximum buffer limit reached: {self.max_buffers}")
            
            # Try to free low-priority buffers
            if not await self._free_low_priority_buffer():
                return None
        
        if buffer_id in self.buffers:
            self.logger.warning(f"Buffer {buffer_id} already exists")
            return self.buffers[buffer_id]
        
        try:
            # Use provided config or global default
            buffer_config = config or self._create_adaptive_config(priority)
            
            # Create buffer
            buffer = FastStreamBuffer(buffer_config)
            
            # Register buffer
            self.buffers[buffer_id] = buffer
            self.buffer_priorities[buffer_id] = priority
            self.buffer_metadata[buffer_id] = metadata or {}
            
            # Setup buffer callbacks
            self._setup_buffer_callbacks(buffer_id, buffer)
            
            # Start monitoring if first buffer
            if len(self.buffers) == 1 and not self.is_monitoring:
                await self.start_monitoring()
            
            self.logger.info(f"Created buffer {buffer_id} with priority {priority.name}")
            return buffer
            
        except Exception as e:
            self.logger.error(f"Failed to create buffer {buffer_id}: {e}")
            return None
    
    async def remove_buffer(self, buffer_id: str) -> bool:
        """Remove buffer instance"""
        if buffer_id not in self.buffers:
            return False
        
        try:
            buffer = self.buffers[buffer_id]
            
            # Stop buffer
            await buffer.stop_buffering()
            
            # Remove from registry
            del self.buffers[buffer_id]
            del self.buffer_priorities[buffer_id]
            del self.buffer_metadata[buffer_id]
            
            # Stop monitoring if no buffers left
            if not self.buffers and self.is_monitoring:
                await self.stop_monitoring()
            
            self.logger.info(f"Removed buffer {buffer_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing buffer {buffer_id}: {e}")
            return False
    
    def get_buffer(self, buffer_id: str) -> Optional[FastStreamBuffer]:
        """Get buffer by ID"""
        return self.buffers.get(buffer_id)
    
    def list_buffers(self) -> List[str]:
        """Get list of active buffer IDs"""
        return list(self.buffers.keys())
    
    def get_buffer_count(self) -> int:
        """Get number of active buffers"""
        return len(self.buffers)
    
    async def start_monitoring(self):
        """Start global buffer monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Buffer monitoring started")
    
    async def stop_monitoring(self):
        """Stop global buffer monitoring"""
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            self.monitor_task = None
        
        self.logger.info("Buffer monitoring stopped")
    
    async def _monitor_loop(self):
        """Global monitoring loop"""
        try:
            while self.is_monitoring:
                await self._update_global_stats()
                
                # Perform optimization if needed
                if self.auto_optimize:
                    await self._check_optimization_needed()
                
                await asyncio.sleep(self.monitor_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error in buffer monitoring loop: {e}")
    
    async def _update_global_stats(self):
        """Update global buffer statistics"""
        try:
            stats = BufferStats()
            
            if not self.buffers:
                self.global_stats = stats
                return
            
            # Aggregate statistics
            total_health = 0.0
            total_latency = 0.0
            total_throughput = 0.0
            memory_usage = 0.0
            
            for buffer_id, buffer in self.buffers.items():
                buffer_info = buffer.get_buffer_info()
                
                stats.total_buffers += 1
                
                # Health categorization
                health = buffer_info['health_percent']
                if health > 70:
                    stats.healthy_buffers += 1
                elif buffer_info['state'] == 'underrun':
                    stats.underrun_buffers += 1
                elif buffer_info['state'] == 'overflow':
                    stats.overflow_buffers += 1
                
                # Accumulate metrics
                total_health += health
                total_latency += buffer_info['avg_latency_ms']
                total_throughput += buffer_info['statistics'].get('throughput_mbps', 0)
                
                # Estimate memory usage
                memory_usage += buffer_info['chunks_in_buffer'] * 0.1  # Rough estimate
            
            # Calculate averages
            if stats.total_buffers > 0:
                stats.avg_health = total_health / stats.total_buffers
                stats.avg_latency = total_latency / stats.total_buffers
            
            stats.total_throughput = total_throughput
            stats.memory_usage_mb = memory_usage
            
            self.global_stats = stats
            
            # Notify callbacks
            for callback in self.stats_callbacks:
                try:
                    callback(stats)
                except Exception as e:
                    self.logger.error(f"Error in stats callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error updating global stats: {e}")
    
    async def _check_optimization_needed(self):
        """Check if buffer optimization is needed"""
        current_time = asyncio.get_event_loop().time()
        
        if current_time - self.last_optimization < self.optimization_interval:
            return
        
        # Check if optimization is needed
        needs_optimization = (
            self.global_stats.avg_health < 60 or
            self.global_stats.avg_latency > 150 or
            self.global_stats.underrun_buffers > 0 or
            self.global_stats.memory_usage_mb > self.memory_limit_mb
        )
        
        if needs_optimization:
            await self._optimize_buffers()
            self.last_optimization = current_time
    
    async def _optimize_buffers(self):
        """Optimize buffer configurations"""
        try:
            self.logger.info("Starting buffer optimization")
            
            for buffer_id, buffer in self.buffers.items():
                priority = self.buffer_priorities[buffer_id]
                buffer_info = buffer.get_buffer_info()
                
                # Optimize based on current performance
                if buffer_info['health_percent'] < 50:
                    # Increase buffer size for struggling buffers
                    await self._adjust_buffer_size(buffer_id, increase=True)
                elif buffer_info['health_percent'] > 90 and priority == BufferPriority.LOW:
                    # Decrease buffer size for over-performing low-priority buffers
                    await self._adjust_buffer_size(buffer_id, increase=False)
                
                # Adjust quality based on latency
                if buffer_info['avg_latency_ms'] > 200:
                    await self._adjust_buffer_quality(buffer_id, decrease=True)
            
            self.logger.info("Buffer optimization completed")
            
        except Exception as e:
            self.logger.error(f"Error during buffer optimization: {e}")
    
    async def _adjust_buffer_size(self, buffer_id: str, increase: bool):
        """Adjust buffer size for optimization"""
        try:
            buffer = self.buffers[buffer_id]
            current_size = buffer.config.max_buffer_size
            
            if increase:
                new_size = min(current_size + 20, 200)
            else:
                new_size = max(current_size - 10, 20)
            
            if new_size != current_size:
                buffer.config.max_buffer_size = new_size
                buffer.config.target_buffer_size = int(new_size * 0.6)
                
                self.logger.debug(f"Adjusted buffer {buffer_id} size: {current_size} -> {new_size}")
                
        except Exception as e:
            self.logger.error(f"Error adjusting buffer size for {buffer_id}: {e}")
    
    async def _adjust_buffer_quality(self, buffer_id: str, decrease: bool):
        """Adjust buffer quality settings"""
        try:
            buffer = self.buffers[buffer_id]
            
            if decrease:
                # Reduce quality to improve performance
                buffer.config.max_latency_ms = min(buffer.config.max_latency_ms + 20, 300)
                buffer.config.chunk_duration_ms = min(buffer.config.chunk_duration_ms + 5, 50)
            else:
                # Increase quality
                buffer.config.max_latency_ms = max(buffer.config.max_latency_ms - 20, 50)
                buffer.config.chunk_duration_ms = max(buffer.config.chunk_duration_ms - 5, 10)
            
            self.logger.debug(f"Adjusted buffer {buffer_id} quality settings")
            
        except Exception as e:
            self.logger.error(f"Error adjusting buffer quality for {buffer_id}: {e}")
    
    async def _free_low_priority_buffer(self) -> bool:
        """Free lowest priority buffer to make space"""
        try:
            # Find lowest priority buffer
            lowest_priority = BufferPriority.CRITICAL
            lowest_buffer_id = None
            
            for buffer_id, priority in self.buffer_priorities.items():
                if priority.value < lowest_priority.value:
                    lowest_priority = priority
                    lowest_buffer_id = buffer_id
            
            if lowest_buffer_id and lowest_priority != BufferPriority.CRITICAL:
                await self.remove_buffer(lowest_buffer_id)
                self.logger.info(f"Freed low-priority buffer {lowest_buffer_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error freeing low-priority buffer: {e}")
            return False
    
    def _create_adaptive_config(self, priority: BufferPriority) -> BufferConfig:
        """Create adaptive buffer configuration based on priority"""
        base_config = BufferConfig()
        
        # Adjust settings based on priority
        if priority == BufferPriority.CRITICAL:
            base_config.max_buffer_size = 100
            base_config.target_buffer_size = 40
            base_config.max_latency_ms = 50.0
            base_config.chunk_duration_ms = 10.0
        elif priority == BufferPriority.HIGH:
            base_config.max_buffer_size = 80
            base_config.target_buffer_size = 30
            base_config.max_latency_ms = 80.0
            base_config.chunk_duration_ms = 15.0
        elif priority == BufferPriority.NORMAL:
            base_config.max_buffer_size = 50
            base_config.target_buffer_size = 20
            base_config.max_latency_ms = 100.0
            base_config.chunk_duration_ms = 20.0
        else:  # LOW
            base_config.max_buffer_size = 30
            base_config.target_buffer_size = 10
            base_config.max_latency_ms = 200.0
            base_config.chunk_duration_ms = 30.0
        
        return base_config
    
    def _setup_buffer_callbacks(self, buffer_id: str, buffer: FastStreamBuffer):
        """Setup callbacks for individual buffer"""
        def on_buffer_state_change(state):
            """Handle buffer state changes"""
            self.logger.debug(f"Buffer {buffer_id} state changed to {state.value}")
            
            # Update metadata
            self.buffer_metadata[buffer_id]['last_state'] = state.value
            self.buffer_metadata[buffer_id]['last_state_time'] = asyncio.get_event_loop().time()
        
        def on_buffer_stats_update(stats):
            """Handle buffer statistics updates"""
            # Store latest stats in metadata
            self.buffer_metadata[buffer_id]['latest_stats'] = stats
        
        # Register callbacks
        buffer.add_state_callback(on_buffer_state_change)
        buffer.add_stats_callback(on_buffer_stats_update)
    
    def add_stats_callback(self, callback: Callable[[BufferStats], None]):
        """Add callback for global statistics updates"""
        self.stats_callbacks.append(callback)
    
    def remove_stats_callback(self, callback: Callable[[BufferStats], None]):
        """Remove statistics callback"""
        if callback in self.stats_callbacks:
            self.stats_callbacks.remove(callback)
    
    def get_global_stats(self) -> BufferStats:
        """Get global buffer statistics"""
        return self.global_stats
    
    def get_buffer_info(self, buffer_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about specific buffer"""
        if buffer_id not in self.buffers:
            return None
        
        buffer = self.buffers[buffer_id]
        priority = self.buffer_priorities[buffer_id]
        metadata = self.buffer_metadata[buffer_id]
        
        info = buffer.get_buffer_info()
        info.update({
            'buffer_id': buffer_id,
            'priority': priority.name,
            'metadata': metadata
        })
        
        return info
    
    async def cleanup_all(self):
        """Cleanup all buffers and stop monitoring"""
        try:
            # Stop monitoring
            await self.stop_monitoring()
            
            # Remove all buffers
            for buffer_id in list(self.buffers.keys()):
                await self.remove_buffer(buffer_id)
            
            self.logger.info("Buffer manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")