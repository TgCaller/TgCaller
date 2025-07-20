"""
TgCaller Types
"""

from .audio_config import AudioConfig
from .video_config import VideoConfig
from .media_stream import MediaStream
from .call_update import CallUpdate, CallStatus
from .stream_type import StreamType
from .group_call_participant import GroupCallParticipant, UpdatedGroupCallParticipant, ParticipantAction, VideoInfo
from .stream_quality import AudioQuality, VideoQuality, QualityConfig
from .frame import Frame, FrameInfo, StreamFrames
from .device import Device, DeviceType, Direction, ExternalMedia
from .record_stream import RecordStream, RecordingFormat, RecordingStatus
from .stream_ended import StreamEnded, StreamEndReason

__all__ = [
    "AudioConfig",
    "VideoConfig", 
    "MediaStream",
    "CallUpdate",
    "CallStatus",
    "StreamType",
    "GroupCallParticipant",
    "UpdatedGroupCallParticipant", 
    "ParticipantAction",
    "VideoInfo",
    "AudioQuality",
    "VideoQuality",
    "QualityConfig",
    "Frame",
    "FrameInfo", 
    "StreamFrames",
    "Device",
    "DeviceType",
    "Direction",
    "ExternalMedia",
    "RecordStream",
    "RecordingFormat",
    "RecordingStatus",
    "StreamEnded",
    "StreamEndReason",
]