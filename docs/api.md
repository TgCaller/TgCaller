# API Reference

## TgCaller Class

### Constructor

```python
TgCaller(client: Client, log_level: int = logging.WARNING)
```

**Parameters:**
- `client`: Pyrogram Client instance
- `log_level`: Logging level (default: WARNING)

### Methods

#### Connection Methods

##### `start()`
Start TgCaller service.

```python
await caller.start()
```

**Raises:**
- `ConnectionError`: If failed to start

##### `stop()`
Stop TgCaller service and cleanup resources.

```python
await caller.stop()
```

#### Call Management

##### `join_call(chat_id, audio_config=None, video_config=None)`
Join a voice/video call.

```python
await caller.join_call(
    chat_id=-1001234567890,
    audio_config=AudioConfig.high_quality(),
    video_config=VideoConfig.hd_720p()
)
```

**Parameters:**
- `chat_id` (int): Chat ID to join
- `audio_config` (AudioConfig, optional): Audio configuration
- `video_config` (VideoConfig, optional): Video configuration

**Returns:** `bool` - Success status

**Raises:**
- `ConnectionError`: If not connected to Telegram
- `CallError`: If failed to join call

##### `leave_call(chat_id)`
Leave a call.

```python
await caller.leave_call(-1001234567890)
```

**Parameters:**
- `chat_id` (int): Chat ID to leave

**Returns:** `bool` - Success status

#### Stream Control

##### `play(chat_id, source, audio_config=None, video_config=None)`
Play media in call.

```python
await caller.play(
    chat_id=-1001234567890,
    source="song.mp3",
    audio_config=AudioConfig.high_quality()
)
```

**Parameters:**
- `chat_id` (int): Chat ID
- `source` (str | Path | MediaStream): Media source (file path or URL)
- `audio_config` (AudioConfig, optional): Audio configuration
- `video_config` (VideoConfig, optional): Video configuration

**Returns:** `bool` - Success status

**Raises:**
- `StreamError`: If failed to play media
- `MediaError`: If media source is invalid

##### `pause(chat_id)`
Pause current stream.

```python
await caller.pause(-1001234567890)
```

**Parameters:**
- `chat_id` (int): Chat ID

**Returns:** `bool` - Success status

##### `resume(chat_id)`
Resume paused stream.

```python
await caller.resume(-1001234567890)
```

**Parameters:**
- `chat_id` (int): Chat ID

**Returns:** `bool` - Success status

##### `stop_stream(chat_id)`
Stop current stream.

```python
await caller.stop_stream(-1001234567890)
```

**Parameters:**
- `chat_id` (int): Chat ID

**Returns:** `bool` - Success status

##### `set_volume(chat_id, volume)`
Set volume level (0.0 to 1.0).

```python
await caller.set_volume(-1001234567890, 0.8)
```

**Parameters:**
- `chat_id` (int): Chat ID
- `volume` (float): Volume level (0.0 to 1.0)

**Returns:** `bool` - Success status

**Raises:**
- `ValueError`: If volume is not between 0.0 and 1.0

##### `seek(chat_id, position)`
Seek to position in seconds.

```python
await caller.seek(-1001234567890, 60.0)
```

**Parameters:**
- `chat_id` (int): Chat ID
- `position` (float): Position in seconds

**Returns:** `bool` - Success status

##### `get_position(chat_id)`
Get current playback position.

```python
position = await caller.get_position(-1001234567890)
```

**Parameters:**
- `chat_id` (int): Chat ID

**Returns:** `float | None` - Current position in seconds

### Event Handlers

#### `@caller.on_stream_end`
Called when stream ends.

```python
@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")
```

**Parameters:**
- `client`: Pyrogram client instance
- `update` (CallUpdate): Update information

#### `@caller.on_stream_start`
Called when stream starts.

```python
@caller.on_stream_start
async def on_stream_start(client, update):
    print(f"Stream started in {update.chat_id}")
```

#### `@caller.on_error`
Called when error occurs.

```python
@caller.on_error
async def on_error(client, error):
    print(f"Error: {error}")
```

**Parameters:**
- `client`: Pyrogram client instance
- `error` (Exception): Error that occurred

#### `@caller.on_kicked`
Called when kicked from call.

```python
@caller.on_kicked
async def on_kicked(client, update):
    print(f"Kicked from {update.chat_id}")
```

#### `@caller.on_left`
Called when left call.

```python
@caller.on_left
async def on_left(client, update):
    print(f"Left call {update.chat_id}")
```

### Properties

#### `is_running`
Check if TgCaller is running.

```python
if caller.is_running:
    print("TgCaller is active")
```

**Returns:** `bool`

#### `client`
Get Pyrogram client instance.

```python
pyrogram_client = caller.client
```

**Returns:** `Client`

### Utility Methods

#### `is_connected(chat_id=None)`
Check connection status.

```python
# Check if TgCaller is connected
if caller.is_connected():
    print("Connected")

# Check specific chat
if caller.is_connected(-1001234567890):
    print("Connected to chat")
```

**Parameters:**
- `chat_id` (int, optional): Specific chat ID to check

**Returns:** `bool`

#### `get_active_calls()`
Get all active calls.

```python
active_calls = caller.get_active_calls()
print(f"Managing {len(active_calls)} calls")
```

**Returns:** `List[int]` - List of chat IDs with active calls

## Configuration Classes

### AudioConfig

