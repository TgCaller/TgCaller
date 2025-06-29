#!/usr/bin/env python3
"""
Docker Example for QuantumTgCalls
Environment variable based configuration
"""

import os
import asyncio
import logging
from pyrogram import Client
from tgcall import QuantumTgCalls, AudioParameters

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get configuration from environment
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
SESSION_STRING = os.getenv('SESSION_STRING', '')
CHAT_ID = int(os.getenv('CHAT_ID', '0'))
MEDIA_PATH = os.getenv('MEDIA_PATH', '/app/media')

# Validate configuration
if not all([API_ID, API_HASH, CHAT_ID]):
    raise ValueError("Missing required environment variables")

# Initialize client
if SESSION_STRING:
    app = Client("quantum_docker", session_string=SESSION_STRING)
else:
    app = Client("quantum_docker", api_id=API_ID, api_hash=API_HASH)

quantum = QuantumTgCalls(app, log_mode=logging.INFO)


@quantum.on_stream_end
async def on_stream_end(client, update):
    """Handle stream end - loop media"""
    logging.info(f"Stream ended in {update.chat_id}")
    
    # Find next media file
    media_files = [
        f for f in os.listdir(MEDIA_PATH) 
        if f.endswith(('.mp3', '.mp4', '.wav', '.flac'))
    ]
    
    if media_files:
        next_file = os.path.join(MEDIA_PATH, media_files[0])
        await quantum.play(update.chat_id, next_file)
        logging.info(f"Playing next: {next_file}")


async def main():
    """Main Docker application"""
    try:
        logging.info("Starting QuantumTgCalls Docker instance...")
        
        # Start quantum
        await quantum.start()
        logging.info("QuantumTgCalls started successfully")
        
        # Join call
        audio_params = AudioParameters(
            bitrate=128000,
            noise_cancellation=True
        )
        
        await quantum.join_call(CHAT_ID, audio_parameters=audio_params)
        logging.info(f"Joined call in chat {CHAT_ID}")
        
        # Start playing media
        media_files = [
            f for f in os.listdir(MEDIA_PATH)
            if f.endswith(('.mp3', '.mp4', '.wav', '.flac'))
        ]
        
        if media_files:
            first_file = os.path.join(MEDIA_PATH, media_files[0])
            await quantum.play(CHAT_ID, first_file)
            logging.info(f"Started playing: {first_file}")
        else:
            logging.warning("No media files found in /app/media")
        
        # Keep running
        logging.info("QuantumTgCalls is running... Press Ctrl+C to stop")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
        
    except Exception as e:
        logging.error(f"Error: {e}")
        
    finally:
        await quantum.stop()
        logging.info("QuantumTgCalls stopped")


if __name__ == "__main__":
    asyncio.run(main())