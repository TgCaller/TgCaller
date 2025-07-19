# Python API Reference

TgCaller provides a comprehensive Python API for building Telegram voice and video call applications.

## Quick Overview

The main entry point is the `TgCaller` class, which provides methods for call management, media streaming, and event handling.

```python
from pyrogram import Client
from tgcaller import TgCaller, AudioConfig, VideoConfig

# Initialize
app = Client("my_session", api_id=API_ID, api_hash=API_HASH)
caller = TgCaller(app)

# Event handlers
@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

# Basic usage
await caller.start()
await caller.join_call(chat_id)
await caller.play(chat_id, "media.mp3")
```

## Core Classes

### TgCaller

The main client class for managing Telegram group calls.

**Key Methods:**
- `start()` - Initialize TgCaller service
- `stop()` - Stop service and cleanup
- `join_call(chat_id, audio_config, video_config)` - Join voice/video call
- `leave_call(chat_id)` - Leave call
- `play(chat_id, source, audio_config, video_config)` - Play media
- `pause(chat_id)` - Pause current stream
- `resume(chat_id)` - Resume paused stream
- `set_volume(chat_id, volume)` - Set volume (0.0-1.0)

### Configuration Classes

#### AudioConfig

Configure audio quality and processing options.

```python
# Presets
config = AudioConfig.high_quality()    # 128kbps, stereo, 48kHz
config = AudioConfig.low_bandwidth()   # 32kbps, mono, 24kHz
config = AudioConfig.voice_call()      # 64kbps, mono, optimized

# Custom configuration
config = AudioConfig(
    bitrate=128000,
    sample_rate=48000,
    channels=2,
    noise_suppression=True,
    echo_cancellation=True
)
```

#### VideoConfig

Configure video quality and encoding options.

```python
# Presets
config = VideoConfig.hd_720p()         # 1280x720, 30fps
config = VideoConfig.full_hd_1080p()   # 1920x1080, 30fps
config = VideoConfig.low_quality()     # 640x480, 15fps

# Custom configuration
config = VideoConfig(
    width=1920,
    height=1080,
    fps=30,
    bitrate=2000000,
    codec="h264"
)
```

### MediaStream

Represents a media source for streaming.

```python
from tgcaller import MediaStream

# File stream
stream = MediaStream("audio.mp3")

# URL stream
stream = MediaStream("https://example.com/stream.mp3")

# Advanced configuration
stream = MediaStream(
    source="video.mp4",
    audio_config=AudioConfig.high_quality(),
    video_config=VideoConfig.hd_720p(),
    repeat=True,
    start_time=30.0  # Start at 30 seconds
)
```

## Event Handling

TgCaller provides decorators for handling various events:

### Stream Events

```python
@caller.on_stream_start
async def on_stream_start(client, update):
    print(f"Stream started in {update.chat_id}")

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")
    # Auto-play next song
    await caller.play(update.chat_id, "next_song.mp3")

@caller.on_stream_paused
async def on_stream_paused(client, update):
    print(f"Stream paused in {update.chat_id}")

@caller.on_stream_resumed
async def on_stream_resumed(client, update):
    print(f"Stream resumed in {update.chat_id}")
```

### Call Events

```python
@caller.on_kicked
async def on_kicked(client, update):
    print(f"Kicked from call in {update.chat_id}")
    # Attempt to rejoin
    await caller.join_call(update.chat_id)

@caller.on_left
async def on_left(client, update):
    print(f"Left call in {update.chat_id}")

@caller.on_error
async def on_error(client, error):
    print(f"Error occurred: {error}")
```

## Status and Information

### Connection Status

```python
# Check if TgCaller is running
if caller.is_running:
    print("TgCaller is active")

# Check specific call connection
if caller.is_connected(chat_id):
    print(f"Connected to call in {chat_id}")

# Get all active calls
active_calls = caller.get_active_calls()
print(f"Managing {len(active_calls)} calls")
```

### Stream Information

```python
# Get current stream position
position = await caller.get_position(chat_id)
print(f"Current position: {position:.1f} seconds")

# Check if media has video
stream = MediaStream("video.mp4")
if stream.has_video:
    print("This stream contains video")
```

## Error Handling

TgCaller provides specific exception types for different error scenarios:

```python
from tgcaller.exceptions import (
    TgCallerError,
    ConnectionError,
    MediaError,
    CallError,
    StreamError
)

try:
    await caller.play(chat_id, "nonexistent.mp3")
except MediaError as e:
    print(f"Media error: {e}")
except CallError as e:
    print(f"Call error: {e}")
except TgCallerError as e:
    print(f"General TgCaller error: {e}")
```

## Advanced Features

For advanced functionality, see the [Advanced Features](advanced.md) guide which covers:

- YouTube integration
- Screen sharing
- Microphone streaming
- Speech transcription
- Audio/video filters
- Bridged calls
- Custom API endpoints

## Type Hints

TgCaller is fully typed for better IDE support:

```python
from typing import Optional
from tgcaller import TgCaller, AudioConfig

async def setup_call(
    caller: TgCaller, 
    chat_id: int, 
    audio_config: Optional[AudioConfig] = None
) -> bool:
    """Setup and join a call with optional audio configuration."""
    try:
        return await caller.join_call(chat_id, audio_config=audio_config)
    except Exception as e:
        print(f"Failed to setup call: {e}")
        return False
```

## Best Practices

### Resource Management

```python
async def main():
    caller = TgCaller(app)
    
    try:
        await caller.start()
        # Your application logic here
        
    finally:
        # Always cleanup
        await caller.stop()
```

### Error Recovery

```python
@caller.on_error
async def handle_error(client, error):
    """Implement error recovery logic."""
    if isinstance(error, ConnectionError):
        # Attempt reconnection
        await asyncio.sleep(5)
        await caller.start()
```

### Performance Optimization

```python
# Use appropriate quality settings
audio_config = AudioConfig.low_bandwidth()  # For poor connections
video_config = VideoConfig.mobile_optimized()  # For mobile users

# Check connection before operations
if caller.is_connected(chat_id):
    await caller.play(chat_id, media)
else:
    await caller.join_call(chat_id)
    await caller.play(chat_id, media)
```

This API reference provides the foundation for building powerful Telegram call applications with TgCaller.