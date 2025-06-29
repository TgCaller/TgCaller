#!/usr/bin/env python3
"""
Advanced QuantumTgCalls Example
Demonstrating advanced features
"""

import asyncio
import logging
from pyrogram import Client
from quantumtgcalls import (
    QuantumTgCalls, 
    AudioParameters, 
    VideoParameters,
    MediaStream
)

logging.basicConfig(level=logging.INFO)

# Configuration
api_id = 12345
api_hash = "your_api_hash"
session_name = "quantum_advanced"

app = Client(session_name, api_id=api_id, api_hash=api_hash)
quantum = QuantumTgCalls(app, log_mode=logging.INFO)


@quantum.on_stream_end
async def handle_stream_end(client, update):
    """Auto-play next song when current ends"""
    print(f"Stream ended in {update.chat_id}, playing next...")
    
    # Play next song from playlist
    next_song = get_next_song()
    if next_song:
        await quantum.play(update.chat_id, next_song)


@quantum.on_kicked
async def handle_kicked(client, update):
    """Handle being kicked from call"""
    print(f"Kicked from {update.chat_id}: {update.message}")
    
    # Try to rejoin after 5 seconds
    await asyncio.sleep(5)
    try:
        await quantum.join_call(update.chat_id)
        print(f"Rejoined call in {update.chat_id}")
    except Exception as e:
        print(f"Failed to rejoin: {e}")


def get_next_song():
    """Get next song from playlist"""
    playlist = [
        "song1.mp3",
        "song2.mp3", 
        "https://example.com/stream.mp3"
    ]
    # Simple round-robin selection
    return playlist[0] if playlist else None


async def demonstrate_features():
    """Demonstrate various QuantumTgCalls features"""
    
    await quantum.start()
    chat_id = -1001234567890
    
    # 1. High-quality audio streaming
    print("=== High-Quality Audio ===")
    hq_audio = AudioParameters(
        bitrate=256000,
        sample_rate=48000,
        noise_cancellation=True,
        echo_cancellation=True
    )
    
    await quantum.join_call(chat_id, audio_parameters=hq_audio)
    await quantum.play(chat_id, "high_quality_audio.flac")
    await asyncio.sleep(5)
    
    # 2. 4K Video streaming
    print("=== 4K Video Streaming ===")
    video_4k = VideoParameters.preset_4k()
    
    await quantum.join_call(chat_id, hq_audio, video_4k)
    
    # Create advanced media stream
    video_stream = MediaStream(
        path="4k_video.mp4",
        audio_parameters=hq_audio,
        video_parameters=video_4k,
        start_time=30.0,  # Start at 30 seconds
        duration=120.0    # Play for 2 minutes
    )
    
    await quantum.play(chat_id, video_stream)
    await asyncio.sleep(10)
    
    # 3. Live streaming from YouTube
    print("=== YouTube Live Stream ===")
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    await quantum.play(chat_id, youtube_url)
    await asyncio.sleep(10)
    
    # 4. Stream controls
    print("=== Stream Controls ===")
    await quantum.pause_stream(chat_id)
    print("Paused for 3 seconds...")
    await asyncio.sleep(3)
    
    await quantum.resume_stream(chat_id)
    print("Resumed!")
    
    # 5. Multiple chat management
    print("=== Multiple Chats ===")
    chat_id_2 = -1001234567891
    
    await quantum.join_call(chat_id_2, hq_audio)
    await quantum.play(chat_id_2, "background_music.mp3")
    
    print(f"Active calls: {list(quantum.active_calls.keys())}")
    
    # 6. Stream seeking
    print("=== Stream Seeking ===")
    await quantum.seek(chat_id, 60.0)  # Seek to 1 minute
    current_time = await quantum.get_stream_time(chat_id)
    print(f"Current position: {current_time}s")
    
    # Keep running for demo
    await asyncio.sleep(30)


async def main():
    """Main function"""
    try:
        await demonstrate_features()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        await quantum.stop()
        print("QuantumTgCalls stopped")


if __name__ == "__main__":
    asyncio.run(main())