#!/usr/bin/env python3
"""
YouTube Streaming Example
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig, VideoConfig
from tgcaller.advanced import YouTubeDownloader, YouTubeStreamer

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("youtube_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)
youtube_streamer = YouTubeStreamer(caller)


@app.on_message(filters.command("yt_play"))
async def youtube_play_command(client, message):
    """Play YouTube video directly"""
    if len(message.command) < 2:
        return await message.reply(
            "🎬 Usage: /yt_play <youtube_url>\n"
            "Example: /yt_play https://youtube.com/watch?v=..."
        )
    
    url = message.command[1]
    chat_id = message.chat.id
    
    try:
        # Send processing message
        processing_msg = await message.reply("🔄 Processing YouTube video...")
        
        # Play YouTube video
        success = await youtube_streamer.play_youtube_url(
            chat_id, url, quality='best[height<=720]'
        )
        
        if success:
            await processing_msg.edit_text(
                f"🎬 Playing YouTube video!\n"
                f"URL: {url}"
            )
        else:
            await processing_msg.edit_text("❌ Failed to play YouTube video")
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("yt_download_play"))
async def youtube_download_play_command(client, message):
    """Download and play YouTube video"""
    if len(message.command) < 2:
        return await message.reply(
            "🎬 Usage: /yt_download_play <youtube_url> [audio_only]\n"
            "Example: /yt_download_play https://youtube.com/watch?v=... true"
        )
    
    url = message.command[1]
    audio_only = len(message.command) > 2 and message.command[2].lower() == 'true'
    chat_id = message.chat.id
    
    try:
        # Send processing message
        processing_msg = await message.reply("📥 Downloading YouTube video...")
        
        # Download and play
        success = await youtube_streamer.download_and_play(
            chat_id, url, audio_only=audio_only
        )
        
        if success:
            content_type = "audio" if audio_only else "video"
            await processing_msg.edit_text(
                f"🎬 Downloaded and playing YouTube {content_type}!\n"
                f"URL: {url}"
            )
        else:
            await processing_msg.edit_text("❌ Failed to download and play")
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("yt_search"))
async def youtube_search_command(client, message):
    """Search YouTube videos"""
    if len(message.command) < 2:
        return await message.reply(
            "🔍 Usage: /yt_search <search_query>\n"
            "Example: /yt_search relaxing music"
        )
    
    query = " ".join(message.command[1:])
    
    try:
        # Send searching message
        searching_msg = await message.reply("🔍 Searching YouTube...")
        
        # Search videos
        downloader = YouTubeDownloader()
        results = await downloader.search_videos(query, max_results=5)
        
        if not results:
            await searching_msg.edit_text("❌ No search results found")
            return
        
        # Format results
        result_text = f"🔍 **Search Results for:** {query}\n\n"
        
        for i, video in enumerate(results, 1):
            duration = video.get('duration', 0)
            duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
            
            result_text += (
                f"**{i}.** {video['title']}\n"
                f"Duration: {duration_str}\n"
                f"Uploader: {video.get('uploader', 'Unknown')}\n"
                f"Use: `/yt_play_result {i-1}`\n\n"
            )
        
        await searching_msg.edit_text(result_text)
        
        # Store results for later use
        if not hasattr(app, 'search_results'):
            app.search_results = {}
        app.search_results[message.from_user.id] = results
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("yt_play_result"))
async def youtube_play_result_command(client, message):
    """Play search result by index"""
    if len(message.command) < 2:
        return await message.reply(
            "🎬 Usage: /yt_play_result <index>\n"
            "Use /yt_search first to get results"
        )
    
    try:
        index = int(message.command[1])
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user has search results
        if not hasattr(app, 'search_results') or user_id not in app.search_results:
            return await message.reply("❌ No search results found. Use /yt_search first")
        
        results = app.search_results[user_id]
        
        if index < 0 or index >= len(results):
            return await message.reply(f"❌ Invalid index. Use 0-{len(results)-1}")
        
        # Play selected video
        video = results[index]
        success = await youtube_streamer.play_youtube_url(chat_id, video['url'])
        
        if success:
            await message.reply(
                f"🎬 Playing: **{video['title']}**\n"
                f"Uploader: {video.get('uploader', 'Unknown')}"
            )
        else:
            await message.reply("❌ Failed to play video")
            
    except ValueError:
        await message.reply("❌ Invalid index number")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("yt_info"))
async def youtube_info_command(client, message):
    """Get YouTube video information"""
    if len(message.command) < 2:
        return await message.reply(
            "ℹ️ Usage: /yt_info <youtube_url>\n"
            "Example: /yt_info https://youtube.com/watch?v=..."
        )
    
    url = message.command[1]
    
    try:
        # Send processing message
        processing_msg = await message.reply("ℹ️ Getting video information...")
        
        # Get video info
        downloader = YouTubeDownloader()
        info = await downloader.get_video_info(url)
        
        if not info:
            await processing_msg.edit_text("❌ Failed to get video information")
            return
        
        # Format information
        duration = info.get('duration', 0)
        duration_str = f"{duration//60}:{duration%60:02d}" if duration else "Unknown"
        
        view_count = info.get('view_count', 0)
        view_count_str = f"{view_count:,}" if view_count else "Unknown"
        
        info_text = (
            f"ℹ️ **Video Information**\n\n"
            f"**Title:** {info.get('title', 'Unknown')}\n"
            f"**Duration:** {duration_str}\n"
            f"**Uploader:** {info.get('uploader', 'Unknown')}\n"
            f"**Views:** {view_count_str}\n\n"
            f"**Description:**\n{info.get('description', 'No description')[:200]}..."
        )
        
        await processing_msg.edit_text(info_text)
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("yt_search_play"))
async def youtube_search_play_command(client, message):
    """Search and play first result"""
    if len(message.command) < 2:
        return await message.reply(
            "🎬 Usage: /yt_search_play <search_query>\n"
            "Example: /yt_search_play relaxing music"
        )
    
    query = " ".join(message.command[1:])
    chat_id = message.chat.id
    
    try:
        # Send processing message
        processing_msg = await message.reply("🔍 Searching and playing...")
        
        # Search and play first result
        success = await youtube_streamer.search_and_play(chat_id, query, index=0)
        
        if success:
            await processing_msg.edit_text(
                f"🎬 Playing first result for: **{query}**"
            )
        else:
            await processing_msg.edit_text("❌ No results found or failed to play")
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


async def main():
    """Start the YouTube streaming bot"""
    await caller.start()
    print("🎬 YouTube streaming bot started!")
    
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