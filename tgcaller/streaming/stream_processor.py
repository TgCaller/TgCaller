"""
Stream Processor - Advanced stream processing and format conversion
"""

import asyncio
import logging
import tempfile
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
import json

from .fast_stream_buffer import StreamChunk

logger = logging.getLogger(__name__)


@dataclass
class ProcessorConfig:
    """Stream processor configuration"""
    
    # Audio processing
    audio_sample_rate: int = 48000
    """Audio sample rate"""
    
    audio_channels: int = 2
    """Number of audio channels"""
    
    audio_bitrate: int = 128000
    """Audio bitrate in bps"""
    
    audio_codec: str = "pcm_s16le"
    """Audio codec for processing"""
    
    # Video processing
    video_width: int = 1280
    """Video width"""
    
    video_height: int = 720
    """Video height"""
    
    video_fps: int = 30
    """Video frame rate"""
    
    video_codec: str = "rawvideo"
    """Video codec for processing"""
    
    video_pixel_format: str = "yuv420p"
    """Video pixel format"""
    
    # Processing options
    enable_filters: bool = True
    """Enable audio/video filters"""
    
    normalize_audio: bool = True
    """Normalize audio levels"""
    
    denoise_audio: bool = False
    """Apply audio denoising"""
    
    stabilize_video: bool = False
    """Apply video stabilization"""
    
    # Performance
    use_hardware_acceleration: bool = True
    """Use hardware acceleration"""
    
    thread_count: int = 0
    """FFmpeg thread count (0 = auto)"""
    
    buffer_size: int = 8192
    """Processing buffer size"""