```python
AudioConfig(
    bitrate: int = 48000,
    channels: int = 2,
    sample_rate: int = 48000,
    codec: str = "opus",
    noise_suppression: bool = False,
    echo_cancellation: bool = True,
    auto_gain_control: bool = True
)
```

**Parameters:**
- `bitrate` (int): Audio bitrate in bps (8000-320000)
- `channels` (int): Number of channels (1=mono, 2=stereo)
- `sample_rate` (int): Sample rate in Hz (8000, 16000, 24000, 48000)
- `codec` (str): Audio codec ("opus", "aac")
- `noise_suppression` (bool): Enable noise suppression
- `echo_cancellation` (bool): Enable echo cancellation
- `auto_gain_control` (bool): Enable automatic gain control

**Presets:**
- `AudioConfig.high_quality()` - 128kbps, stereo, 48kHz
- `AudioConfig.low_bandwidth()` - 32kbps, mono, 24kHz
- `AudioConfig.voice_call()` - 64kbps, mono, 48kHz

### VideoConfig

```python
VideoConfig(
    width: int = 1280,
    height: int = 720,
    fps: int = 30,
    bitrate: int = 1000000,
    codec: str = "h264",
    hardware_acceleration: bool = True
)
```

**Parameters:**
- `width` (int): Video width in pixels (320-1920)
- `height` (int): Video height in pixels (240-1080)
- `fps` (int): Frame rate (15, 24, 30, 60)
- `bitrate` (int): Video bitrate in bps (100000-5000000)
- `codec` (str): Video codec ("h264", "vp8")
- `hardware_acceleration` (bool): Enable hardware acceleration

**Presets:**
- `VideoConfig.hd_720p()` - 1280x720, 30fps
- `VideoConfig.full_hd_1080p()` - 1920x1080, 30fps
- `VideoConfig.low_quality()` - 640x480, 15fps
- `VideoConfig.mobile_optimized()` - 854x480, 24fps

### MediaStream

```python
MediaStream(
    source: Union[str, Path],
    audio_config: Optional[AudioConfig] = None,
    video_config: Optional[VideoConfig] = None,
    repeat: bool = False,
    start_time: Optional[float] = None,
    duration: Optional[float] = None
)
```

**Parameters:**
- `source`: Path to media file or stream URL
- `audio_config`: Audio configuration
- `video_config`: Video configuration
- `repeat`: Repeat the stream when it ends
- `start_time`: Start time in seconds
- `duration`: Duration in seconds

**Properties:**
- `has_video` - Check if stream has video
- `is_file` - Check if source is a file
- `is_url` - Check if source is a URL

### CallUpdate

```python
CallUpdate(
    chat_id: int,
    status: CallStatus,
    user_id: Optional[int] = None,
    message: Optional[str] = None,
    error: Optional[Exception] = None,
    metadata: Optional[Dict[str, Any]] = None
)
```

**Parameters:**
- `chat_id`: Chat ID where the call is happening
- `status`: Current call status
- `user_id`: User ID (for user-specific updates)
- `message`: Update message
- `error`: Error information if status is ERROR
- `metadata`: Additional metadata

**Properties:**
- `is_error` - Check if update is an error
- `is_active` - Check if call is active

### CallStatus (Enum)

- `IDLE` - Not in call
- `CONNECTING` - Connecting to call
- `CONNECTED` - Connected to call
- `PLAYING` - Playing media
- `PAUSED` - Media paused
- `ENDED` - Call ended
- `ERROR` - Error occurred

### StreamType (Enum)

- `AUDIO` - Audio only stream
- `VIDEO` - Video stream (includes audio)
- `SCREEN` - Screen sharing stream
- `MICROPHONE` - Live microphone input
- `CAMERA` - Live camera input
- `MIXED` - Mixed audio/video stream
- `RAW` - Raw stream data
- `PIPED` - Piped stream from external source

## Exceptions

### TgCallerError
Base exception for all TgCaller errors.

### ConnectionError
Connection-related errors.

### MediaError
Media processing errors.

### CallError
Call management errors.

### StreamError
Stream control errors.

### ConfigurationError
Configuration validation errors.

## Advanced Features

### YouTube Integration

```python
from tgcaller.advanced import YouTubeDownloader, YouTubeStreamer

# Download YouTube videos
downloader = YouTubeDownloader()
file_path = await downloader.download_video("https://youtube.com/watch?v=...")

# Stream YouTube videos
youtube = YouTubeStreamer(caller)
await youtube.play_youtube_url(chat_id, "https://youtube.com/watch?v=...")
```

### Screen Sharing

```python
from tgcaller.advanced import ScreenShare, ScreenShareStreamer

# List available monitors
screen_share = ScreenShare()
monitors = screen_share.list_monitors()

# Start screen sharing
streamer = ScreenShareStreamer(caller, chat_id)
await streamer.start_streaming(monitor_index=1)
```

### Audio Filters

```python
from tgcaller.advanced import AudioFilters, VideoFilters

audio_filters = AudioFilters()
video_filters = VideoFilters()

# Apply audio effects
echo_audio = audio_filters.apply_echo(audio_data, delay=0.3)
reverb_audio = audio_filters.apply_reverb(audio_data, room_size=0.7)

# Apply video effects
blurred_video = video_filters.apply_blur(video_frame, kernel_size=15)
sepia_video = video_filters.apply_sepia(video_frame)
```

### Transcription

```python
from tgcaller.advanced import WhisperTranscription

transcriber = WhisperTranscription("base")
result = await transcriber.transcribe_file("audio.wav")
print(result['text'])
```