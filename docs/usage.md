# Usage Guide

## Basic Usage

### Setting Up Your First Bot

```python
import asyncio
from pyrogram import Client
from tgcaller import TgCaller

# Your API credentials
API_ID = 12345
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

# Initialize Pyrogram client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Initialize TgCaller
caller = TgCaller(app)

async def main():
    # Start TgCaller
    await caller.start()
    
    # Your bot logic here
    chat_id = -1001234567890  # Your group chat ID
    
    # Join voice call
    await caller.join_call(chat_id)
    
    # Play audio file
    await caller.play(chat_id, "song.mp3")
    
    # Keep running
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Audio Configuration

### Quality Presets

```python
from tgcaller import AudioConfig

# High quality audio (128kbps, stereo, 48kHz)
audio_config = AudioConfig.high_quality()

# Low bandwidth audio (32kbps, mono, 24kHz)
audio_config = AudioConfig.low_bandwidth()

# Voice call optimized
audio_config = AudioConfig.voice_call()
```

### Custom Audio Configuration

```python
audio_config = AudioConfig(
    bitrate=128000,           # 128 kbps
    sample_rate=48000,        # 48 kHz
    channels=2,               # Stereo
    noise_suppression=True,   # Clean audio
    echo_cancellation=True    # No echo
)

await caller.play(chat_id, "song.mp3", audio_config=audio_config)
```

## Video Configuration

### Video Presets

```python
from tgcaller import VideoConfig

# HD 720p video
video_config = VideoConfig.hd_720p()

# Full HD 1080p video
video_config = VideoConfig.full_hd_1080p()

# Low quality for poor connections
video_config = VideoConfig.low_quality()
```

### Custom Video Configuration

```python
video_config = VideoConfig(
    width=1920,
    height=1080,
    fps=30,
    bitrate=2000000,          # 2 Mbps
    codec="h264"
)

await caller.play(chat_id, "video.mp4", video_config=video_config)
```

## Event Handling

### Stream Events

```python
@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")
    # Auto-play next song
    await caller.play(update.chat_id, "next_song.mp3")

@caller.on_stream_start
async def on_stream_start(client, update):
    print(f"Stream started in {update.chat_id}")

@caller.on_error
async def on_error(client, error):
    print(f"Error occurred: {error}")
```

### Call Events

```python
@caller.on_kicked
async def on_kicked(client, update):
    print(f"Kicked from {update.chat_id}")

@caller.on_left
async def on_left(client, update):
    print(f"Left call {update.chat_id}")
```

## Stream Control

### Basic Controls

```python
# Pause stream
await caller.pause(chat_id)

# Resume stream
await caller.resume(chat_id)

# Stop stream
await caller.stop_stream(chat_id)

# Set volume (0.0 to 1.0)
await caller.set_volume(chat_id, 0.8)

# Seek to position (in seconds)
await caller.seek(chat_id, 60.0)

# Get current position
position = await caller.get_position(chat_id)
```

## Music Bot Example

```python
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig

app = Client("music_bot")
caller = TgCaller(app)

@app.on_message(filters.command("play"))
async def play_music(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /play <song_name>")
    
    song = message.command[1]
    chat_id = message.chat.id
    
    # Join call if not already joined
    if not caller.is_connected(chat_id):
        await caller.join_call(chat_id)
        await message.reply("📞 Joined voice chat!")
    
    # Play song
    audio_config = AudioConfig.high_quality()
    await caller.play(chat_id, f"music/{song}.mp3", audio_config=audio_config)
    await message.reply(f"🎵 Playing: {song}")

@app.on_message(filters.command("pause"))
async def pause_music(client, message):
    if await caller.pause(message.chat.id):
        await message.reply("⏸️ Music paused")

@app.on_message(filters.command("resume"))
async def resume_music(client, message):
    if await caller.resume(message.chat.id):
        await message.reply("▶️ Music resumed")

@app.on_message(filters.command("stop"))
async def stop_music(client, message):
    if await caller.stop_stream(message.chat.id):
        await message.reply("⏹️ Music stopped")

@app.on_message(filters.command("leave"))
async def leave_call(client, message):
    if await caller.leave_call(message.chat.id):
        await message.reply("👋 Left voice chat")

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

app.run()
```

## Advanced Features

### YouTube Streaming

```python
from tgcaller.advanced import YouTubeStreamer

youtube = YouTubeStreamer(caller)

# Play YouTube video directly
await youtube.play_youtube_url(chat_id, "https://youtube.com/watch?v=...")

# Search and play
await youtube.search_and_play(chat_id, "relaxing music", index=0)
```

### Screen Sharing

```python
from tgcaller.advanced import ScreenShareStreamer

screen_streamer = ScreenShareStreamer(caller, chat_id)

# Start screen sharing
await screen_streamer.start_streaming(monitor_index=1)

# Stop screen sharing
await screen_streamer.stop_streaming()
```

### Microphone Streaming

```python
from tgcaller.advanced import MicrophoneStreamer

mic_streamer = MicrophoneStreamer(caller, chat_id)

# Start microphone streaming
await mic_streamer.start_streaming()

# Stop microphone streaming
await mic_streamer.stop_streaming()
```

### Audio Filters

```python
from tgcaller.advanced import AudioFilters, FilterChain

# Create filter chain
filter_chain = FilterChain()
audio_filters = AudioFilters()

# Add echo effect
filter_chain.add_audio_filter(
    audio_filters.apply_echo,
    delay=0.3,
    decay=0.5
)

# Add reverb effect
filter_chain.add_audio_filter(
    audio_filters.apply_reverb,
    room_size=0.7,
    damping=0.4
)

# Process audio through filters
filtered_audio = filter_chain.process_audio(audio_data)
```

## Error Handling

```python
from tgcaller.exceptions import TgCallerError, ConnectionError, MediaError

try:
    await caller.play(chat_id, "song.mp3")
except MediaError as e:
    print(f"Media error: {e}")
except ConnectionError as e:
    print(f"Connection error: {e}")
except TgCallerError as e:
    print(f"TgCaller error: {e}")
```

## Best Practices

### 1. Always Handle Errors

```python
try:
    await caller.join_call(chat_id)
except Exception as e:
    print(f"Failed to join call: {e}")
```

### 2. Check Connection Status

```python
if not caller.is_connected(chat_id):
    await caller.join_call(chat_id)
```

### 3. Cleanup Resources

```python
async def cleanup():
    # Leave all calls
    for chat_id in caller.get_active_calls():
        await caller.leave_call(chat_id)
    
    # Stop TgCaller
    await caller.stop()
```

### 4. Use Appropriate Quality Settings

```python
# For music streaming
audio_config = AudioConfig.high_quality()

# For voice calls
audio_config = AudioConfig.voice_call()

# For poor connections
audio_config = AudioConfig.low_bandwidth()
```