class StreamProcessor:
    """
    Advanced stream processor with FFmpeg integration
    
    Features:
    - Real-time format conversion
    - Audio/video filtering
    - Quality optimization
    - Hardware acceleration
    - Adaptive processing
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        """
        Initialize stream processor
        
        Args:
            config: Processor configuration
        """
        self.config = config or ProcessorConfig()
        self.logger = logger
        
        # Processing state
        self.is_processing = False
        self.ffmpeg_process: Optional[asyncio.subprocess.Process] = None
        self.temp_files: List[Path] = []
        
        # Statistics
        self.processing_stats = {
            'chunks_processed': 0,
            'bytes_processed': 0,
            'processing_time_ms': 0.0,
            'avg_processing_time': 0.0,
            'errors': 0
        }
    
    async def process_stream_chunks(
        self,
        input_generator: AsyncGenerator[StreamChunk, None],
        output_format: str = "raw"
    ) -> AsyncGenerator[StreamChunk, None]:
        """
        Process stream chunks with format conversion
        
        Args:
            input_generator: Input chunk generator
            output_format: Output format (raw, opus, h264, etc.)
            
        Yields:
            Processed StreamChunk objects
        """
        try:
            self.is_processing = True
            
            # Start FFmpeg processor
            if not await self._start_ffmpeg_processor(output_format):
                return
            
            # Process chunks
            async for input_chunk in input_generator:
                if not self.is_processing:
                    break
                
                processed_chunk = await self._process_single_chunk(input_chunk)
                
                if processed_chunk:
                    yield processed_chunk
                    
        except Exception as e:
            self.logger.error(f"Error in stream processing: {e}")
        finally:
            await self._cleanup_processor()
    
    async def _start_ffmpeg_processor(self, output_format: str) -> bool:
        """Validate FFmpeg configuration before processing input chunks.

        Each chunk is processed in its own FFmpeg invocation so output is
        complete for that input chunk instead of being read at arbitrary
        boundaries from a long-running stdout pipe.
        """
        try:
            self._build_processing_command(output_format)
            self._output_format = output_format
            self.logger.info("FFmpeg chunk processor configured")
            return True
        except Exception as e:
            self.logger.error("Error configuring FFmpeg processor: %s", e)
            return False
    
    def _build_processing_command(self, output_format: str) -> List[str]:
        """Build an audio-only FFmpeg command for supported output formats.

        This processor accepts raw signed 16-bit PCM audio. Video formats such
        as H.264 are not valid outputs for this audio-only input pipeline.
        """
        if output_format not in {"raw", "opus", "aac"}:
            raise ValueError(
                f"Unsupported audio output format: {output_format!r}. "
                "Choose 'raw', 'opus', or 'aac'."
            )

        cmd = ['ffmpeg']
        
        # Input settings
        cmd.extend([
            '-f', 's16le',
            '-ar', str(self.config.audio_sample_rate),
            '-ac', str(self.config.audio_channels),
            '-i', 'pipe:0'
        ])
        
        # This pipeline processes audio-only PCM. Video hardware acceleration
        # does not accelerate this input and must not be advertised as active.
        
        # Thread settings
        if self.config.thread_count > 0:
            cmd.extend(['-threads', str(self.config.thread_count)])
        
        # Audio processing
        if self.config.enable_filters:
            audio_filters = self._build_audio_filters()
            if audio_filters:
                cmd.extend(['-af', audio_filters])
        
        # Output format specific settings
        if output_format == "opus":
            cmd.extend([
                '-acodec', 'libopus',
                '-ab', str(self.config.audio_bitrate),
                '-f', 'ogg'
            ])
        elif output_format == "aac":
            cmd.extend([
                '-acodec', 'aac',
                '-ab', str(self.config.audio_bitrate),
                '-f', 'adts'
            ])
        elif output_format == "raw":
            cmd.extend([
                '-acodec', 'pcm_s16le',
                '-f', 's16le'
            ])
        else:
            # Default to raw
            cmd.extend(['-acodec', 'pcm_s16le', '-f', 's16le'])
        
        # Output to stdout
        cmd.append('pipe:1')
        
        return cmd
    
    def _build_audio_filters(self) -> str:
        """Build audio filter chain"""
        filters = []
        
        # Normalization
        if self.config.normalize_audio:
            filters.append('loudnorm=I=-16:TP=-1.5:LRA=11')
        
        # Denoising
        if self.config.denoise_audio:
            filters.append('afftdn=nf=-25')
        
        # High-pass filter to remove low-frequency noise
        filters.append('highpass=f=80')
        
        # Low-pass filter to remove high-frequency artifacts
        filters.append('lowpass=f=15000')
        
        return ','.join(filters) if filters else ''
    
    async def _process_single_chunk(self, chunk: StreamChunk) -> Optional[StreamChunk]:
        """Process one complete chunk and return its complete FFmpeg output."""
        start_time = asyncio.get_running_loop().time()
        process = None
        try:
            output_format = getattr(self, "_output_format", None)
            if output_format is None:
                raise RuntimeError("FFmpeg processor has not been configured")

            # Raw PCM already matches this processor's input/output contract.
            # When filters are disabled, avoid spawning FFmpeg for every chunk.
            if output_format == "raw" and not self.config.enable_filters:
                processing_time = (asyncio.get_running_loop().time() - start_time) * 1000
                self._update_processing_stats(len(chunk.data), processing_time)
                return StreamChunk(
                    data=chunk.data,
                    timestamp=chunk.timestamp,
                    sequence=chunk.sequence,
                    chunk_type=chunk.chunk_type,
                    duration_ms=chunk.duration_ms,
                    metadata={
                        **chunk.metadata,
                        "processed": True,
                        "processing_time_ms": processing_time,
                        "original_size": len(chunk.data),
                        "processed_size": len(chunk.data),
                        "output_format": output_format,
                        "processing_path": "raw_passthrough",
                    },
                )

            command = self._build_processing_command(output_format)
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=chunk.data),
                    timeout=15.0,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise RuntimeError("FFmpeg timed out while processing a chunk")

            if process.returncode != 0:
                detail = stderr.decode("utf-8", errors="replace")[-2000:]
                raise RuntimeError(
                    f"FFmpeg exited with code {process.returncode}: {detail}"
                )
            if not stdout:
                raise RuntimeError("FFmpeg produced no output for the input chunk")

            processing_time = (asyncio.get_running_loop().time() - start_time) * 1000
            self._update_processing_stats(len(chunk.data), processing_time)
            return StreamChunk(
                data=stdout,
                timestamp=chunk.timestamp,
                sequence=chunk.sequence,
                chunk_type=chunk.chunk_type,
                duration_ms=chunk.duration_ms,
                metadata={
                    **chunk.metadata,
                    "processed": True,
                    "processing_time_ms": processing_time,
                    "original_size": len(chunk.data),
                    "processed_size": len(stdout),
                    "output_format": output_format,
                },
            )
        except Exception as e:
            self.logger.error("Error processing chunk %s: %s", chunk.sequence, e)
            self.processing_stats["errors"] += 1
            return None
    
    async def _write_to_ffmpeg(self, data: bytes):
        """Write PCM bytes to FFmpeg without blocking the event loop."""
        process = self.ffmpeg_process
        if not process or not process.stdin:
            raise RuntimeError("FFmpeg stdin is not available")
        if process.returncode is not None:
            raise RuntimeError(
                f"FFmpeg exited with return code {process.returncode}"
            )

        process.stdin.write(data)
        await process.stdin.drain()

    async def _read_from_ffmpeg(self) -> Optional[bytes]:
        """Read available output bytes asynchronously from FFmpeg stdout."""
        process = self.ffmpeg_process
        if not process or not process.stdout:
            return None

        data = await process.stdout.read(max(1, self.config.buffer_size))
        return data or None
    
    def _update_processing_stats(self, bytes_processed: int, processing_time_ms: float):
        """Update processing statistics"""
        self.processing_stats['chunks_processed'] += 1
        self.processing_stats['bytes_processed'] += bytes_processed
        self.processing_stats['processing_time_ms'] += processing_time_ms
        
        # Calculate average processing time
        chunk_count = self.processing_stats['chunks_processed']
        self.processing_stats['avg_processing_time'] = (
            self.processing_stats['processing_time_ms'] / chunk_count
        )
    
    async def _cleanup_processor(self):
        """Cleanup FFmpeg processor"""
        try:
            self.is_processing = False
            
            # Chunk processing uses short-lived subprocesses; normally there
            # is no persistent FFmpeg process to stop here.
            process = self.ffmpeg_process
            if process:
                if process.returncode is None:
                    process.terminate()
                    try:
                        await asyncio.wait_for(process.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                self.ffmpeg_process = None
            
            # Cleanup temporary files
            for temp_file in self.temp_files:
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            self.temp_files.clear()
            
            self.logger.info("Stream processor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during processor cleanup: {e}")
    
    async def _wait_for_ffmpeg(self):
        """Wait for the asynchronous FFmpeg subprocess to terminate."""
        process = self.ffmpeg_process
        if process:
            await process.wait()
    
    async def analyze_stream_format(self, sample_data: bytes) -> Dict[str, Any]:
        """Analyze stream format using FFprobe"""
        try:
            # Create temporary file with sample data
            with tempfile.NamedTemporaryFile(delete=False, suffix='.raw') as temp_file:
                temp_file.write(sample_data)
                temp_path = Path(temp_file.name)
            
            self.temp_files.append(temp_path)
            
            # Run FFprobe
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                '-f', 's16le',
                '-ar', str(self.config.audio_sample_rate),
                '-ac', str(self.config.audio_channels),
                str(temp_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return json.loads(stdout.decode())
            else:
                self.logger.error(f"FFprobe error: {stderr.decode()}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error analyzing stream format: {e}")
            return {}
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.processing_stats.copy()
        
        # Calculate additional metrics
        if stats['chunks_processed'] > 0:
            stats['avg_chunk_size'] = stats['bytes_processed'] / stats['chunks_processed']
            stats['processing_efficiency'] = (
                stats['chunks_processed'] / (stats['chunks_processed'] + stats['errors']) * 100
            )
        
        return stats
    
    def reset_stats(self):
        """Reset processing statistics"""
        self.processing_stats = {
            'chunks_processed': 0,
            'bytes_processed': 0,
            'processing_time_ms': 0.0,
            'avg_processing_time': 0.0,
            'errors': 0
        }
    
    @property
    def is_active(self) -> bool:
        """Check if processor is active"""
        return self.is_processing
    
    @property
    def processing_efficiency(self) -> float:
        """Get processing efficiency percentage"""
        total_operations = self.processing_stats['chunks_processed'] + self.processing_stats['errors']
        if total_operations == 0:
            return 100.0
        
        return (self.processing_stats['chunks_processed'] / total_operations) * 100.0