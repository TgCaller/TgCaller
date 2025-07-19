# TgCaller

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/tgcaller?style=for-the-badge)](https://pypi.org/project/tgcaller/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-00d4aa?style=for-the-badge)](https://github.com/tgcaller/TgCaller/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/tgcaller?style=for-the-badge&color=blue)](https://pypi.org/project/tgcaller/)

**🎯 Modern, Fast, and Reliable Telegram Group Calls Library**

*Built for developers who need a simple yet powerful solution for Telegram voice and video calls*

[Get Started](installation.md){ .md-button .md-button--primary }
[View Examples](usage.md){ .md-button }

</div>

---

## ⚡ Why TgCaller?

TgCaller is a modern library designed with developer experience and reliability in mind:

- 🚀 **Fast & Lightweight**: Optimized performance with minimal resource usage
- 📱 **Easy to Use**: Simple, intuitive API with comprehensive documentation
- 🔧 **Reliable**: Built-in error handling and auto-recovery mechanisms
- 📹 **HD Support**: High-quality audio and video streaming capabilities
- 🔌 **Extensible**: Plugin system for custom features and integrations
- 📚 **Well Documented**: Complete guides, examples, and API reference

---

## 🚀 Quick Start

### Installation

```bash
pip install tgcaller
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

## 🎵 Core Features

### Audio Streaming
- Multiple quality presets (high quality, low bandwidth)
- Opus and AAC codec support
- Noise suppression and echo cancellation
- Real-time volume control and seek functionality

### Video Streaming
- 720p and 1080p HD support
- H.264 and VP8 codec support
- Hardware acceleration when available
- Multiple resolution presets for different use cases

### Advanced Capabilities
- 🌉 **Bridged Calls** - Connect multiple chats
- 🎤 **Microphone Streaming** - Live microphone input
- 🖥️ **Screen Sharing** - Share your screen in video calls
- 🎬 **YouTube Integration** - Stream YouTube videos directly
- 🎤 **Speech Transcription** - Real-time speech-to-text
- 🎛️ **Audio/Video Filters** - Apply real-time effects

---

## 🛠️ CLI Tools

TgCaller comes with powerful command-line tools:

```bash
# Test installation
tgcaller test --api-id 12345 --api-hash "your_hash"

# System diagnostics
tgcaller info

# Show examples
tgcaller examples
```

[Learn more about CLI →](cli.md)

---

## 🤝 Community

[![GitHub](https://img.shields.io/badge/GitHub-TgCaller-181717?style=for-the-badge&logo=github)](https://github.com/TgCaller/TgCaller)
[![Telegram](https://img.shields.io/badge/Telegram-@TgCallerOfficial-26A5E4?style=for-the-badge&logo=telegram)](https://t.me/TgCallerOfficial)

- **[GitHub](https://github.com/TgCaller/TgCaller)** - Source code and issues
- **[Telegram Group](https://t.me/TgCallerOfficial)** - Get help and discuss
- **[Documentation](https://tgcaller.github.io/TgCaller/)** - Complete guides

---

**Made with ❤️ for the Telegram developer community**