"""
CPU Usage Monitoring
"""

import asyncio
import logging
import psutil
from typing import Dict, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CpuStats:
    """CPU usage statistics"""
    overall_percent: float
    per_core: list
    load_average: tuple
    process_percent: float
    memory_percent: float
    memory_mb: float


class CpuMonitor:
    """Monitor CPU usage for TgCaller operations"""
    
    def __init__(self, update_interval: float = 5.0):
        self.update_interval = update_interval
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.callbacks: list = []
        self.logger = logger
        
        # Statistics
        self.current_stats: Optional[CpuStats] = None
        self.history: list = []
        self.max_history = 100
        
        # Thresholds
        self.cpu_warning_threshold = 80.0
        self.memory_warning_threshold = 80.0
    
    def add_callback(self, callback: Callable[[CpuStats], None]):
        """Add callback for CPU stats updates"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[CpuStats], None]):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start_monitoring(self) -> bool:
        """Start CPU monitoring"""
        if self.monitoring:
            return True
        
        try:
            self.monitoring = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.logger.info("CPU monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start CPU monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop CPU monitoring"""
        self.monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None
        
        self.logger.info("CPU monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect CPU stats
                stats = await self._collect_stats()
                
                if stats:
                    self.current_stats = stats
                    
                    # Add to history
                    self.history.append(stats)
                    if len(self.history) > self.max_history:
                        self.history.pop(0)
                    
                    # Check thresholds
                    await self._check_thresholds(stats)
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(stats)
                        except Exception as e:
                            self.logger.error(f"Error in CPU monitor callback: {e}")
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in CPU monitoring loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _collect_stats(self) -> Optional[CpuStats]:
        """Collect CPU and memory statistics"""
        try:
            # Run CPU-intensive operations in thread pool
            loop = asyncio.get_event_loop()
            
            # Get overall CPU usage
            overall_cpu = await loop.run_in_executor(
                None, psutil.cpu_percent, 1.0
            )
            
            # Get per-core usage
            per_core = await loop.run_in_executor(
                None, psutil.cpu_percent, 1.0, True
            )
            
            # Get load average (Unix only)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = (0.0, 0.0, 0.0)  # Windows doesn't have load average
            
            # Get current process stats
            process = psutil.Process()
            process_cpu = process.cpu_percent()
            
            # Get memory stats
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            memory_mb = memory_info.rss / 1024 / 1024
            
            return CpuStats(
                overall_percent=overall_cpu,
                per_core=per_core,
                load_average=load_avg,
                process_percent=process_cpu,
                memory_percent=memory_percent,
                memory_mb=memory_mb
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting CPU stats: {e}")
            return None
    
    async def _check_thresholds(self, stats: CpuStats):
        """Check if stats exceed warning thresholds"""
        try:
            if stats.overall_percent > self.cpu_warning_threshold:
                self.logger.warning(
                    f"High CPU usage detected: {stats.overall_percent:.1f}%"
                )
            
            if stats.memory_percent > self.memory_warning_threshold:
                self.logger.warning(
                    f"High memory usage detected: {stats.memory_percent:.1f}% "
                    f"({stats.memory_mb:.1f} MB)"
                )
            
            if stats.process_percent > 50.0:
                self.logger.warning(
                    f"TgCaller process using high CPU: {stats.process_percent:.1f}%"
                )
                
        except Exception as e:
            self.logger.error(f"Error checking thresholds: {e}")
    
    def get_current_stats(self) -> Optional[CpuStats]:
        """Get current CPU statistics"""
        return self.current_stats
    
    def get_average_cpu(self, samples: int = 10) -> Optional[float]:
        """Get average CPU usage over last N samples"""
        if not self.history:
            return None
        
        recent_history = self.history[-samples:]
        if not recent_history:
            return None
        
        total_cpu = sum(stats.overall_percent for stats in recent_history)
        return total_cpu / len(recent_history)
    
    def get_peak_cpu(self, samples: int = 10) -> Optional[float]:
        """Get peak CPU usage over last N samples"""
        if not self.history:
            return None
        
        recent_history = self.history[-samples:]
        if not recent_history:
            return None
        
        return max(stats.overall_percent for stats in recent_history)
    
    def get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB"""
        if self.current_stats:
            return self.current_stats.memory_mb
        return None
    
    def set_warning_thresholds(self, cpu_threshold: float, memory_threshold: float):
        """Set warning thresholds"""
        self.cpu_warning_threshold = cpu_threshold
        self.memory_warning_threshold = memory_threshold
        
        self.logger.info(
            f"Updated thresholds: CPU {cpu_threshold}%, Memory {memory_threshold}%"
        )