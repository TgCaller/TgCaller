"""
Media Processing Utilities
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class MediaUtils:
    """Media processing utilities"""
    
    @staticmethod
    async def get_media_info(source: str) -> Optional[Dict[str, Any]]:
        """Get media file information using ffprobe"""
        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                source
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                import json
                return json.loads(stdout.decode())
            else:
                logger.error(f"ffprobe error: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting media info: {e}")
            return None
    
    @staticmethod
    async def convert_audio(
        input_path: str,
        output_path: str,
        bitrate: int = 48000,
        sample_rate: int = 48000,
        channels: int = 2
    ) -> bool:
        """Convert audio file to required format"""
        try:
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-acodec", "libopus",
                "-ab", str(bitrate),
                "-ar", str(sample_rate),
                "-ac", str(channels),
                "-y",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Audio converted successfully: {output_path}")
                return True
            else:
                logger.error(f"ffmpeg error: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            return False
    
    @staticmethod
    async def extract_audio(video_path: str, audio_path: str) -> bool:
        """Extract audio from video file"""
        try:
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vn",
                "-acodec", "libopus",
                "-y",
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            return False
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """Check if file format is supported"""
        supported_audio = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        supported_video = ['.mp4', '.avi', '.mkv', '.mov', '.webm']
        
        path = Path(file_path)
        extension = path.suffix.lower()
        
        return extension in supported_audio + supported_video
    
    @staticmethod
    async def download_youtube(url: str, output_path: str) -> Optional[str]:
        """Download YouTube video/audio"""
        try:
            import yt_dlp
            
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': output_path,
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
                
        except Exception as e:
            logger.error(f"Error downloading YouTube video: {e}")
            return None