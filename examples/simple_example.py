#!/usr/bin/env python3
"""
Simple QuantumTgCalls Example
Following pytgcalls usage patterns
"""

import asyncio
import logging
from pyrogram import Client
from tgcall import QuantumTgCalls, AudioParameters, VideoParameters

# Configure logging
logging.basicConfig(level=logging.INFO)

# Pyrogram client configuration
api_id = 12345  # Your API ID
api_hash = "your_api_hash"  # Your API Hash
session_name = "quantum_session"

app = Client(session_name, api_id=api_id, api_hash=api_hash)
quantum = QuantumTgCalls(app)


@quantum.on_stream_end
async def on_stream_end(client, update):
    """Handle stream end event"""
    print(f"Stream ended in chat {update.chat_id}")


@quantum.on_kicked
async def on_kicked(client, update):
    """Handle kicked from call event"""
    print(f"Kicked from call in chat {update.chat_id}")


async def main():
    """Main function"""
    try:
        # Start QuantumTgCalls
        await quantum.start()
        print("QuantumTgCalls started!")
        
        # Example chat ID (replace with actual chat ID)
        chat_id = -1001234567890
        
        # Join voice call with custom audio parameters
        audio_params = AudioParameters(
            bitrate=48000,
            noise_cancellation=True,
            echo_cancellation=True
        )
        
        await quantum.join_call(chat_id, audio_parameters=audio_params)
        print(f"Joined call in chat {chat_id}")
        
        # Play audio file
        await quantum.play(chat_id, "audio.mp3")
        print("Playing audio...")
        
        # Wait for stream to finish
        await asyncio.sleep(10)
        
        # Join video call
        video_params = VideoParameters.preset_720p()
        await quantum.join_call(chat_id, audio_params, video_params)
        
        # Play video file
        await quantum.play(chat_id, "video.mp4")
        print("Playing video...")
        
        # Keep running
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        # Stop QuantumTgCalls
        await quantum.stop()
        print("QuantumTgCalls stopped")


if __name__ == "__main__":
    asyncio.run(main())