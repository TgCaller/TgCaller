# 📚 API Reference

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
- `chat_id`: Chat ID to join
- `audio_config`: Audio configuration (optional)
- `video_config`: Video configuration (optional)

**Returns:** `bool` - Success status

##### `leave_call(chat_id)`
Leave a call.

```python
await caller.leave_call(-1001234567890)
```

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
- `chat_id`: Chat ID
- `source`: Media source (file path or URL)
- `audio_config`: Audio configuration
- `video_config`: Video configuration

##### `pause(chat_id)`
Pause current stream.

```python
await caller.pause(-1001234567890)
```

##### `resume(chat_id)`
Resume paused stream.

```python
await caller.resume(-1001234567890)
```

##### `stop(chat_id)`
Stop current stream.

```python
await caller.stop(-1001234567890)
```

##### `set_volume(chat_id, volume)`
Set volume level (0.0 to 1.0).

```python
await caller.set_volume(-1001234567890, 0.8)
```

##### `seek(chat_id, position)`
Seek to position in seconds.

```python
await caller.seek(-1001234567890, 60.0)
```

##### `get_position(chat_id)`
Get current playback position.

```python
position = await caller.get_position(-1001234567890)
```

### Event Handlers

#### `@caller.on_stream_end`
Called when stream ends.

```python
@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")
```

#### `@caller.on_error`
Called when error occurs.

```python
@caller.on_error
async def on_error(client, error):
    print(f"Error: {error}")
```

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

#### `client`
Get Pyrogram client instance.

```python
pyrogram_client = caller.client
```

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

#### `get_active_calls()`
Get all active calls.

```python
active_calls = caller.get_active_calls()
print(f"Managing {len(active_calls)} calls")
```

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

**Presets:**
- `AudioConfig.high_quality()` - 128kbps, stereo, 48kHz
- `AudioConfig.low_bandwidth()` - 32kbps, mono, 24kHz

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

**Presets:**
- `VideoConfig.hd_720p()` - 1280x720, 30fps
- `VideoConfig.full_hd_1080p()` - 1920x1080, 30fps
- `VideoConfig.low_quality()` - 640x480, 15fps

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

## Utilities

### MediaUtils

```python
from tgcaller.utils import MediaUtils

# Get media information
info = await MediaUtils.get_media_info("video.mp4")

# Convert audio format
success = await MediaUtils.convert_audio(
    "input.mp3", "output.opus",
    bitrate=128000, sample_rate=48000
)

# Extract audio from video
success = await MediaUtils.extract_audio("video.mp4", "audio.opus")

# Download YouTube video
file_path = await MediaUtils.download_youtube(
    "https://youtube.com/watch?v=...", 
    "%(title)s.%(ext)s"
)
```

### Logger Setup

```python
from tgcaller.utils import setup_logger

logger = setup_logger(
    name="my_bot",
    level=logging.INFO,
    log_file="bot.log"
)
```