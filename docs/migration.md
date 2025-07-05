# 🔄 Migration Guide: pytgcalls → TgCaller

## Quick Migration (2 minutes)

### Step 1: Install TgCaller
```bash
pip uninstall pytgcalls
pip install tgcaller
```

### Step 2: Update Imports
```python
# OLD
from pytgcalls import PyTgCalls
from pytgcalls.types import Update

# NEW
from tgcaller import TgCaller
from tgcaller.types import CallUpdate
```

### Step 3: Update Code
```python
# OLD
pytgcalls = PyTgCalls(app)

# NEW
caller = TgCaller(app)
```

## Complete Migration Examples

### Basic Audio Streaming

#### Before (pytgcalls):
```python
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped

pytgcalls = PyTgCalls(app)

@pytgcalls.on_stream_end()
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

await pytgcalls.start()
audio = AudioPiped("song.mp3")
await pytgcalls.join_group_call(chat_id, stream=audio)
```

#### After (TgCaller):
```python
from tgcaller import TgCaller, AudioConfig

caller = TgCaller(app)

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

await caller.start()
audio_config = AudioConfig.high_quality()
await caller.join_call(chat_id, audio_config=audio_config)
await caller.play(chat_id, "song.mp3")
```

### Video Streaming

#### Before (pytgcalls):
```python
from pytgcalls.types import AudioVideoPiped

video = AudioVideoPiped("video.mp4")
await pytgcalls.join_group_call(chat_id, stream=video)
```

#### After (TgCaller):
```python
from tgcaller import VideoConfig

video_config = VideoConfig.hd_720p()
await caller.join_call(chat_id, video_config=video_config)
await caller.play(chat_id, "video.mp4")
```

## Method Mapping

| pytgcalls | TgCaller | Notes |
|-----------|----------|-------|
| `PyTgCalls(app)` | `TgCaller(app)` | Direct replacement |
| `start()` | `start()` | Same |
| `join_group_call()` | `join_call()` | Simplified |
| `leave_group_call()` | `leave_call()` | Same |
| `change_stream()` | `play()` | More intuitive |
| `pause_stream()` | `pause()` | Simplified |
| `resume_stream()` | `resume()` | Simplified |

## Benefits After Migration

- **Simpler API** - Less boilerplate code
- **Better Performance** - Faster connection times
- **More Reliable** - Built-in error recovery
- **Better Documentation** - Comprehensive guides
- **Active Support** - Regular updates and community help

## Need Help?

- **[Documentation](https://tgcaller.github.io/TgCaller/)** - Complete guides
- **[Telegram Group](https://t.me/tgcaller)** - Get help from community
- **[GitHub Issues](https://github.com/TgCaller/TgCaller/issues)** - Report bugs