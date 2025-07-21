"""
YouTube Streamer with FastStreamBuffer integration
"""

import asyncio
import logging
import subprocess
from typing import Optional, AsyncGenerator, Dict, Any
from dataclasses import dataclass
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

from .fast_stream_buffer import FastStreamBuffer, BufferConfig, StreamChunk
from ..types import AudioConfig, VideoConfig

logger = logging.getLogger(__name__)


@dataclass
class YouTubeStreamConfig:
    """YouTube streaming configuration"""
    
    # Quality settings
    video_quality: str = "best[height<=720]"
    """Video quality selector"""
    
    audio_quality: str = "bestaudio"
    """Audio quality selector"""
    
    # Buffer settings
    buffer_config: Optional[BufferConfig] = None
    """FastStreamBuffer configuration"""
    
    # FFmpeg settings
    ffmpeg_options: Dict[str, str] = None
    """Custom FFmpeg options"""
    
    # Streaming settings
    chunk_size: int = 8192
    """Chunk size for streaming"""
    
    enable_audio: bool = True
    """Enable audio streaming"""
    
    enable_video: bool = True
    """Enable video streaming"""
    
    # Performance settings
    use_hardware_acceleration: bool = True
    """Use hardware acceleration if available"""
    
    max_download_rate: Optional[str] = None
    """Maximum download rate (e.g., '1M')"""
    
    def __post_init__(self):
        """Initialize default values"""
        if self.buffer_config is None:
            self.buffer_config = BufferConfig(
                max_buffer_size=100,
                min_buffer_size=10,
                target_buffer_size=30,
                chunk_duration_ms=20.0,
                max_latency_ms=80.0
            )
        
        if self.ffmpeg_options is None:
            self.ffmpeg_options = {
                'before_options': '-re -fflags +genpts',
                'options': '-f s16le -ar 48000 -ac 2'
            }


