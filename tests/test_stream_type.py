"""
Test StreamType Enum
"""

import pytest
from tgcaller.types import StreamType


class TestStreamType:
    """Test StreamType enumeration"""
    
    def test_stream_type_values(self):
        """Test stream type values"""
        assert StreamType.AUDIO.value == "audio"
        assert StreamType.VIDEO.value == "video"
        assert StreamType.SCREEN.value == "screen"
        assert StreamType.MICROPHONE.value == "microphone"
        assert StreamType.CAMERA.value == "camera"
        assert StreamType.MIXED.value == "mixed"
        assert StreamType.RAW.value == "raw"
        assert StreamType.PIPED.value == "piped"
    
    def test_string_representation(self):
        """Test string representation"""
        assert str(StreamType.AUDIO) == "audio"
        assert str(StreamType.VIDEO) == "video"
    
    def test_has_audio_property(self):
        """Test has_audio property"""
        assert StreamType.AUDIO.has_audio is True
        assert StreamType.VIDEO.has_audio is True
        assert StreamType.MICROPHONE.has_audio is True
        assert StreamType.SCREEN.has_audio is False
        assert StreamType.CAMERA.has_audio is False
    
    def test_has_video_property(self):
        """Test has_video property"""
        assert StreamType.VIDEO.has_video is True
        assert StreamType.SCREEN.has_video is True
        assert StreamType.CAMERA.has_video is True
        assert StreamType.AUDIO.has_video is False
        assert StreamType.MICROPHONE.has_video is False
    
    def test_is_live_property(self):
        """Test is_live property"""
        assert StreamType.MICROPHONE.is_live is True
        assert StreamType.CAMERA.is_live is True
        assert StreamType.SCREEN.is_live is True
        assert StreamType.AUDIO.is_live is False
        assert StreamType.VIDEO.is_live is False
    
    def test_import_from_main_package(self):
        """Test importing StreamType from main package"""
        from tgcaller import StreamType as MainStreamType
        assert MainStreamType.AUDIO.value == "audio"