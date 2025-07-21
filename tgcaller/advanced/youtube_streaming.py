"""
Advanced YouTube Streaming with FastStreamBuffer Integration
"""

import asyncio
import logging
from typing import Optional, Dict, Any

from ..streaming import FastStreamBuffer, YouTubeStreamer, YouTubeStreamConfig, BufferManager, BufferPriority
from ..types import AudioConfig, VideoConfig

logger = logging.getLogger(__name__)


class AdvancedYouTubeStreamer:
    """
    Advanced YouTube streamer with ultra-low-latency capabilities
    
    Features:
    - FastStreamBuffer integration
    - Multi-quality adaptive streaming
    - Buffer management and optimization
    - Real-time performance monitoring
    """
    
    def __init__(self, caller, buffer_manager: Optional[BufferManager] = None):
        """
        Initialize advanced YouTube streamer
        
        Args:
            caller: TgCaller instance
            buffer_manager: Optional buffer manager instance
        """
        self.caller = caller
        self.buffer_manager = buffer_manager or BufferManager(max_buffers=5)
        self.logger = logger
        
        # Active streams
        self.active_streams: Dict[int, YouTubeStreamer] = {}
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
    
    async def stream_youtube_ultra_low_latency(
        self,
        chat_id: int,
        url: str,
        quality: str = "720p",
        audio_config: Optional[AudioConfig] = None,
        video_config: Optional[VideoConfig] = None
    ) -> bool:
        """
        Stream YouTube with ultra-low latency optimization
        
        Args:
            chat_id: Target chat ID
            url: YouTube URL
            quality: Stream quality (720p, 1080p, etc.)
            audio_config: Audio configuration
            video_config: Video configuration
            
        Returns:
            True if streaming started successfully
        """
        try:
            # Stop existing stream if any
            if chat_id in self.active_streams:
                await self.stop_stream(chat_id)
            
            # Create optimized configuration
            stream_config = self._create_optimized_config(quality)
            
            # Create YouTube streamer
            streamer = YouTubeStreamer(self.caller, stream_config)
            
            # Start streaming
            success = await streamer.stream_youtube_url(
                chat_id, url, audio_config, video_config
            )
            
            if success:
                self.active_streams[chat_id] = streamer
                
                # Start performance monitoring
                await self.performance_monitor.start_monitoring(chat_id, streamer)
                
                self.logger.info(f"Started ultra-low-latency YouTube streaming for chat {chat_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start ultra-low-latency streaming: {e}")
            return False
    
    async def stop_stream(self, chat_id: int) -> bool:
        """Stop YouTube stream"""
        if chat_id not in self.active_streams:
            return False
        
        try:
            streamer = self.active_streams[chat_id]
            await streamer.stop_streaming()
            
            # Stop monitoring
            await self.performance_monitor.stop_monitoring(chat_id)
            
            del self.active_streams[chat_id]
            
            self.logger.info(f"Stopped YouTube streaming for chat {chat_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping stream for chat {chat_id}: {e}")
            return False
    
    def _create_optimized_config(self, quality: str) -> YouTubeStreamConfig:
        """Create optimized streaming configuration"""
        # Quality-specific settings
        quality_settings = {
            "480p": {
                "video_quality": "best[height<=480]",
                "max_buffer_size": 40,
                "target_buffer_size": 15,
                "chunk_duration_ms": 25.0,
                "max_latency_ms": 120.0
            },
            "720p": {
                "video_quality": "best[height<=720]",
                "max_buffer_size": 60,
                "target_buffer_size": 25,
                "chunk_duration_ms": 20.0,
                "max_latency_ms": 100.0
            },
            "1080p": {
                "video_quality": "best[height<=1080]",
                "max_buffer_size": 80,
                "target_buffer_size": 35,
                "chunk_duration_ms": 15.0,
                "max_latency_ms": 80.0
            }
        }
        
        settings = quality_settings.get(quality, quality_settings["720p"])
        
        # Create buffer configuration
        from ..streaming.fast_stream_buffer import BufferConfig
        buffer_config = BufferConfig(
            max_buffer_size=settings["max_buffer_size"],
            target_buffer_size=settings["target_buffer_size"],
            chunk_duration_ms=settings["chunk_duration_ms"],
            max_latency_ms=settings["max_latency_ms"],
            adaptive_quality=True,
            use_threading=True
        )
        
        # Create stream configuration
        return YouTubeStreamConfig(
            video_quality=settings["video_quality"],
            buffer_config=buffer_config,
            ffmpeg_options={
                'before_options': '-re -fflags +genpts -probesize 32 -analyzeduration 0',
                'options': '-f s16le -ar 48000 -ac 2 -bufsize 64k'
            },
            chunk_size=4096,  # Smaller chunks for lower latency
            use_hardware_acceleration=True
        )
    
    def get_stream_stats(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get streaming statistics for chat"""
        if chat_id not in self.active_streams:
            return None
        
        streamer = self.active_streams[chat_id]
        return streamer.get_streaming_stats()
    
    def get_all_streams_stats(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all active streams"""
        return {
            chat_id: streamer.get_streaming_stats()
            for chat_id, streamer in self.active_streams.items()
        }
    
    async def cleanup(self):
        """Cleanup all streams and resources"""
        try:
            # Stop all streams
            for chat_id in list(self.active_streams.keys()):
                await self.stop_stream(chat_id)
            
            # Cleanup buffer manager
            await self.buffer_manager.cleanup_all()
            
            # Stop performance monitoring
            await self.performance_monitor.cleanup()
            
            self.logger.info("Advanced YouTube streamer cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


class PerformanceMonitor:
    """Monitor streaming performance and optimize in real-time"""
    
    def __init__(self):
        self.logger = logger
        self.monitoring_tasks: Dict[int, asyncio.Task] = {}
        self.performance_data: Dict[int, Dict[str, Any]] = {}
    
    async def start_monitoring(self, chat_id: int, streamer: YouTubeStreamer):
        """Start monitoring for specific stream"""
        if chat_id in self.monitoring_tasks:
            return
        
        self.monitoring_tasks[chat_id] = asyncio.create_task(
            self._monitor_stream_performance(chat_id, streamer)
        )
        
        self.logger.info(f"Started performance monitoring for chat {chat_id}")
    
    async def stop_monitoring(self, chat_id: int):
        """Stop monitoring for specific stream"""
        if chat_id in self.monitoring_tasks:
            self.monitoring_tasks[chat_id].cancel()
            try:
                await self.monitoring_tasks[chat_id]
            except asyncio.CancelledError:
                pass
            
            del self.monitoring_tasks[chat_id]
            self.performance_data.pop(chat_id, None)
            
            self.logger.info(f"Stopped performance monitoring for chat {chat_id}")
    
    async def _monitor_stream_performance(self, chat_id: int, streamer: YouTubeStreamer):
        """Monitor stream performance"""
        try:
            while True:
                # Collect performance metrics
                stats = streamer.get_streaming_stats()
                
                # Analyze performance
                analysis = self._analyze_performance(stats)
                
                # Store data
                self.performance_data[chat_id] = {
                    'stats': stats,
                    'analysis': analysis,
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                # Apply optimizations if needed
                if analysis['needs_optimization']:
                    await self._apply_optimizations(chat_id, streamer, analysis)
                
                await asyncio.sleep(5.0)  # Monitor every 5 seconds
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error monitoring performance for chat {chat_id}: {e}")
    
    def _analyze_performance(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance metrics"""
        analysis = {
            'needs_optimization': False,
            'issues': [],
            'recommendations': []
        }
        
        # Check buffer health
        buffer_health = stats.get('health_percent', 0)
        if buffer_health < 60:
            analysis['needs_optimization'] = True
            analysis['issues'].append('low_buffer_health')
            analysis['recommendations'].append('increase_buffer_size')
        
        # Check latency
        avg_latency = stats.get('avg_latency_ms', 0)
        if avg_latency > 150:
            analysis['needs_optimization'] = True
            analysis['issues'].append('high_latency')
            analysis['recommendations'].append('reduce_quality')
        
        # Check underruns
        underruns = stats.get('buffer_underruns', 0)
        if underruns > 5:
            analysis['needs_optimization'] = True
            analysis['issues'].append('frequent_underruns')
            analysis['recommendations'].append('increase_buffer_target')
        
        return analysis
    
    async def _apply_optimizations(
        self, 
        chat_id: int, 
        streamer: YouTubeStreamer, 
        analysis: Dict[str, Any]
    ):
        """Apply performance optimizations"""
        try:
            recommendations = analysis['recommendations']
            
            if 'increase_buffer_size' in recommendations:
                # Increase buffer size
                if streamer.buffer:
                    current_size = streamer.buffer.config.max_buffer_size
                    new_size = min(current_size + 20, 150)
                    streamer.buffer.config.max_buffer_size = new_size
                    
                    self.logger.info(f"Increased buffer size for chat {chat_id}: {current_size} -> {new_size}")
            
            if 'reduce_quality' in recommendations:
                # Reduce quality settings
                if streamer.buffer:
                    streamer.buffer.config.max_latency_ms += 20
                    streamer.buffer.config.chunk_duration_ms += 5
                    
                    self.logger.info(f"Reduced quality settings for chat {chat_id}")
            
            if 'increase_buffer_target' in recommendations:
                # Increase target buffer size
                if streamer.buffer:
                    current_target = streamer.buffer.config.target_buffer_size
                    new_target = min(current_target + 10, streamer.buffer.config.max_buffer_size - 10)
                    streamer.buffer.config.target_buffer_size = new_target
                    
                    self.logger.info(f"Increased buffer target for chat {chat_id}: {current_target} -> {new_target}")
                    
        except Exception as e:
            self.logger.error(f"Error applying optimizations for chat {chat_id}: {e}")
    
    def get_performance_data(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get performance data for specific chat"""
        return self.performance_data.get(chat_id)
    
    async def cleanup(self):
        """Cleanup all monitoring tasks"""
        for chat_id in list(self.monitoring_tasks.keys()):
            await self.stop_monitoring(chat_id)