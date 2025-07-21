"""
FastStreamBuffer - Ultra-low-latency streaming with async buffered chunks
"""

import asyncio
import logging
import time
from typing import Optional, Callable, List, Dict, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import deque
import numpy as np

logger = logging.getLogger(__name__)


class BufferState(Enum):
    """Buffer state enumeration"""
    IDLE = "idle"
    FILLING = "filling"
    READY = "ready"
    STREAMING = "streaming"
    UNDERRUN = "underrun"
    OVERFLOW = "overflow"
    ERROR = "error"


@dataclass
class StreamChunk:
    """Individual stream chunk data"""
    
    data: bytes
    """Raw chunk data"""
    
    timestamp: float
    """Chunk timestamp"""
    
    sequence: int
    """Sequence number"""
    
    chunk_type: str = "audio"
    """Chunk type (audio/video)"""
    
    duration_ms: float = 0.0
    """Chunk duration in milliseconds"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional chunk metadata"""
    
    @property
    def size(self) -> int:
        """Get chunk size in bytes"""
        return len(self.data)
    
    @property
    def age_ms(self) -> float:
        """Get chunk age in milliseconds"""
        return (time.time() - self.timestamp) * 1000


@dataclass
class BufferConfig:
    """FastStreamBuffer configuration"""
    
    # Buffer sizing
    max_buffer_size: int = 50
    """Maximum number of chunks to buffer"""
    
    min_buffer_size: int = 5
    """Minimum chunks before streaming starts"""
    
    target_buffer_size: int = 20
    """Target buffer size for optimal streaming"""
    
    # Timing
    chunk_duration_ms: float = 20.0
    """Target chunk duration in milliseconds"""
    
    max_latency_ms: float = 100.0
    """Maximum acceptable latency"""
    
    underrun_threshold: int = 3
    """Chunks remaining before underrun warning"""
    
    # Quality control
    adaptive_quality: bool = True
    """Enable adaptive quality based on buffer health"""
    
    drop_on_overflow: bool = True
    """Drop old chunks on buffer overflow"""
    
    prioritize_recent: bool = True
    """Prioritize recent chunks over old ones"""
    
    # Performance
    use_threading: bool = True
    """Use threading for buffer operations"""
    
    max_concurrent_chunks: int = 10
    """Maximum concurrent chunk processing"""


