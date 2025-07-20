"""
Test Media Devices System
"""

import pytest
from unittest.mock import Mock, patch

from tgcaller.devices import MediaDevices, InputDevice, SpeakerDevice, CameraDevice, ScreenDevice


class TestMediaDevices:
    """Test Media Devices"""
    
    @patch('tgcaller.devices.media_devices.pyaudio')
    def test_microphone_devices_success(self, mock_pyaudio):
        """Test successful microphone detection"""
        # Mock pyaudio
        mock_pa = Mock()
        mock_pyaudio.PyAudio.return_value = mock_pa
        mock_pa.get_device_count.return_value = 2
        
        # Mock device info
        mock_pa.get_device_info_by_index.side_effect = [
            {
                'name': 'Microphone 1',
                'maxInputChannels': 1,
                'maxOutputChannels': 0,
                'defaultSampleRate': 48000.0,
                'hostApi': 0,
                'defaultLowInputLatency': 0.01,
                'defaultHighInputLatency': 0.1
            },
            {
                'name': 'Microphone 2',
                'maxInputChannels': 2,
                'maxOutputChannels': 0,
                'defaultSampleRate': 44100.0,
                'hostApi': 1,
                'defaultLowInputLatency': 0.02,
                'defaultHighInputLatency': 0.2
            }
        ]
        
        mock_pa.get_default_input_device_info.return_value = {'index': 0}
        
        # Test
        devices = MediaDevices.microphone_devices()
        
        assert len(devices) == 2
        assert isinstance(devices[0], InputDevice)
        assert devices[0].name == 'Microphone 1'
        assert devices[0].channels == 1
        assert devices[0].is_default is True
        assert devices[1].is_default is False
    
    @patch('tgcaller.devices.media_devices.pyaudio', None)
    def test_microphone_devices_no_pyaudio(self):
        """Test microphone detection without pyaudio"""
        devices = MediaDevices.microphone_devices()
        assert devices == []
    
    @patch('tgcaller.devices.media_devices.cv2')
    def test_camera_devices_success(self, mock_cv2):
        """Test successful camera detection"""
        # Mock camera capture
        mock_cap = Mock()
        mock_cv2.VideoCapture.return_value = mock_cap
        
        # First camera exists, second doesn't
        mock_cap.isOpened.side_effect = [True, False] + [False] * 8
        mock_cap.get.side_effect = [1920, 1080, 30.0]  # width, height, fps
        mock_cap.getBackendName.return_value = "DirectShow"
        
        # Test
        devices = MediaDevices.camera_devices()
        
        assert len(devices) == 1
        assert isinstance(devices[0], CameraDevice)
        assert devices[0].name == 'Camera 0'
        assert devices[0].width == 1920
        assert devices[0].height == 1080
        assert devices[0].fps == 30.0
        assert devices[0].is_default is True
    
    @patch('tgcaller.devices.media_devices.cv2', None)
    def test_camera_devices_no_opencv(self):
        """Test camera detection without opencv"""
        devices = MediaDevices.camera_devices()
        assert devices == []
    
    @patch('tgcaller.devices.media_devices.mss')
    def test_screen_devices_success(self, mock_mss_module):
        """Test successful screen detection"""
        # Mock mss
        mock_mss = Mock()
        mock_mss_module.mss.return_value.__enter__.return_value = mock_mss
        
        mock_mss.monitors = [
            {'left': 0, 'top': 0, 'width': 0, 'height': 0},  # "All in One" monitor
            {'left': 0, 'top': 0, 'width': 1920, 'height': 1080},  # Primary monitor
            {'left': 1920, 'top': 0, 'width': 1920, 'height': 1080}  # Secondary monitor
        ]
        
        # Test
        devices = MediaDevices.screen_devices()
        
        assert len(devices) == 2
        assert isinstance(devices[0], ScreenDevice)
        assert devices[0].name == 'Screen 1'
        assert devices[0].width == 1920
        assert devices[0].height == 1080
        assert devices[0].is_primary is True
        assert devices[1].is_primary is False
    
    @patch('tgcaller.devices.media_devices.mss', None)
    def test_screen_devices_no_mss(self):
        """Test screen detection without mss"""
        devices = MediaDevices.screen_devices()
        assert devices == []
    
    @patch('tgcaller.devices.media_devices.pyaudio')
    def test_get_default_microphone(self, mock_pyaudio):
        """Test getting default microphone"""
        # Mock pyaudio
        mock_pa = Mock()
        mock_pyaudio.PyAudio.return_value = mock_pa
        mock_pa.get_device_count.return_value = 2
        
        mock_pa.get_device_info_by_index.side_effect = [
            {
                'name': 'Mic 1',
                'maxInputChannels': 1,
                'maxOutputChannels': 0,
                'defaultSampleRate': 48000.0,
                'hostApi': 0,
                'defaultLowInputLatency': 0.01,
                'defaultHighInputLatency': 0.1
            },
            {
                'name': 'Mic 2',
                'maxInputChannels': 1,
                'maxOutputChannels': 0,
                'defaultSampleRate': 48000.0,
                'hostApi': 0,
                'defaultLowInputLatency': 0.01,
                'defaultHighInputLatency': 0.1
            }
        ]
        
        mock_pa.get_default_input_device_info.return_value = {'index': 1}
        
        # Test
        default_mic = MediaDevices.get_default_microphone()
        
        assert default_mic is not None
        assert default_mic.name == 'Mic 2'
        assert default_mic.is_default is True
    
    def test_device_info_properties(self):
        """Test device info properties"""
        # Test InputDevice
        input_device = InputDevice(
            index=0,
            name="Test Mic",
            channels=2,
            sample_rate=48000.0,
            metadata={}
        )
        assert input_device.is_video is False
        
        # Test CameraDevice
        camera_device = CameraDevice(
            index=0,
            name="Test Camera",
            width=1920,
            height=1080,
            fps=30.0,
            metadata={}
        )
        assert camera_device.is_video is True
        
        # Test ScreenDevice
        screen_device = ScreenDevice(
            index=1,
            name="Test Screen",
            width=1920,
            height=1080,
            x=0,
            y=0,
            metadata={}
        )
        assert screen_device.is_video is True