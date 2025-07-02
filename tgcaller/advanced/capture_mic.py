"""
Microphone Capture - Real-time microphone input
"""

import asyncio
import logging
import numpy as np
from typing import Optional, Callable
try:
    import pyaudio
except ImportError:
    pyaudio = None

from ..types import AudioConfig

logger = logging.getLogger(__name__)


class MicrophoneCapture:
    """Capture microphone input for streaming"""
    
    def __init__(self, audio_config: Optional[AudioConfig] = None):
        if pyaudio is None:
            raise ImportError("pyaudio is required for microphone capture")
        
        self.audio_config = audio_config or AudioConfig()
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.callbacks = []
        self.logger = logger
    
    def add_callback(self, callback: Callable[[np.ndarray], None]):
        """Add callback for audio data"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[np.ndarray], None]):
        """Remove callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start_capture(self, device_index: Optional[int] = None) -> bool:
        """
        Start microphone capture
        
        Args:
            device_index: Audio device index (None for default)
            
        Returns:
            True if capture started successfully
        """
        if self.is_recording:
            self.logger.warning("Microphone capture already running")
            return True
        
        try:
            # Audio parameters
            chunk_size = 1024
            format_map = {
                1: pyaudio.paInt16,
                2: pyaudio.paInt16,
                4: pyaudio.paInt32
            }
            
            # Create stream
            self.stream = self.pyaudio.open(
                format=format_map.get(2, pyaudio.paInt16),
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            self.is_recording = True
            
            self.logger.info("Microphone capture started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start microphone capture: {e}")
            return False
    
    async def stop_capture(self):
        """Stop microphone capture"""
        if not self.is_recording:
            return
        
        try:
            self.is_recording = False
            
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            self.logger.info("Microphone capture stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping microphone capture: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        try:
            # Convert to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            
            # Reshape for channels
            if self.audio_config.channels == 2:
                audio_data = audio_data.reshape(-1, 2)
            
            # Call all callbacks
            for callback in self.callbacks:
                try:
                    callback(audio_data)
                except Exception as e:
                    self.logger.error(f"Error in audio callback: {e}")
            
            return (in_data, pyaudio.paContinue)
            
        except Exception as e:
            self.logger.error(f"Error in audio callback: {e}")
            return (in_data, pyaudio.paAbort)
    
    def list_devices(self) -> list:
        """List available audio devices"""
        devices = []
        
        try:
            for i in range(self.pyaudio.get_device_count()):
                device_info = self.pyaudio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
        except Exception as e:
            self.logger.error(f"Error listing devices: {e}")
        
        return devices
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'pyaudio') and self.pyaudio:
            self.pyaudio.terminate()


class MicrophoneStreamer:
    """Stream microphone to TgCaller"""
    
    def __init__(self, caller, chat_id: int):
        self.caller = caller
        self.chat_id = chat_id
        self.mic_capture = None
        self.is_streaming = False
    
    async def start_streaming(
        self, 
        audio_config: Optional[AudioConfig] = None,
        device_index: Optional[int] = None
    ) -> bool:
        """Start streaming microphone to call"""
        try:
            # Join call if not already joined
            if not self.caller.is_connected(self.chat_id):
                await self.caller.join_call(self.chat_id, audio_config=audio_config)
            
            # Setup microphone capture
            self.mic_capture = MicrophoneCapture(audio_config)
            self.mic_capture.add_callback(self._stream_audio)
            
            # Start capture
            success = await self.mic_capture.start_capture(device_index)
            if success:
                self.is_streaming = True
                logger.info(f"Started microphone streaming to chat {self.chat_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to start microphone streaming: {e}")
            return False
    
    async def stop_streaming(self):
        """Stop microphone streaming"""
        try:
            self.is_streaming = False
            
            if self.mic_capture:
                await self.mic_capture.stop_capture()
                self.mic_capture = None
            
            logger.info(f"Stopped microphone streaming to chat {self.chat_id}")
            
        except Exception as e:
            logger.error(f"Error stopping microphone streaming: {e}")
    
    def _stream_audio(self, audio_data: np.ndarray):
        """Stream audio data to call"""
        if self.is_streaming:
            # This would send audio_data to the call
            # Implementation depends on actual streaming protocol
            pass