class FastStreamBuffer:
    """
    Ultra-low-latency streaming buffer with async chunk processing
    
    Features:
    - Async buffered chunk processing
    - Adaptive quality control
    - Underrun/overflow protection
    - Thread-safe operations
    - Real-time latency monitoring
    """
    
    def __init__(self, config: Optional[BufferConfig] = None):
        """
        Initialize FastStreamBuffer
        
        Args:
            config: Buffer configuration
        """
        self.config = config or BufferConfig()
        self.logger = logger
        
        # Buffer state
        self.state = BufferState.IDLE
        self.buffer: deque[StreamChunk] = deque(maxlen=self.config.max_buffer_size)
        self.sequence_counter = 0
        
        # Threading
        self.buffer_lock = threading.RLock() if self.config.use_threading else None
        self.producer_task: Optional[asyncio.Task] = None
        self.consumer_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.chunk_callbacks: List[Callable[[StreamChunk], None]] = []
        self.state_callbacks: List[Callable[[BufferState], None]] = []
        self.stats_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        
        # Statistics
        self.stats = {
            'chunks_produced': 0,
            'chunks_consumed': 0,
            'chunks_dropped': 0,
            'underruns': 0,
            'overflows': 0,
            'avg_latency_ms': 0.0,
            'buffer_health': 100.0,
            'throughput_mbps': 0.0
        }
        
        # Monitoring
        self.monitor_task: Optional[asyncio.Task] = None
        self.monitor_interval = 1.0
        
        # Quality adaptation
        self.quality_controller = QualityController(self)
    
    def add_chunk_callback(self, callback: Callable[[StreamChunk], None]):
        """Add callback for processed chunks"""
        self.chunk_callbacks.append(callback)
    
    def add_state_callback(self, callback: Callable[[BufferState], None]):
        """Add callback for state changes"""
        self.state_callbacks.append(callback)
    
    def add_stats_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add callback for statistics updates"""
        self.stats_callbacks.append(callback)
    
    async def start_buffering(self, source_generator: AsyncGenerator[bytes, None]) -> bool:
        """
        Start buffering from async source
        
        Args:
            source_generator: Async generator yielding raw data chunks
            
        Returns:
            True if buffering started successfully
        """
        if self.state != BufferState.IDLE:
            self.logger.warning("Buffer already active")
            return False
        
        try:
            self._set_state(BufferState.FILLING)
            
            # Start producer task
            self.producer_task = asyncio.create_task(
                self._producer_loop(source_generator)
            )
            
            # Start consumer task
            self.consumer_task = asyncio.create_task(
                self._consumer_loop()
            )
            
            # Start monitoring
            self.monitor_task = asyncio.create_task(
                self._monitor_loop()
            )
            
            self.logger.info("FastStreamBuffer started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start buffering: {e}")
            await self.stop_buffering()
            return False
    
    async def stop_buffering(self):
        """Stop buffering and cleanup"""
        try:
            self._set_state(BufferState.IDLE)
            
            # Cancel tasks
            for task in [self.producer_task, self.consumer_task, self.monitor_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Clear buffer
            with self._get_lock():
                self.buffer.clear()
                self.sequence_counter = 0
            
            self.logger.info("FastStreamBuffer stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping buffer: {e}")
    
    async def _producer_loop(self, source_generator: AsyncGenerator[bytes, None]):
        """Producer loop - fills buffer with chunks"""
        try:
            chunk_tasks = []
            
            async for raw_data in source_generator:
                if self.state == BufferState.IDLE:
                    break
                
                # Create chunk processing task
                if len(chunk_tasks) < self.config.max_concurrent_chunks:
                    task = asyncio.create_task(
                        self._process_raw_chunk(raw_data)
                    )
                    chunk_tasks.append(task)
                
                # Clean completed tasks
                chunk_tasks = [t for t in chunk_tasks if not t.done()]
                
                # Yield control
                await asyncio.sleep(0)
            
            # Wait for remaining tasks
            if chunk_tasks:
                await asyncio.gather(*chunk_tasks, return_exceptions=True)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Producer loop error: {e}")
            self._set_state(BufferState.ERROR)
    
    async def _process_raw_chunk(self, raw_data: bytes):
        """Process raw data into stream chunk"""
        try:
            # Create stream chunk
            chunk = StreamChunk(
                data=raw_data,
                timestamp=time.time(),
                sequence=self._get_next_sequence(),
                duration_ms=self.config.chunk_duration_ms
            )
            
            # Add to buffer
            await self._add_chunk_to_buffer(chunk)
            
            self.stats['chunks_produced'] += 1
            
        except Exception as e:
            self.logger.error(f"Error processing chunk: {e}")
    
    async def _add_chunk_to_buffer(self, chunk: StreamChunk):
        """Add chunk to buffer with overflow handling"""
        with self._get_lock():
            # Check for overflow
            if len(self.buffer) >= self.config.max_buffer_size:
                if self.config.drop_on_overflow:
                    # Drop oldest chunk
                    dropped = self.buffer.popleft()
                    self.stats['chunks_dropped'] += 1
                    self.stats['overflows'] += 1
                    
                    self.logger.debug(f"Dropped chunk {dropped.sequence} due to overflow")
                else:
                    # Skip adding new chunk
                    self.stats['chunks_dropped'] += 1
                    return
            
            # Add chunk
            self.buffer.append(chunk)
            
            # Update state based on buffer level
            buffer_level = len(self.buffer)
            
            if self.state == BufferState.FILLING and buffer_level >= self.config.min_buffer_size:
                self._set_state(BufferState.READY)
            elif buffer_level >= self.config.target_buffer_size:
                self._set_state(BufferState.STREAMING)
    
    async def _consumer_loop(self):
        """Consumer loop - processes buffered chunks"""
        try:
            while self.state != BufferState.IDLE:
                chunk = await self._get_next_chunk()
                
                if chunk:
                    # Process chunk
                    await self._process_chunk(chunk)
                    self.stats['chunks_consumed'] += 1
                else:
                    # No chunks available
                    await asyncio.sleep(0.001)  # 1ms
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Consumer loop error: {e}")
            self._set_state(BufferState.ERROR)
    
    async def _get_next_chunk(self) -> Optional[StreamChunk]:
        """Get next chunk from buffer"""
        with self._get_lock():
            if not self.buffer:
                # Check for underrun
                if self.state == BufferState.STREAMING:
                    self._set_state(BufferState.UNDERRUN)
                    self.stats['underruns'] += 1
                return None
            
            # Get chunk based on priority
            if self.config.prioritize_recent:
                chunk = self.buffer.pop()  # Get newest
            else:
                chunk = self.buffer.popleft()  # Get oldest
            
            # Update state based on remaining buffer
            remaining = len(self.buffer)
            
            if remaining <= self.config.underrun_threshold:
                if self.state == BufferState.STREAMING:
                    self._set_state(BufferState.UNDERRUN)
            elif remaining >= self.config.target_buffer_size:
                if self.state == BufferState.UNDERRUN:
                    self._set_state(BufferState.STREAMING)
            
            return chunk
    
    async def _process_chunk(self, chunk: StreamChunk):
        """Process individual chunk"""
        try:
            # Apply quality control
            if self.config.adaptive_quality:
                chunk = await self.quality_controller.process_chunk(chunk)
            
            # Calculate latency
            latency_ms = chunk.age_ms
            self._update_latency_stats(latency_ms)
            
            # Check latency threshold
            if latency_ms > self.config.max_latency_ms:
                self.logger.warning(f"High latency detected: {latency_ms:.1f}ms")
            
            # Notify callbacks
            for callback in self.chunk_callbacks:
                try:
                    callback(chunk)
                except Exception as e:
                    self.logger.error(f"Error in chunk callback: {e}")
            
        except Exception as e:
            self.logger.error(f"Error processing chunk {chunk.sequence}: {e}")
    
    async def _monitor_loop(self):
        """Monitor buffer health and performance"""
        try:
            while self.state != BufferState.IDLE:
                await self._update_statistics()
                await asyncio.sleep(self.monitor_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Monitor loop error: {e}")
    
    async def _update_statistics(self):
        """Update buffer statistics"""
        try:
            with self._get_lock():
                buffer_level = len(self.buffer)
                
                # Calculate buffer health (0-100%)
                health = min(100.0, (buffer_level / self.config.target_buffer_size) * 100)
                self.stats['buffer_health'] = health
                
                # Calculate throughput
                if self.stats['chunks_consumed'] > 0:
                    total_bytes = self.stats['chunks_consumed'] * self.config.chunk_duration_ms * 1024  # Estimate
                    throughput_mbps = (total_bytes * 8) / (1024 * 1024)  # Convert to Mbps
                    self.stats['throughput_mbps'] = throughput_mbps
            
            # Notify stats callbacks
            for callback in self.stats_callbacks:
                try:
                    callback(self.stats.copy())
                except Exception as e:
                    self.logger.error(f"Error in stats callback: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error updating statistics: {e}")
    
    def _update_latency_stats(self, latency_ms: float):
        """Update latency statistics"""
        current_avg = self.stats['avg_latency_ms']
        
        # Exponential moving average
        alpha = 0.1
        self.stats['avg_latency_ms'] = (alpha * latency_ms) + ((1 - alpha) * current_avg)
    
    def _set_state(self, new_state: BufferState):
        """Set buffer state and notify callbacks"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            
            self.logger.debug(f"Buffer state changed: {old_state.value} -> {new_state.value}")
            
            # Notify state callbacks
            for callback in self.state_callbacks:
                try:
                    callback(new_state)
                except Exception as e:
                    self.logger.error(f"Error in state callback: {e}")
    
    def _get_next_sequence(self) -> int:
        """Get next sequence number"""
        self.sequence_counter += 1
        return self.sequence_counter
    
    def _get_lock(self):
        """Get buffer lock (context manager)"""
        if self.buffer_lock:
            return self.buffer_lock
        else:
            # Dummy context manager for non-threaded mode
            class DummyLock:
                def __enter__(self): return self
                def __exit__(self, *args): pass
            return DummyLock()
    
    @property
    def buffer_level(self) -> int:
        """Get current buffer level"""
        with self._get_lock():
            return len(self.buffer)
    
    @property
    def buffer_health(self) -> float:
        """Get buffer health percentage"""
        return self.stats['buffer_health']
    
    @property
    def average_latency(self) -> float:
        """Get average latency in milliseconds"""
        return self.stats['avg_latency_ms']
    
    def get_buffer_info(self) -> Dict[str, Any]:
        """Get comprehensive buffer information"""
        with self._get_lock():
            return {
                'state': self.state.value,
                'buffer_level': len(self.buffer),
                'max_buffer_size': self.config.max_buffer_size,
                'target_size': self.config.target_buffer_size,
                'health_percent': self.stats['buffer_health'],
                'avg_latency_ms': self.stats['avg_latency_ms'],
                'chunks_in_buffer': len(self.buffer),
                'oldest_chunk_age': self.buffer[0].age_ms if self.buffer else 0,
                'newest_chunk_age': self.buffer[-1].age_ms if self.buffer else 0,
                'statistics': self.stats.copy()
            }


