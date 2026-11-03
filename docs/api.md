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


## Incoming Audio Frames

The audio-only media engine can deliver decoded audio received from remote
participants through the `on_audio_frame` event.

Register an application handler with the decorator:

```python
@caller.on_audio_frame
async def on_audio_frame(client, chat_id, frame):
    # frame is an aiortc/av AudioFrame containing decoded remote audio.
    print(
        f"Audio received in {chat_id}: "
        f"{frame.samples} samples at {frame.sample_rate} Hz"
    )
```

The callback arguments are:

- `client`: the Pyrogram client passed to `TgCaller`.
- `chat_id`: the Telegram group-call chat ID.
- `frame`: a decoded `av.AudioFrame` supplied by aiortc.

The callback is invoked for remote audio tracks received by the joined call.
It is not a microphone-capture callback and does not report the audio that
your own client is publishing.

### Dispatch and backpressure

Incoming tracks are drained into a bounded per-call queue before application
callbacks run. The default queue capacity is 50 frames. If the queue is full,
the oldest queued frame is discarded so newer real-time audio can be delivered.
This favors low latency over preserving every frame during a slow consumer.

Async callbacks have a default execution timeout of 0.25 seconds. Callback
exceptions and async callback timeouts are logged and do not terminate the
remote track receive loop. Keep handlers short; for expensive processing,
enqueue work into an application-managed worker. Prefer `async def` handlers:
a synchronous handler executes on the event loop and cannot be interrupted by
the async callback timeout.

### Scope and verification

This API describes the implemented local aiortc receive/dispatch path.
A passing local RTP test does not establish Telegram live-call interoperability.
That still requires a live Telegram group call with valid API credentials and
an active call. The current media engine is audio-only; video receive/publish
is not documented as supported by this path.

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

### Incoming audio receive counters

Use `caller.get_audio_receive_stats(chat_id)` to read a snapshot of local
incoming audio counters. See [Incoming Audio](incoming-audio.md) for counter
definitions and limitations. A custom transport may return an empty mapping
when it does not implement this optional capability.
