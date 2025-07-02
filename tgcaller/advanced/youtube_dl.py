"""
YouTube Downloader - Download and stream YouTube videos
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Download and stream YouTube videos"""
    
    def __init__(self, download_dir: Optional[str] = None):
        if yt_dlp is None:
            raise ImportError("yt-dlp is required for YouTube downloading")
        
        self.download_dir = download_dir or tempfile.gettempdir()
        self.logger = logger
        
        # Default yt-dlp options
        self.default_opts = {
            'format': 'best[height<=720]',
            'outtmpl': os.path.join(self.download_dir, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'extract_flat': False,
        }
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information without downloading"""
        try:
            opts = self.default_opts.copy()
            opts['quiet'] = True
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Run in thread to avoid blocking
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None, 
                    lambda: ydl.extract_info(url, download=False)
                )
                
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description'),
                    'thumbnail': info.get('thumbnail'),
                    'formats': info.get('formats', [])
                }
                
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None
    
    async def download_video(
        self, 
        url: str,
        quality: str = 'best[height<=720]',
        audio_only: bool = False
    ) -> Optional[str]:
        """
        Download video from YouTube
        
        Args:
            url: YouTube URL
            quality: Video quality format
            audio_only: Download audio only
            
        Returns:
            Path to downloaded file
        """
        try:
            opts = self.default_opts.copy()
            
            if audio_only:
                opts['format'] = 'bestaudio/best'
                opts['outtmpl'] = os.path.join(
                    self.download_dir, 
                    '%(title)s.%(ext)s'
                )
            else:
                opts['format'] = quality
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Run in thread
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=True)
                )
                
                # Get downloaded file path
                filename = ydl.prepare_filename(info)
                
                if os.path.exists(filename):
                    self.logger.info(f"Downloaded: {filename}")
                    return filename
                else:
                    self.logger.error(f"Downloaded file not found: {filename}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error downloading video: {e}")
            return None
    
    async def download_playlist(
        self, 
        url: str,
        max_downloads: int = 10
    ) -> List[str]:
        """Download YouTube playlist"""
        try:
            opts = self.default_opts.copy()
            opts['noplaylist'] = False
            opts['playlistend'] = max_downloads
            
            downloaded_files = []
            
            def progress_hook(d):
                if d['status'] == 'finished':
                    downloaded_files.append(d['filename'])
            
            opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    lambda: ydl.download([url])
                )
            
            self.logger.info(f"Downloaded {len(downloaded_files)} files from playlist")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"Error downloading playlist: {e}")
            return []
    
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search YouTube videos"""
        try:
            search_url = f"ytsearch{max_results}:{query}"
            
            opts = {
                'quiet': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                loop = asyncio.get_event_loop()
                search_results = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(search_url, download=False)
                )
                
                videos = []
                for entry in search_results.get('entries', []):
                    videos.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': entry.get('url'),
                        'duration': entry.get('duration'),
                        'uploader': entry.get('uploader'),
                        'view_count': entry.get('view_count')
                    })
                
                return videos
                
        except Exception as e:
            self.logger.error(f"Error searching videos: {e}")
            return []
    
    async def get_stream_url(
        self, 
        url: str,
        quality: str = 'best[height<=720]'
    ) -> Optional[str]:
        """Get direct stream URL without downloading"""
        try:
            opts = {
                'format': quality,
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(opts) as ydl:
                loop = asyncio.get_event_loop()
                info = await loop.run_in_executor(
                    None,
                    lambda: ydl.extract_info(url, download=False)
                )
                
                # Get the best format URL
                if 'url' in info:
                    return info['url']
                elif 'formats' in info and info['formats']:
                    return info['formats'][-1].get('url')
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting stream URL: {e}")
            return None
    
    def cleanup_downloads(self, max_age_hours: int = 24):
        """Clean up old downloaded files"""
        try:
            import time
            
            download_path = Path(self.download_dir)
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            deleted_count = 0
            
            for file_path in download_path.glob('*'):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} old files")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up downloads: {e}")


class YouTubeStreamer:
    """Stream YouTube videos directly to TgCaller"""
    
    def __init__(self, caller, downloader: Optional[YouTubeDownloader] = None):
        self.caller = caller
        self.downloader = downloader or YouTubeDownloader()
        self.logger = logger
    
    async def play_youtube_url(
        self, 
        chat_id: int, 
        url: str,
        quality: str = 'best[height<=720]'
    ) -> bool:
        """Play YouTube video directly in call"""
        try:
            # Get stream URL
            stream_url = await self.downloader.get_stream_url(url, quality)
            
            if not stream_url:
                self.logger.error("Failed to get stream URL")
                return False
            
            # Play in call
            success = await self.caller.play(chat_id, stream_url)
            
            if success:
                self.logger.info(f"Started playing YouTube video in chat {chat_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error playing YouTube URL: {e}")
            return False
    
    async def download_and_play(
        self, 
        chat_id: int, 
        url: str,
        quality: str = 'best[height<=720]',
        audio_only: bool = False
    ) -> bool:
        """Download and play YouTube video"""
        try:
            # Download video
            file_path = await self.downloader.download_video(
                url, quality, audio_only
            )
            
            if not file_path:
                self.logger.error("Failed to download video")
                return False
            
            # Play downloaded file
            success = await self.caller.play(chat_id, file_path)
            
            if success:
                self.logger.info(f"Started playing downloaded video in chat {chat_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error downloading and playing: {e}")
            return False
    
    async def search_and_play(
        self, 
        chat_id: int, 
        query: str,
        index: int = 0
    ) -> bool:
        """Search and play first result"""
        try:
            # Search videos
            results = await self.downloader.search_videos(query, max_results=5)
            
            if not results or index >= len(results):
                self.logger.error("No search results found")
                return False
            
            # Play selected result
            video = results[index]
            return await self.play_youtube_url(chat_id, video['url'])
            
        except Exception as e:
            self.logger.error(f"Error searching and playing: {e}")
            return False