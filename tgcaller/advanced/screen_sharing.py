"""
Screen Sharing - Capture and stream screen
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Tuple
try:
    import cv2
    import mss
except ImportError:
    cv2 = None
    mss = None

from ..types import VideoConfig

logger = logging.getLogger(__name__)


class ScreenShare:
    """Screen sharing functionality"""
    
    def __init__(self, video_config: Optional[VideoConfig] = None):
        if mss is None or cv2 is None:
            raise ImportError("mss and opencv-python required for screen sharing")
        
        self.video_config = video_config or VideoConfig()
        self.sct = mss.mss()
        self.is_sharing = False
        self.callbacks = []
        self.logger = logger
        self.monitor = None
    
    def add_callback(self, callback):
        """Add callback for screen frames"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def list_monitors(self) -> list:
        """List available monitors"""
        try:
            monitors = []
            for i, monitor in enumerate(self.sct.monitors):
                if i == 0:  # Skip the "All in One" monitor
                    continue
                monitors.append({
                    'index': i,
                    'width': monitor['width'],
                    'height': monitor['height'],
                    'left': monitor['left'],
                    'top': monitor['top']
                })
            return monitors
        except Exception as e:
            self.logger.error(f"Error listing monitors: {e}")
            return []
    
    async def start_sharing(
        self, 
        monitor_index: int = 1,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> bool:
        """
        Start screen sharing
        
        Args:
            monitor_index: Monitor to capture (1 for primary)
            region: Custom region (left, top, width, height)
            
        Returns:
            True if sharing started successfully
        """
        if self.is_sharing:
            self.logger.warning("Screen sharing already active")
            return True
        
        try:
            # Setup monitor/region
            if region:
                self.monitor = {
                    'left': region[0],
                    'top': region[1], 
                    'width': region[2],
                    'height': region[3]
                }
            else:
                if monitor_index >= len(self.sct.monitors):
                    raise ValueError(f"Monitor {monitor_index} not found")
                self.monitor = self.sct.monitors[monitor_index]
            
            self.is_sharing = True
            
            # Start capture loop
            asyncio.create_task(self._capture_loop())
            
            self.logger.info(f"Screen sharing started on monitor {monitor_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start screen sharing: {e}")
            return False
    
    async def stop_sharing(self):
        """Stop screen sharing"""
        self.is_sharing = False
        self.logger.info("Screen sharing stopped")
    
    async def _capture_loop(self):
        """Main capture loop"""
        fps = self.video_config.fps
        frame_delay = 1.0 / fps
        
        while self.is_sharing:
            try:
                # Capture screen
                screenshot = self.sct.grab(self.monitor)
                
                # Convert to numpy array
                frame = np.array(screenshot)
                
                # Convert BGRA to BGR
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Resize if needed
                target_size = (self.video_config.width, self.video_config.height)
                if frame.shape[:2][::-1] != target_size:
                    frame = cv2.resize(frame, target_size)
                
                # Call callbacks
                for callback in self.callbacks:
                    try:
                        callback(frame)
                    except Exception as e:
                        self.logger.error(f"Error in screen share callback: {e}")
                
                await asyncio.sleep(frame_delay)
                
            except Exception as e:
                self.logger.error(f"Error in screen capture: {e}")
                await asyncio.sleep(1)


class ScreenShareStreamer:
    """Stream screen to TgCaller"""
    
    def __init__(self, caller, chat_id: int):
        self.caller = caller
        self.chat_id = chat_id
        self.screen_share = None
        self.is_streaming = False
    
    async def start_streaming(
        self,
        video_config: Optional[VideoConfig] = None,
        monitor_index: int = 1,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> bool:
        """Start streaming screen to call"""
        try:
            # Join call if not already joined
            if not self.caller.is_connected(self.chat_id):
                await self.caller.join_call(self.chat_id, video_config=video_config)
            
            # Setup screen sharing
            self.screen_share = ScreenShare(video_config)
            self.screen_share.add_callback(self._stream_frame)
            
            # Start sharing
            success = await self.screen_share.start_sharing(monitor_index, region)
            if success:
                self.is_streaming = True
                logger.info(f"Started screen sharing to chat {self.chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to start screen streaming: {e}")
            return False
    
    async def stop_streaming(self):
        """Stop screen streaming"""
        try:
            self.is_streaming = False
            
            if self.screen_share:
                await self.screen_share.stop_sharing()
                self.screen_share = None
            
            logger.info(f"Stopped screen streaming to chat {self.chat_id}")
            
        except Exception as e:
            logger.error(f"Error stopping screen streaming: {e}")
    
    def _stream_frame(self, frame: np.ndarray):
        """Stream frame to call"""
        if self.is_streaming:
            # This would send frame to the call
            # Implementation depends on actual streaming protocol
            pass


class WindowCapture:
    """Capture specific application window"""
    
    def __init__(self):
        self.logger = logger
    
    def list_windows(self) -> list:
        """List available windows"""
        try:
            import pygetwindow as gw
            windows = []
            
            for window in gw.getAllWindows():
                if window.title and window.visible:
                    windows.append({
                        'title': window.title,
                        'left': window.left,
                        'top': window.top,
                        'width': window.width,
                        'height': window.height
                    })
            
            return windows
        except ImportError:
            self.logger.error("pygetwindow required for window capture")
            return []
        except Exception as e:
            self.logger.error(f"Error listing windows: {e}")
            return []
    
    async def capture_window(self, window_title: str) -> Optional[np.ndarray]:
        """Capture specific window"""
        try:
            import pygetwindow as gw
            
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                return None
            
            window = windows[0]
            
            # Get window region
            region = {
                'left': window.left,
                'top': window.top,
                'width': window.width,
                'height': window.height
            }
            
            # Capture using mss
            with mss.mss() as sct:
                screenshot = sct.grab(region)
                frame = np.array(screenshot)
                return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
        except Exception as e:
            self.logger.error(f"Error capturing window: {e}")
            return None