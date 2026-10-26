"""
YouTube Streamer with FastStreamBuffer integration
"""

import asyncio
import logging
import subprocess
import time
from typing import Optional, AsyncGenerator, Dict, Any, List
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
    # 48 kHz stereo signed 16-bit PCM: 20 ms = 48000 * 0.020 * 2 channels * 2 bytes.
    chunk_size: int = 3840
    """Chunk size for streaming"""
    
    enable_audio: bool = True
    """Enable audio streaming"""
    
    enable_video: bool = False
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
    
    def __init__(
        self, caller, config: Optional[YouTubeStreamConfig] = None, downloader=None
    ):
        """
        Initialize YouTube streamer
        
        Args:
            caller: TgCaller instance
            config: Streaming configuration
        """
        if yt_dlp is None:
            raise ImportError("yt-dlp is required for YouTube streaming")
        
        # Preserve the historical advanced.YouTubeStreamer(caller, downloader)
        # call shape while keeping this module as the single streaming engine.
        if config is not None and not isinstance(config, YouTubeStreamConfig):
            if downloader is not None:
                raise TypeError("pass a stream config or downloader, not both positionally")
            downloader, config = config, None
        self.caller = caller
        self.config = config or YouTubeStreamConfig()
        self.downloader = downloader
        self.logger = logger
        
        # Streaming components
        self.buffer: Optional[FastStreamBuffer] = None
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.stream_url: Optional[str] = None
        
        # State management
        self.is_streaming = False
        self.current_chat_id: Optional[int] = None
        # Serialize frame delivery so concurrent callback tasks cannot reorder
        # consecutive PCM chunks when the transport is slower than the producer.
        self._send_lock = asyncio.Lock()
        
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
        # Video output is not implemented by this raw-PCM pipeline. Reject it
        # before resolving a URL or joining a Telegram call so the API cannot
        # leave a call joined after an unsupported request.
        if self.config.enable_video or video_config is not None:
            self.logger.error(
                "YouTube video streaming is not implemented; audio-only mode is required"
            )
            return False

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
            
            # Mark the stream active before starting the producer. The chunk
            # generator checks this flag on its first iteration.
            self.is_streaming = True
            success = await self._start_streaming_pipeline()
            
            if success:
                self.stream_stats['start_time'] = time.time()
                self.logger.info(f"Started YouTube audio streaming to chat {chat_id}")
            else:
                await self.stop_streaming()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to start YouTube streaming: {e}")
            await self.stop_streaming()
            return False
    
    async def play_youtube_url(
        self, chat_id: int, url: str, quality: str = "best[height<=720]"
    ) -> bool:
        """Backward-compatible name for the canonical buffered audio pipeline."""
        self.config.audio_quality = quality
        return await self.stream_youtube_url(chat_id, url)

    def _get_downloader(self):
        """Load the optional download helper only when a download API is used."""
        if self.downloader is None:
            from ..advanced.youtube_dl import YouTubeDownloader
            self.downloader = YouTubeDownloader()
        return self.downloader

    async def download_and_play(
        self,
        chat_id: int,
        url: str,
        quality: str = "best[height<=720]",
        audio_only: bool = False,
    ) -> bool:
        """Download media and hand the resulting file to TgCaller's play API."""
        try:
            file_path = await self._get_downloader().download_video(
                url, quality=quality, audio_only=audio_only
            )
            if not file_path:
                return False
            return bool(await self.caller.play(chat_id, file_path))
        except Exception as exc:
            self.logger.error("Error downloading and playing YouTube media: %s", exc)
            return False

    async def search_and_play(
        self, chat_id: int, query: str, index: int = 0
    ) -> bool:
        """Search YouTube and stream the selected result through the same pipeline."""
        try:
            if isinstance(index, bool) or not isinstance(index, int) or index < 0:
                return False
            results = await self._get_downloader().search_videos(query, max_results=5)
            if not results or index >= len(results):
                return False
            url = results[index].get("url")
            if not url:
                return False
            return await self.play_youtube_url(chat_id, url)
        except Exception as exc:
            self.logger.error("Error searching and playing YouTube media: %s", exc)
            return False

    async def stop_streaming(self):
        """Stop YouTube streaming"""
        try:
            self.is_streaming = False
            
            # Stop buffer
            if self.buffer:
                await self.buffer.stop_buffering()
                self.buffer = None
            
            # Stop FFmpeg process and always reap it before dropping the handle.
            process = self.ffmpeg_process
            if process:
                if process.poll() is None:
                    process.terminate()
                    try:
                        await asyncio.wait_for(
                            asyncio.get_running_loop().run_in_executor(
                                None, process.wait
                            ),
                            timeout=5.0,
                        )
                    except asyncio.TimeoutError:
                        process.kill()
                        await asyncio.get_running_loop().run_in_executor(
                            None, process.wait
                        )
                if process.stdout and not process.stdout.closed:
                    process.stdout.close()
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
                
                # A selected direct URL is normally returned for the requested
                # format. In audio-only mode, reject a video-only direct result.
                if not isinstance(info, dict):
                    return None

                direct_url = info.get('url')
                if direct_url and (
                    not self.config.enable_audio
                    or info.get('acodec') not in (None, 'none')
                ):
                    return direct_url

                formats = info.get('formats') or []
                if self.config.enable_audio:
                    # Do not assume formats[-1] is audio: yt-dlp format order
                    # is not a contract and may end with a video-only rendition.
                    formats = [
                        item for item in formats
                        if isinstance(item, dict)
                        and item.get('url')
                        and item.get('acodec') not in (None, 'none')
                    ]
                    # Prefer audio-only formats and then the highest declared
                    # audio bitrate, with total bitrate as a fallback.
                    formats.sort(
                        key=lambda item: (
                            item.get('vcodec') == 'none',
                            item.get('abr') or item.get('tbr') or 0,
                        ),
                        reverse=True,
                    )
                else:
                    formats = [
                        item for item in formats
                        if isinstance(item, dict) and item.get('url')
                    ]

                return formats[0].get('url') if formats else None
                
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
                # Never leave FFmpeg's stderr pipe unread: a full pipe can
                # stall FFmpeg and silently freeze audio delivery.
                stderr=subprocess.DEVNULL,
                bufsize=0
            )
            
            # Verify process started
            await asyncio.sleep(0.1)
            if self.ffmpeg_process.poll() is not None:
                self.logger.error(
                    "FFmpeg exited during startup with return code %s",
                    self.ffmpeg_process.returncode,
                )
                return False
            
            self.logger.info("FFmpeg process started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting FFmpeg: {e}")
            return False
    
    def _build_ffmpeg_command(self) -> List[str]:
        """Build an audio-only FFmpeg command for the current raw-PCM pipeline.

        Video is deliberately rejected until a real video packetization and
        Telegram media-engine path exists; raw video cannot share an s16le pipe.
        """
        if self.config.enable_video:
            raise NotImplementedError(
                "YouTube video output is not implemented yet; set enable_video=False "
                "for the supported raw-PCM audio pipeline."
            )
        if not self.config.enable_audio:
            raise ValueError("At least audio output must be enabled")

        cmd = ['ffmpeg']
        
        # Input options
        before_options = self.config.ffmpeg_options.get('before_options', '')
        if before_options:
            cmd.extend(before_options.split())
        
        # Input source
        cmd.extend(['-i', self.stream_url])
        
        # Keep output predictable: this pipeline transports raw PCM audio only.
        # Hardware acceleration is not applicable to this audio-only output.
        
        # Audio settings
        if self.config.enable_audio:
            cmd.extend([
                '-acodec', 'pcm_s16le',
                '-ar', '48000',
                '-ac', '2'
            ])
        else:
            cmd.extend(['-an'])
        
        # Explicitly disable video; raw PCM stdout cannot carry video frames.
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
        """Read one aligned PCM chunk from FFmpeg without returning short pipe reads.

        The audio pipeline emits 48 kHz, stereo, signed 16-bit PCM. The default
        3840-byte chunk is one 20 ms frame. OS pipes may return fewer bytes than
        requested, so accumulate reads until one frame is ready or EOF is reached.
        Any final partial chunk is returned only when it ends on a complete PCM
        sample frame (4 bytes for stereo s16le).
        """
        try:
            process = self.ffmpeg_process
            if not process or not process.stdout:
                return None

            def read_frame():
                frame_size = self.config.chunk_size
                if (
                    isinstance(frame_size, bool)
                    or not isinstance(frame_size, int)
                    or frame_size <= 0
                    or frame_size % 4 != 0
                ):
                    raise ValueError(
                        "chunk_size must be a positive multiple of 4 for stereo s16le PCM"
                    )

                chunks = bytearray()
                while len(chunks) < frame_size:
                    part = process.stdout.read(frame_size - len(chunks))
                    if not part:
                        break
                    chunks.extend(part)

                if not chunks:
                    return None
                # Never pass a broken stereo PCM sample frame downstream.
                usable_size = len(chunks) - (len(chunks) % 4)
                if usable_size == 0:
                    return None
                return bytes(chunks[:usable_size])

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, read_frame)

        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Error reading FFmpeg chunk: {e}")
            return None
    
    def _setup_buffer_callbacks(self):
        """Setup FastStreamBuffer callbacks"""
        # Async callback is awaited by FastStreamBuffer, providing backpressure
        # and preventing one detached task per audio chunk.
        async def on_chunk_ready(chunk: StreamChunk):
            """Deliver a processed chunk before the buffer consumes the next one."""
            sent = await self._send_chunk_to_caller(chunk)
            if not sent:
                self.logger.warning(
                    "Audio chunk %s was not delivered to TgCaller", chunk.sequence
                )
                return

            self.stream_stats['chunks_processed'] += 1
            count = self.stream_stats['chunks_processed']
            self.stream_stats['avg_chunk_latency'] = (
                (self.stream_stats['avg_chunk_latency'] * (count - 1) + chunk.age_ms)
                / count
            )
        
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
    
    async def _send_chunk_to_caller(self, chunk: StreamChunk) -> bool:
        """Send one chunk and report whether the caller accepted it."""
        try:
            async with self._send_lock:
                chat_id = self.current_chat_id
                if chat_id is None or not self.caller.is_connected(chat_id):
                    return False

                # Keep delivery serialized; the buffer awaits this operation so
                # a slow transport naturally applies backpressure to FFmpeg.
                result = await self.caller.send_frame(
                    chat_id,
                    chunk.data,
                    chunk.chunk_type
                )
                # Older public send_frame implementations return None on success.
                return result is not False
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.logger.error(f"Error sending chunk to caller: {e}")
            return False
    
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