class QualityController:
    """Adaptive quality controller for stream chunks"""
    
    def __init__(self, buffer: FastStreamBuffer):
        self.buffer = buffer
        self.logger = logger
        
        # Quality levels
        self.quality_levels = {
            'ultra': {'bitrate_factor': 1.0, 'compression': 0.0},
            'high': {'bitrate_factor': 0.8, 'compression': 0.1},
            'medium': {'bitrate_factor': 0.6, 'compression': 0.2},
            'low': {'bitrate_factor': 0.4, 'compression': 0.3}
        }
        
        self.current_quality = 'high'
    
    async def process_chunk(self, chunk: StreamChunk) -> StreamChunk:
        """Process chunk with quality adaptation"""
        try:
            # Determine quality based on buffer health
            new_quality = self._determine_quality()
            
            if new_quality != self.current_quality:
                self.current_quality = new_quality
                self.logger.debug(f"Quality adapted to: {new_quality}")
            
            # Apply quality adjustments
            if self.current_quality != 'ultra':
                chunk = await self._apply_quality_adjustments(chunk)
            
            return chunk
            
        except Exception as e:
            self.logger.error(f"Error in quality control: {e}")
            return chunk
    
    def _determine_quality(self) -> str:
        """Determine appropriate quality level"""
        health = self.buffer.buffer_health
        latency = self.buffer.average_latency
        
        if health > 80 and latency < 50:
            return 'ultra'
        elif health > 60 and latency < 100:
            return 'high'
        elif health > 40 and latency < 200:
            return 'medium'
        else:
            return 'low'
    
    async def _apply_quality_adjustments(self, chunk: StreamChunk) -> StreamChunk:
        """Apply quality adjustments to chunk"""
        try:
            quality_config = self.quality_levels[self.current_quality]
            
            # Apply compression if needed
            if quality_config['compression'] > 0:
                chunk.data = await self._compress_chunk_data(
                    chunk.data, 
                    quality_config['compression']
                )
            
            # Update metadata
            chunk.metadata['quality_level'] = self.current_quality
            chunk.metadata['bitrate_factor'] = quality_config['bitrate_factor']
            
            return chunk
            
        except Exception as e:
            self.logger.error(f"Error applying quality adjustments: {e}")
            return chunk
    
    async def _compress_chunk_data(self, data: bytes, compression_level: float) -> bytes:
        """Apply compression to chunk data"""
        try:
            # Simple compression simulation
            # In real implementation, this would use actual audio/video compression
            compression_ratio = 1.0 - compression_level
            target_size = int(len(data) * compression_ratio)
            
            if target_size < len(data):
                # Simulate compression by truncating (not ideal, but for demo)
                return data[:target_size]
            
            return data
            
        except Exception as e:
            self.logger.error(f"Error compressing chunk data: {e}")
            return data