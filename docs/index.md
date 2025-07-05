# TgCaller

<!--
  PROBLEM FIX:
  1. Do not use <div> with markdown badges inside. Use pure markdown for badges, then optionally use <div align="center"> only for text/buttons if needed.
  2. Avoid HTML wrappers around badges, as Material for MkDocs disables markdown parsing inside HTML. 
-->

[![PyPI](https://img.shields.io/pypi/v/tgcaller?style=for-the-badge)](https://pypi.org/project/tgcaller/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-00d4aa?style=for-the-badge)](https://github.com/TgCaller/TgCaller/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/tgcaller?style=for-the-badge&color=blue)](https://pypi.org/project/tgcaller/)
[![GitHub Stars](https://img.shields.io/github/stars/TgCaller/TgCaller?style=for-the-badge&logo=github)](https://github.com/TgCaller/TgCaller)

<div align="center">

**🎯 Modern, Fast, and Reliable Telegram Group Calls Library**

*Built for developers who need a simple yet powerful solution for Telegram voice and video calls*

[**Get Started**](installation.md){ .md-button .md-button--primary }
[**View on GitHub**](https://github.com/TgCaller/TgCaller){ .md-button }

</div>

---

## ⚡ Why TgCaller?

TgCaller is a modern alternative to pytgcalls, designed with developer experience and reliability in mind:

<!--
  PROBLEM FIX:
  3. For feature cards, Material for MkDocs disables markdown inside HTML.
     For best cross-compatibility, use pure markdown for features, or keep as is if you are happy with simple HTML fallback.
-->

- 🚀 **Fast & Lightweight**: Optimized performance, 3x faster connection times compared to alternatives.
- 📱 **Easy to Use**: Simple, intuitive API with less boilerplate code, more functionality.
- 🔧 **Reliable**: Built-in error handling and auto-recovery. <2% error rate in production environments.
- 📹 **HD Support**: High-quality audio and video streaming with support for 720p and 1080p video calls.
- 🔌 **Extensible**: Plugin system for custom features. Extend functionality without modifying core code.
- 📚 **Well Documented**: Comprehensive guides and examples. Complete API reference with interactive examples.

---

## 🚀 Quick Start

### Installation

=== "PyPI"

    ```bash
    pip install tgcaller
    ```

=== "With Video Support"

    ```bash
    pip install tgcaller[media]
    ```

=== "Complete Installation"

    ```bash
    pip install tgcaller[all]
    ```

### Basic Usage

```python
import asyncio
from pyrogram import Client
from tgcaller import TgCaller

# Initialize
app = Client("my_session", api_id=API_ID, api_hash=API_HASH)
caller = TgCaller(app)

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

async def main():
    await caller.start()
    
    # Join voice call
    await caller.join_call(-1001234567890)
    
    # Play audio
    await caller.play(-1001234567890, "song.mp3")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎵 Features

### Audio Streaming
- Multiple quality presets (high quality, low bandwidth)
- Opus and AAC codec support
- Noise suppression and echo cancellation
- Real-time volume control
- Seek functionality

### Video Streaming
- 720p and 1080p HD support
- H.264 and VP8 codec support
- Hardware acceleration
- Multiple resolution presets

### Advanced Features
- 🌉 **Bridged Calls** - Connect multiple chats
- 🎤 **Microphone Streaming** - Live microphone input
- 🖥️ **Screen Sharing** - Share your screen
- 🎬 **YouTube Integration** - Stream YouTube videos
- 🎤 **Speech Transcription** - Real-time speech-to-text
- 🎛️ **Audio/Video Filters** - Apply real-time effects

---

## 📊 Performance Comparison

| Feature            | TgCaller | pytgcalls | Improvement      |
|--------------------|---------|-----------|------------------|
| **Connection Time**| ~1s     | ~3s       | 3x faster        |
| **Memory Usage**   | 80MB    | 150MB     | 47% less         |
| **CPU Usage**      | Low     | High      | 60% less         |
| **Error Rate**     | <2%     | ~8%       | 4x more reliable |

---

## 🎮 Examples

### Music Bot

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

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

app.run()
```

### Advanced Features

```python
from tgcaller.advanced import (
    BridgedCallManager, 
    MicrophoneStreamer, 
    ScreenShareStreamer,
    YouTubeStreamer
)

# Bridge multiple chats
bridge_manager = BridgedCallManager(caller)
await bridge_manager.create_bridge("conference", [chat1, chat2, chat3])

# Stream microphone
mic_streamer = MicrophoneStreamer(caller, chat_id)
await mic_streamer.start_streaming()

# Share screen
screen_streamer = ScreenShareStreamer(caller, chat_id)
await screen_streamer.start_streaming(monitor_index=1)

# Stream YouTube
youtube = YouTubeStreamer(caller)
await youtube.play_youtube_url(chat_id, "https://youtube.com/watch?v=...")
```

---

## 🤝 Community

[![GitHub](https://img.shields.io/badge/GitHub-TgCaller-181717?style=for-the-badge&logo=github)](https://github.com/TgCaller/TgCaller)
[![Telegram](https://img.shields.io/badge/Telegram-@TgCallerOfficial-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/TgCallerOfficial)
[![PyPI](https://img.shields.io/badge/PyPI-tgcaller-3775A9?style=for-the-badge&logo=pypi&logoColor=white)](https://pypi.org/project/tgcaller/)

- **[GitHub](https://github.com/TgCaller/TgCaller)** - Source code and issues
- **[Telegram Group](https://t.me/TgCallerOfficial)** - Get help and discuss
- **[Documentation](https://tgcaller.github.io/TgCaller/)** - Complete guides

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/TgCaller/TgCaller/blob/main/LICENSE) file for details.

---

**Made with ❤️ for the Telegram developer community**

[![Made with Python](https://img.shields.io/badge/Made_with-Python-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Powered by FFmpeg](https://img.shields.io/badge/Powered_by-FFmpeg-007808?style=for-the-badge)](https://ffmpeg.org)
