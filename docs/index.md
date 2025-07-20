# TgCaller

[![PyPI Version](https://img.shields.io/pypi/v/tgcaller?style=flat-square)](https://pypi.org/project/tgcaller/)
[![Python Version](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](https://github.com/TgCaller/TgCaller/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/tgcaller?style=flat-square&color=blue)](https://pypi.org/project/tgcaller/)
[![Stars](https://img.shields.io/github/stars/TgCaller/TgCaller?style=flat-square&logo=github)](https://github.com/TgCaller/TgCaller/stargazers)
[![Forks](https://img.shields.io/github/forks/TgCaller/TgCaller?style=flat-square&logo=github)](https://github.com/TgCaller/TgCaller/network/members)

---

🎯 **Modern, Fast, and Reliable Telegram Group Calls Library**

> Built for developers who need a simple yet powerful solution for Telegram voice and video calls.

---

## 🚀 Why TgCaller?

- **Fast & Lightweight** – Optimized performance with minimal resource usage.
- **Easy to Use** – Simple, intuitive API with comprehensive documentation.
- **Reliable** – Built-in error handling and auto-recovery mechanisms.
- **HD Support** – High-quality audio and video streaming capabilities.
- **Extensible** – Plugin system for custom features and integrations.
- **Well Documented** – Complete guides, examples, and API reference.

---

## ⚡ Quick Start

### 📦 Installation

```bash
pip install tgcaller

🔧 Basic Usage

import asyncio
from pyrogram import Client
from tgcaller import TgCaller

app = Client("my_session", api_id=API_ID, api_hash=API_HASH)
caller = TgCaller(app)

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

async def main():
    await caller.start()
    await caller.join_call(-1001234567890)
    await caller.play(-1001234567890, "song.mp3")

if __name__ == "__main__":
    asyncio.run(main())


---

🎵 Core Features

🔊 Audio Streaming

Multiple quality presets

Opus & AAC support

Noise suppression & echo cancellation

Real-time volume control & seeking


🎥 Video Streaming

720p and 1080p HD support

H.264 and VP8 codec support

Hardware acceleration (if available)

Resolution presets for flexibility



---

🎯 Advanced Capabilities

Bridged Calls – Connect multiple chats

Microphone Streaming – Live mic input

Screen Sharing – Share your screen in real-time

YouTube Integration – Stream YouTube directly

Speech Transcription – Real-time speech-to-text

Audio/Video Filters – Real-time effects



---

🛠 CLI Tools

tgcaller test --api-id 12345 --api-hash "your_hash"
tgcaller info
tgcaller examples


---

🤝 Community

GitHub Source Code

Telegram Support Group

Full Documentation



---

Made with ❤️ for the Telegram developer community.
