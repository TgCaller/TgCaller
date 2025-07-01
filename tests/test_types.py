"""
Test TgCaller Types
"""

import pytest
from tgcaller.types import AudioConfig, VideoConfig, MediaStream, CallUpdate, CallStatus


class TestAudioConfig:
    """Test AudioConfig"""
    
    def test_default_config(self):
        """Test default audio configuration"""
        config = AudioConfig()
        assert config.bitrate == 48000
        assert config.channels == 2
        assert config.sample_rate == 48000
        assert config.codec == "opus"
    
    def test_high_quality_preset(self):
        """Test high quality preset"""
        config = AudioConfig.high_quality()
        assert config.bitrate == 128000
        assert config.sample_rate == 48000
        assert config.channels == 2
    
    def test_low_bandwidth_preset(self):
        """Test low bandwidth preset"""
        config = AudioConfig.low_bandwidth()
        assert config.bitrate == 32000
        assert config.sample_rate == 24000
        assert config.channels == 1
    
    def test_invalid_bitrate(self):
        """Test invalid bitrate validation"""
        with pytest.raises(ValueError):
            AudioConfig(bitrate=1000)  # Too low
        
        with pytest.raises(ValueError):
            AudioConfig(bitrate=500000)  # Too high
    
    def test_invalid_channels(self):
        """Test invalid channels validation"""
        with pytest.raises(ValueError):
            AudioConfig(channels=3)  # Invalid
    
    def test_invalid_codec(self):
        """Test invalid codec validation"""
        with pytest.raises(ValueError):
            AudioConfig(codec="mp3")  # Invalid


class TestVideoConfig:
    """Test VideoConfig"""
    
    def test_default_config(self):
        """Test default video configuration"""
        config = VideoConfig()
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 30
        assert config.codec == "h264"
    
    def test_hd_720p_preset(self):
        """Test 720p HD preset"""
        config = VideoConfig.hd_720p()
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 30
    
    def test_full_hd_1080p_preset(self):
        """Test 1080p Full HD preset"""
        config = VideoConfig.full_hd_1080p()
        assert config.width == 1920
        assert config.height == 1080
        assert config.fps == 30
    
    def test_resolution_property(self):
        """Test resolution property"""
        config = VideoConfig(width=1920, height=1080)
        assert config.resolution == (1920, 1080)
    
    def test_invalid_dimensions(self):
        """Test invalid dimensions validation"""
        with pytest.raises(ValueError):
            VideoConfig(width=100)  # Too small
        
        with pytest.raises(ValueError):
            VideoConfig(height=100)  # Too small


class TestMediaStream:
    """Test MediaStream"""
    
    def test_file_stream(self):
        """Test file-based media stream"""
        stream = MediaStream("test.mp3")
        assert stream.source == "test.mp3"
        assert stream.audio_config is not None
    
    def test_url_stream(self):
        """Test URL-based media stream"""
        stream = MediaStream("https://example.com/video.mp4")
        assert stream.is_url
        assert stream.has_video
    
    def test_video_detection(self):
        """Test video format detection"""
        video_stream = MediaStream("video.mp4")
        assert video_stream.has_video
        
        audio_stream = MediaStream("audio.mp3")
        assert not audio_stream.has_video


class TestCallUpdate:
    """Test CallUpdate"""
    
    def test_basic_update(self):
        """Test basic call update"""
        update = CallUpdate(
            chat_id=-1001234567890,
            status=CallStatus.CONNECTED,
            message="Connected to call"
        )
        
        assert update.chat_id == -1001234567890
        assert update.status == CallStatus.CONNECTED
        assert update.is_active
        assert not update.is_error
    
    def test_error_update(self):
        """Test error call update"""
        error = Exception("Test error")
        update = CallUpdate(
            chat_id=-1001234567890,
            status=CallStatus.ERROR,
            error=error
        )
        
        assert update.is_error
        assert not update.is_active
        assert update.error == error