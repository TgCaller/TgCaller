"""
Network Ping Monitoring
"""

import asyncio
import logging
import time
import subprocess
import platform
from typing import Optional, List, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PingResult:
    """Ping result data"""
    host: str
    success: bool
    latency_ms: Optional[float]
    packet_loss: float
    timestamp: float
    error_message: Optional[str] = None


class PingMonitor:
    """Monitor network latency and connectivity"""
    
    def __init__(self, hosts: List[str] = None, interval: float = 30.0):
        self.hosts = hosts or [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "149.154.167.50",  # Telegram server
        ]
        self.interval = interval
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.callbacks: List[Callable[[List[PingResult]], None]] = []
        self.logger = logger
        
        # Results history
        self.results_history: List[List[PingResult]] = []
        self.max_history = 100
        
        # Statistics
        self.current_results: List[PingResult] = []
        
        # Platform-specific ping command
        self.ping_cmd = self._get_ping_command()
    
    def _get_ping_command(self) -> List[str]:
        """Get platform-specific ping command"""
        system = platform.system().lower()
        
        if system == "windows":
            return ["ping", "-n", "1", "-w", "3000"]  # 1 ping, 3s timeout
        else:
            return ["ping", "-c", "1", "-W", "3"]  # 1 ping, 3s timeout
    
    def add_callback(self, callback: Callable[[List[PingResult]], None]):
        """Add callback for ping results"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[List[PingResult]], None]):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start_monitoring(self) -> bool:
        """Start ping monitoring"""
        if self.monitoring:
            return True
        
        try:
            self.monitoring = True
            self.monitor_task = asyncio.create_task(self._monitor_loop())
            
            self.logger.info(f"Ping monitoring started for hosts: {self.hosts}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start ping monitoring: {e}")
            return False
    
    async def stop_monitoring(self):
        """Stop ping monitoring"""
        self.monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None
        
        self.logger.info("Ping monitoring stopped")
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Ping all hosts
                results = await self._ping_all_hosts()
                
                if results:
                    self.current_results = results
                    
                    # Add to history
                    self.results_history.append(results)
                    if len(self.results_history) > self.max_history:
                        self.results_history.pop(0)
                    
                    # Notify callbacks
                    for callback in self.callbacks:
                        try:
                            callback(results)
                        except Exception as e:
                            self.logger.error(f"Error in ping monitor callback: {e}")
                
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in ping monitoring loop: {e}")
                await asyncio.sleep(self.interval)
    
    async def _ping_all_hosts(self) -> List[PingResult]:
        """Ping all configured hosts"""
        tasks = [self._ping_host(host) for host in self.hosts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        ping_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                ping_results.append(PingResult(
                    host=self.hosts[i],
                    success=False,
                    latency_ms=None,
                    packet_loss=100.0,
                    timestamp=time.time(),
                    error_message=str(result)
                ))
            else:
                ping_results.append(result)
        
        return ping_results
    
    async def _ping_host(self, host: str) -> PingResult:
        """Ping a single host"""
        try:
            cmd = self.ping_cmd + [host]
            
            start_time = time.time()
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            end_time = time.time()
            
            if process.returncode == 0:
                # Parse latency from output
                latency = self._parse_latency(stdout.decode(), host)
                
                return PingResult(
                    host=host,
                    success=True,
                    latency_ms=latency,
                    packet_loss=0.0,
                    timestamp=end_time
                )
            else:
                return PingResult(
                    host=host,
                    success=False,
                    latency_ms=None,
                    packet_loss=100.0,
                    timestamp=end_time,
                    error_message=stderr.decode().strip()
                )
                
        except Exception as e:
            return PingResult(
                host=host,
                success=False,
                latency_ms=None,
                packet_loss=100.0,
                timestamp=time.time(),
                error_message=str(e)
            )
    
    def _parse_latency(self, output: str, host: str) -> Optional[float]:
        """Parse latency from ping output"""
        try:
            system = platform.system().lower()
            
            if system == "windows":
                # Windows: "time=1ms" or "time<1ms"
                import re
                match = re.search(r'time[<=](\d+)ms', output)
                if match:
                    return float(match.group(1))
            else:
                # Unix: "time=1.234 ms"
                import re
                match = re.search(r'time=([0-9.]+)\s*ms', output)
                if match:
                    return float(match.group(1))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing latency for {host}: {e}")
            return None
    
    async def ping_once(self, host: str) -> PingResult:
        """Ping a host once"""
        return await self._ping_host(host)
    
    def get_current_results(self) -> List[PingResult]:
        """Get current ping results"""
        return self.current_results.copy()
    
    def get_average_latency(self, host: str, samples: int = 10) -> Optional[float]:
        """Get average latency for host over last N samples"""
        if not self.results_history:
            return None
        
        recent_results = self.results_history[-samples:]
        latencies = []
        
        for results in recent_results:
            for result in results:
                if result.host == host and result.success and result.latency_ms:
                    latencies.append(result.latency_ms)
        
        if not latencies:
            return None
        
        return sum(latencies) / len(latencies)
    
    def get_packet_loss_rate(self, host: str, samples: int = 10) -> float:
        """Get packet loss rate for host over last N samples"""
        if not self.results_history:
            return 0.0
        
        recent_results = self.results_history[-samples:]
        total_pings = 0
        failed_pings = 0
        
        for results in recent_results:
            for result in results:
                if result.host == host:
                    total_pings += 1
                    if not result.success:
                        failed_pings += 1
        
        if total_pings == 0:
            return 0.0
        
        return (failed_pings / total_pings) * 100.0
    
    def get_best_host(self) -> Optional[str]:
        """Get host with best average latency"""
        if not self.current_results:
            return None
        
        best_host = None
        best_latency = float('inf')
        
        for result in self.current_results:
            if result.success and result.latency_ms and result.latency_ms < best_latency:
                best_latency = result.latency_ms
                best_host = result.host
        
        return best_host
    
    def is_network_healthy(self, max_latency: float = 200.0, max_loss: float = 5.0) -> bool:
        """Check if network is healthy based on thresholds"""
        if not self.current_results:
            return False
        
        successful_pings = [r for r in self.current_results if r.success]
        
        if not successful_pings:
            return False
        
        # Check if at least one host has good latency
        for result in successful_pings:
            if result.latency_ms and result.latency_ms <= max_latency:
                return True
        
        return False