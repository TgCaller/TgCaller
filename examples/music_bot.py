#!/usr/bin/env python3
"""
Music Bot Example using TgCaller
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)

# Playlist storage
playlists = {}


@app.on_message(filters.command("play"))
async def play_command(client, message):
    """Play music command"""
    if len(message.command) < 2:
        return await message.reply("🎯 Usage: /play <song_name>")
    
    song_name = " ".join(message.command[1:])
    chat_id = message.chat.id
    
    try:
        # Join call if not already joined
        if not caller.is_connected(chat_id):
            await caller.join_call(chat_id)
            await message.reply("📞 Joined voice chat!")
        
        # High quality audio
        audio_config = AudioConfig.high_quality()
        
        # Play song
        song_path = f"music/{song_name}.mp3"
        if os.path.exists(song_path):
            await caller.play(chat_id, song_path, audio_config=audio_config)
            await message.reply(f"🎵 Now playing: **{song_name}**")
        else:
            await message.reply(f"❌ Song not found: {song_name}")
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("pause"))
async def pause_command(client, message):
    """Pause music"""
    chat_id = message.chat.id
    
    if await caller.pause(chat_id):
        await message.reply("⏸️ Music paused")
    else:
        await message.reply("❌ Nothing to pause")


@app.on_message(filters.command("resume"))
async def resume_command(client, message):
    """Resume music"""
    chat_id = message.chat.id
    
    if await caller.resume(chat_id):
        await message.reply("▶️ Music resumed")
    else:
        await message.reply("❌ Nothing to resume")


@app.on_message(filters.command("stop"))
async def stop_command(client, message):
    """Stop music"""
    chat_id = message.chat.id
    
    if await caller.stop(chat_id):
        await message.reply("⏹️ Music stopped")
    else:
        await message.reply("❌ Nothing to stop")


@app.on_message(filters.command("leave"))
async def leave_command(client, message):
    """Leave voice chat"""
    chat_id = message.chat.id
    
    if await caller.leave_call(chat_id):
        await message.reply("👋 Left voice chat")
    else:
        await message.reply("❌ Not in voice chat")


@app.on_message(filters.command("volume"))
async def volume_command(client, message):
    """Set volume"""
    if len(message.command) < 2:
        return await message.reply("🎯 Usage: /volume <0-100>")
    
    try:
        volume = int(message.command[1])
        if not 0 <= volume <= 100:
            return await message.reply("❌ Volume must be between 0-100")
        
        chat_id = message.chat.id
        volume_float = volume / 100.0
        
        if await caller.set_volume(chat_id, volume_float):
            await message.reply(f"🔊 Volume set to {volume}%")
        else:
            await message.reply("❌ Not in voice chat")
            
    except ValueError:
        await message.reply("❌ Invalid volume value")


@caller.on_stream_end
async def on_stream_end(client, update):
    """Auto-play next song"""
    chat_id = update.chat_id
    
    # Get playlist for this chat
    playlist = playlists.get(chat_id, [])
    
    if playlist:
        next_song = playlist.pop(0)
        audio_config = AudioConfig.high_quality()
        await caller.play(chat_id, next_song, audio_config=audio_config)
        print(f"🎵 Auto-playing next song in chat {chat_id}")


@caller.on_error
async def on_error(client, error):
    """Handle errors"""
    print(f"❌ TgCaller error: {error}")


async def main():
    """Start the bot"""
    await caller.start()
    print("🎵 Music bot started!")
    
    # Keep running
    await app.start()
    print("🤖 Bot is running...")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
    finally:
        await caller.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())