"""
CPU Usage Monitoring
"""

import asyncio
import logging
from typing import Dict, Optional, Callable
from dataclasses import dataclass

try:
    import psutil
except ImportError:  # psutil is an optional platform-dependent extra.
    psutil = None

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

        self.current_stats: Optional[CpuStats] = None
        self.history: list = []
        self.max_history = 100

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
        """Start CPU monitoring when the optional psutil dependency is available."""
        if self.monitoring:
            return True
        if psutil is None:
            self.logger.warning(
                "CPU monitoring is unavailable; install the optional "
                "'tgcaller[monitoring]' extra on a supported platform."
            )
            return False

        try:
            self.monitoring = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            self.logger.info("CPU monitoring started")
            return True
        except Exception as e:
            self.monitoring = False
            self.logger.error("Failed to start CPU monitoring: %s", e)
            return False

    async def stop_monitoring(self):
        """Stop CPU monitoring and await task cleanup."""
        self.monitoring = False
        task = self.monitor_task
        self.monitor_task = None
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.logger.info("CPU monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                stats = await self._collect_stats()
                if stats:
                    self.current_stats = stats
                    self.history.append(stats)
                    if len(self.history) > self.max_history:
                        self.history.pop(0)
                    await self._check_thresholds(stats)
                    for callback in self.callbacks:
                        try:
                            callback(stats)
                        except Exception as e:
                            self.logger.error("Error in CPU monitor callback: %s", e)
                await asyncio.sleep(self.update_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("Error in CPU monitoring loop: %s", e)
                await asyncio.sleep(self.update_interval)

    async def _collect_stats(self) -> Optional[CpuStats]:
        """Collect CPU and memory statistics, if psutil is available."""
        if psutil is None:
            return None
        try:
            loop = asyncio.get_running_loop()
            overall_cpu = await loop.run_in_executor(None, psutil.cpu_percent, 1.0)
            per_core = await loop.run_in_executor(None, psutil.cpu_percent, 1.0, True)
            try:
                load_avg = psutil.getloadavg()
            except (AttributeError, OSError):
                load_avg = (0.0, 0.0, 0.0)

            process = psutil.Process()
            process_cpu = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            return CpuStats(
                overall_percent=overall_cpu,
                per_core=per_core,
                load_average=load_avg,
                process_percent=process_cpu,
                memory_percent=memory_percent,
                memory_mb=memory_info.rss / 1024 / 1024,
            )
        except Exception as e:
            self.logger.error("Error collecting CPU stats: %s", e)
            return None

    async def _check_thresholds(self, stats: CpuStats):
        """Check if stats exceed warning thresholds"""
        try:
            if stats.overall_percent > self.cpu_warning_threshold:
                self.logger.warning(
                    "High CPU usage detected: %.1f%%", stats.overall_percent
                )
            if stats.memory_percent > self.memory_warning_threshold:
                self.logger.warning(
                    "High memory usage detected: %.1f%% (%.1f MB)",
                    stats.memory_percent,
                    stats.memory_mb,
                )
            if stats.process_percent > 50.0:
                self.logger.warning(
                    "TgCaller process using high CPU: %.1f%%", stats.process_percent
                )
        except Exception as e:
            self.logger.error("Error checking thresholds: %s", e)

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
        return sum(stats.overall_percent for stats in recent_history) / len(recent_history)

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
        return self.current_stats.memory_mb if self.current_stats else None

    def set_warning_thresholds(self, cpu_threshold: float, memory_threshold: float):
        """Set warning thresholds"""
        self.cpu_warning_threshold = cpu_threshold
        self.memory_warning_threshold = memory_threshold
        self.logger.info(
            "Updated thresholds: CPU %.1f%%, Memory %.1f%%",
            cpu_threshold,
            memory_threshold,
        )