class YouTubeStreamer:
    """
    Ultra-low-latency YouTube streamer using FastStreamBuffer
    
    Features:
    - Direct streaming without full download
    - Async buffered chunk processing
    - Adaptive quality control
    - FFmpeg integration for format conversion
    - Real-time latency optimization
    """
    
    def __init__(self, caller, config: Optional[YouTubeStreamConfig] = None):
        """
        Initialize YouTube streamer
        
        Args:
            caller: TgCaller instance
            config: Streaming configuration
        """
        if yt_dlp is None:
            raise ImportError("yt-dlp is required for YouTube streaming")
        
        self.caller = caller
        self.config = config or YouTubeStreamConfig()
        self.logger = logger
        
        # Streaming components
        self.buffer: Optional[FastStreamBuffer] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.stream_url: Optional[str] = None
        
        # State management
        self.is_streaming = False
        self.current_chat_id: Optional[int] = None
        
        # Statistics
        self.stream_stats = {
            'start_time': 0.0,
            'bytes_streamed': 0,
            'chunks_processed': 0,
            'avg_chunk_latency': 0.0,
            'buffer_underruns': 0,
            'quality_adaptations': 0
        }
    
    async def stream_youtube_url(
        self, 
        chat_id: int, 
        url: str,
        audio_config: Optional[AudioConfig] = None,
        video_config: Optional[VideoConfig] = None
    ) -> bool:
        """
        Stream YouTube video with ultra-low latency
        
        Args:
            chat_id: Target chat ID
            url: YouTube URL
            audio_config: Audio configuration
            video_config: Video configuration
            
        Returns:
            True if streaming started successfully
        """
        if self.is_streaming:
            self.logger.warning("Already streaming, stopping current stream")
            await self.stop_streaming()
        
        try:
            self.current_chat_id = chat_id
            
            # Get stream URL
            self.stream_url = await self._get_stream_url(url)
            if not self.stream_url:
                return False
            
            # Join call if not connected
            if not self.caller.is_connected(chat_id):
                await self.caller.join_call(chat_id, audio_config, video_config)
            
            # Initialize buffer
            self.buffer = FastStreamBuffer(self.config.buffer_config)
            
            # Setup buffer callbacks
            self._setup_buffer_callbacks()
            
            # Start streaming pipeline
            success = await self._start_streaming_pipeline()
            
            if success:
                self.is_streaming = True
                self.stream_stats['start_time'] = time.time()
                self.logger.info(f"Started YouTube streaming to chat {chat_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start YouTube streaming: {e}")
            await self.stop_streaming()
            return False
    
    async def stop_streaming(self):
        """Stop YouTube streaming"""
        try:
            self.is_streaming = False
            
            # Stop buffer
            if self.buffer:
                await self.buffer.stop_buffering()
                self.buffer = None
            
            # Stop FFmpeg process
            if self.ffmpeg_process:
                self.ffmpeg_process.terminate()
                try:
                    await asyncio.wait_for(
                        asyncio.create_task(self._wait_for_process()), 
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    self.ffmpeg_process.kill()
                
                self.ffmpeg_process = None
            
            # Reset state
            self.current_chat_id = None
            self.stream_url = None
            
            self.logger.info("YouTube streaming stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping streaming: {e}")
    
    async def _get_stream_url(self, url: str) -> Optional[str]:
        """Get direct stream URL from YouTube"""
        try:
            ydl_opts = {
                'format': self.config.video_quality if self.config.enable_video else self.config.audio_quality,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            if self.config.max_download_rate:
                ydl_opts['ratelimit'] = self.config.max_download_rate
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Run in thread to avoid blocking
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
                
                # Get stream URL
                if 'url' in info:
                    return info['url']
                elif 'formats' in info and info['formats']:
                    # Get best format URL
                    return info['formats'][-1].get('url')
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting stream URL: {e}")
            return None
    
    async def _start_streaming_pipeline(self) -> bool:
        """Start the streaming pipeline"""
        try:
            # Start FFmpeg process
            if not await self._start_ffmpeg_process():
                return False
            
            # Create chunk generator
            chunk_generator = self._create_chunk_generator()
            
            # Start buffer
            success = await self.buffer.start_buffering(chunk_generator)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error starting streaming pipeline: {e}")
            return False
    
    async def _start_ffmpeg_process(self) -> bool:
        """Start FFmpeg process for format conversion"""
        try:
            # Build FFmpeg command
            cmd = self._build_ffmpeg_command()
            
            # Start process
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            # Verify process started
            await asyncio.sleep(0.1)
            if self.ffmpeg_process.poll() is not None:
                stderr = self.ffmpeg_process.stderr.read().decode()
                self.logger.error(f"FFmpeg failed to start: {stderr}")
                return False
            
            self.logger.info("FFmpeg process started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting FFmpeg: {e}")
            return False
    
    def _build_ffmpeg_command(self) -> List[str]:
        """Build FFmpeg command for streaming"""
        cmd = ['ffmpeg']
        
        # Input options
        before_options = self.config.ffmpeg_options.get('before_options', '')
        if before_options:
            cmd.extend(before_options.split())
        
        # Input source
        cmd.extend(['-i', self.stream_url])
        
        # Hardware acceleration
        if self.config.use_hardware_acceleration:
            cmd.extend(['-hwaccel', 'auto'])
        
        # Audio settings
        if self.config.enable_audio:
            cmd.extend([
                '-acodec', 'pcm_s16le',
                '-ar', '48000',
                '-ac', '2'
            ])
        else:
            cmd.extend(['-an'])
        
        # Video settings
        if self.config.enable_video:
            cmd.extend([
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'yuv420p'
            ])
        else:
            cmd.extend(['-vn'])
        
        # Output options
        options = self.config.ffmpeg_options.get('options', '')
        if options:
            cmd.extend(options.split())
        
        # Output to stdout
        cmd.extend(['-f', 's16le', 'pipe:1'])
        
        return cmd
    
    async def _create_chunk_generator(self) -> AsyncGenerator[bytes, None]:
        """Create async generator for stream chunks"""
        try:
            while self.is_streaming and self.ffmpeg_process:
                # Check if process is still running
                if self.ffmpeg_process.poll() is not None:
                    break
                
                # Read chunk from FFmpeg
                chunk_data = await self._read_ffmpeg_chunk()
                
                if chunk_data:
                    yield chunk_data
                    self.stream_stats['bytes_streamed'] += len(chunk_data)
                else:
                    # No data available, yield control
                    await asyncio.sleep(0.001)
                    
        except Exception as e:
            self.logger.error(f"Error in chunk generator: {e}")
        finally:
            self.logger.debug("Chunk generator finished")
    
    async def _read_ffmpeg_chunk(self) -> Optional[bytes]:
        """Read chunk from FFmpeg process"""
        try:
            if not self.ffmpeg_process or not self.ffmpeg_process.stdout:
                return None
            
            # Read chunk asynchronously
            loop = asyncio.get_event_loop()
            chunk_data = await loop.run_in_executor(
                None,
                lambda: self.ffmpeg_process.stdout.read(self.config.chunk_size)
            )
            
            return chunk_data if chunk_data else None
            
        except Exception as e:
            self.logger.error(f"Error reading FFmpeg chunk: {e}")
            return None
    
    def _setup_buffer_callbacks(self):
        """Setup FastStreamBuffer callbacks"""
        # Chunk processing callback
        def on_chunk_ready(chunk: StreamChunk):
            """Handle processed chunk"""
            try:
                # Send chunk to TgCaller
                asyncio.create_task(self._send_chunk_to_caller(chunk))
                
                # Update statistics
                self.stream_stats['chunks_processed'] += 1
                self.stream_stats['avg_chunk_latency'] = (
                    (self.stream_stats['avg_chunk_latency'] * (self.stream_stats['chunks_processed'] - 1) + 
                     chunk.age_ms) / self.stream_stats['chunks_processed']
                )
                
            except Exception as e:
                self.logger.error(f"Error handling chunk: {e}")
        
        # State change callback
        def on_state_change(state):
            """Handle buffer state changes"""
            self.logger.debug(f"Buffer state changed to: {state.value}")
            
            if state.value == 'underrun':
                self.stream_stats['buffer_underruns'] += 1
                self.logger.warning("Buffer underrun detected")
        
        # Statistics callback
        def on_stats_update(stats):
            """Handle statistics updates"""
            # Log performance metrics periodically
            if stats['chunks_consumed'] % 100 == 0:
                self.logger.info(
                    f"Streaming stats - Health: {stats['buffer_health']:.1f}%, "
                    f"Latency: {stats['avg_latency_ms']:.1f}ms, "
                    f"Throughput: {stats['throughput_mbps']:.2f}Mbps"
                )
        
        # Register callbacks
        self.buffer.add_chunk_callback(on_chunk_ready)
        self.buffer.add_state_callback(on_state_change)
        self.buffer.add_stats_callback(on_stats_update)
    
    async def _send_chunk_to_caller(self, chunk: StreamChunk):
        """Send processed chunk to TgCaller"""
        try:
            if not self.current_chat_id or not self.caller.is_connected(self.current_chat_id):
                return
            
            # Convert chunk to format expected by TgCaller
            # This would integrate with TgCaller's streaming system
            await self.caller.send_frame(
                self.current_chat_id,
                chunk.data,
                chunk.chunk_type
            )
            
        except Exception as e:
            self.logger.error(f"Error sending chunk to caller: {e}")
    
    async def _wait_for_process(self):
        """Wait for FFmpeg process to terminate"""
        if self.ffmpeg_process:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.ffmpeg_process.wait)
    
    def get_streaming_stats(self) -> Dict[str, Any]:
        """Get comprehensive streaming statistics"""
        stats = self.stream_stats.copy()
        
        if self.buffer:
            stats.update(self.buffer.get_buffer_info())
        
        # Calculate additional metrics
        if stats['start_time'] > 0:
            duration = time.time() - stats['start_time']
            stats['duration_seconds'] = duration
            stats['avg_throughput_mbps'] = (stats['bytes_streamed'] * 8) / (duration * 1024 * 1024)
        
        return stats
    
    @property
    def buffer_health(self) -> float:
        """Get current buffer health percentage"""
        return self.buffer.buffer_health if self.buffer else 0.0
    
    @property
    def current_latency(self) -> float:
        """Get current streaming latency in milliseconds"""
        return self.buffer.average_latency if self.buffer else 0.0


# Import time for timestamps
import time