#!/usr/bin/env python3
"""
Simple TgCaller Bot Example
"""

import asyncio
import logging
from pyrogram import Client
from tgcaller import TgCaller, AudioConfig, VideoConfig

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configuration
API_ID = 12345  # Your API ID
API_HASH = "your_api_hash"  # Your API Hash
SESSION_NAME = "tgcaller_bot"

# Initialize
app = Client(SESSION_NAME, api_id=API_ID, api_hash=API_HASH)
caller = TgCaller(app)


@caller.on_stream_end
async def on_stream_end(client, update):
    """Handle stream end event"""
    print(f"🎵 Stream ended in chat {update.chat_id}")


@caller.on_error
async def on_error(client, error):
    """Handle errors"""
    print(f"❌ Error: {error}")


async def main():
    """Main function"""
    try:
        # Start TgCaller
        await caller.start()
        print("✅ TgCaller started!")
        
        # Example chat ID (replace with actual)
        chat_id = -1001234567890
        
        # Join voice call
        await caller.join_call(chat_id)
        print(f"📞 Joined call in chat {chat_id}")
        
        # Play audio with high quality
        audio_config = AudioConfig.high_quality()
        await caller.play(chat_id, "song.mp3", audio_config=audio_config)
        print("🎵 Playing audio...")
        
        # Wait a bit
        await asyncio.sleep(10)
        
        # Play video
        video_config = VideoConfig.hd_720p()
        await caller.play(chat_id, "video.mp4", video_config=video_config)
        print("📺 Playing video...")
        
        # Keep running
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        await caller.stop()
        print("🛑 TgCaller stopped")


if __name__ == "__main__":
    asyncio.run(main())