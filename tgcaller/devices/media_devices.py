"""
Media Devices Detection and Management
"""

import logging
from typing import List, Optional

from .device_info import InputDevice, SpeakerDevice, CameraDevice, ScreenDevice

logger = logging.getLogger(__name__)

# Optional imports
try:
    import pyaudio
except ImportError:
    pyaudio = None

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import mss
except ImportError:
    mss = None


class MediaDevices:
    """Media device detection and management"""
    
    @staticmethod
    def microphone_devices() -> List[InputDevice]:
        """
        Get list of available microphone devices
        
        Returns:
            List of InputDevice objects
        """
        devices = []
        
        if pyaudio is None:
            logger.warning("pyaudio not available, returning empty microphone list")
            return devices
        
        try:
            pa = pyaudio.PyAudio()
            
            for i in range(pa.get_device_count()):
                device_info = pa.get_device_info_by_index(i)
                
                # Only input devices
                if device_info['maxInputChannels'] > 0:
                    device = InputDevice(
                        index=i,
                        name=device_info['name'],
                        channels=device_info['maxInputChannels'],
                        sample_rate=device_info['defaultSampleRate'],
                        is_default=(i == pa.get_default_input_device_info()['index']),
                        metadata={
                            'host_api': device_info['hostApi'],
                            'max_input_channels': device_info['maxInputChannels'],
                            'default_low_input_latency': device_info['defaultLowInputLatency'],
                            'default_high_input_latency': device_info['defaultHighInputLatency']
                        }
                    )
                    devices.append(device)
            
            pa.terminate()
            
        except Exception as e:
            logger.error(f"Error detecting microphone devices: {e}")
        
        return devices
    
    @staticmethod
    def speaker_devices() -> List[SpeakerDevice]:
        """
        Get list of available speaker devices
        
        Returns:
            List of SpeakerDevice objects
        """
        devices = []
        
        if pyaudio is None:
            logger.warning("pyaudio not available, returning empty speaker list")
            return devices
        
        try:
            pa = pyaudio.PyAudio()
            
            for i in range(pa.get_device_count()):
                device_info = pa.get_device_info_by_index(i)
                
                # Only output devices
                if device_info['maxOutputChannels'] > 0:
                    device = SpeakerDevice(
                        index=i,
                        name=device_info['name'],
                        channels=device_info['maxOutputChannels'],
                        sample_rate=device_info['defaultSampleRate'],
                        is_default=(i == pa.get_default_output_device_info()['index']),
                        metadata={
                            'host_api': device_info['hostApi'],
                            'max_output_channels': device_info['maxOutputChannels'],
                            'default_low_output_latency': device_info['defaultLowOutputLatency'],
                            'default_high_output_latency': device_info['defaultHighOutputLatency']
                        }
                    )
                    devices.append(device)
            
            pa.terminate()
            
        except Exception as e:
            logger.error(f"Error detecting speaker devices: {e}")
        
        return devices
    
    @staticmethod
    def camera_devices() -> List[CameraDevice]:
        """
        Get list of available camera devices
        
        Returns:
            List of CameraDevice objects
        """
        devices = []
        
        if cv2 is None:
            logger.warning("opencv-python not available, returning empty camera list")
            return devices
        
        try:
            # Try to detect cameras (usually 0-9 are checked)
            for i in range(10):
                cap = cv2.VideoCapture(i)
                
                if cap.isOpened():
                    # Get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    device = CameraDevice(
                        index=i,
                        name=f"Camera {i}",
                        width=width if width > 0 else 640,
                        height=height if height > 0 else 480,
                        fps=fps if fps > 0 else 30.0,
                        is_default=(i == 0),
                        metadata={
                            'backend': cap.getBackendName(),
                            'fourcc': int(cap.get(cv2.CAP_PROP_FOURCC)),
                            'brightness': cap.get(cv2.CAP_PROP_BRIGHTNESS),
                            'contrast': cap.get(cv2.CAP_PROP_CONTRAST)
                        }
                    )
                    devices.append(device)
                
                cap.release()
                
        except Exception as e:
            logger.error(f"Error detecting camera devices: {e}")
        
        return devices
    
    @staticmethod
    def screen_devices() -> List[ScreenDevice]:
        """
        Get list of available screen devices
        
        Returns:
            List of ScreenDevice objects
        """
        devices = []
        
        if mss is None:
            logger.warning("mss not available, returning empty screen list")
            return devices
        
        try:
            with mss.mss() as sct:
                for i, monitor in enumerate(sct.monitors):
                    if i == 0:  # Skip "All in One" monitor
                        continue
                    
                    device = ScreenDevice(
                        index=i,
                        name=f"Screen {i}",
                        width=monitor['width'],
                        height=monitor['height'],
                        x=monitor['left'],
                        y=monitor['top'],
                        is_primary=(i == 1),  # Usually first real monitor is primary
                        metadata={
                            'monitor_info': monitor,
                            'pixel_ratio': 1.0  # Could be detected from system
                        }
                    )
                    devices.append(device)
                    
        except Exception as e:
            logger.error(f"Error detecting screen devices: {e}")
        
        return devices
    
    @staticmethod
    def get_default_microphone() -> Optional[InputDevice]:
        """Get default microphone device"""
        devices = MediaDevices.microphone_devices()
        for device in devices:
            if device.is_default:
                return device
        return devices[0] if devices else None
    
    @staticmethod
    def get_default_speaker() -> Optional[SpeakerDevice]:
        """Get default speaker device"""
        devices = MediaDevices.speaker_devices()
        for device in devices:
            if device.is_default:
                return device
        return devices[0] if devices else None
    
    @staticmethod
    def get_default_camera() -> Optional[CameraDevice]:
        """Get default camera device"""
        devices = MediaDevices.camera_devices()
        for device in devices:
            if device.is_default:
                return device
        return devices[0] if devices else None
    
    @staticmethod
    def get_primary_screen() -> Optional[ScreenDevice]:
        """Get primary screen device"""
        devices = MediaDevices.screen_devices()
        for device in devices:
            if device.is_primary:
                return device
        return devices[0] if devices else None