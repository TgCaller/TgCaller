#!/usr/bin/env python3
"""
Screen Sharing Example
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, VideoConfig
from tgcaller.advanced import ScreenShare, ScreenShareStreamer

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("screen_share_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)

# Active screen shares
active_shares = {}


@app.on_message(filters.command("list_monitors"))
async def list_monitors_command(client, message):
    """List available monitors"""
    try:
        screen_share = ScreenShare()
        monitors = screen_share.list_monitors()
        
        if not monitors:
            return await message.reply("❌ No monitors found")
        
        monitor_list = []
        for monitor in monitors:
            monitor_list.append(
                f"**Monitor {monitor['index']}**\n"
                f"Resolution: {monitor['width']}x{monitor['height']}\n"
                f"Position: ({monitor['left']}, {monitor['top']})"
            )
        
        await message.reply(
            "🖥️ **Available Monitors:**\n\n" + "\n\n".join(monitor_list)
        )
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("start_screen_share"))
async def start_screen_share_command(client, message):
    """Start screen sharing"""
    if len(message.command) < 2:
        return await message.reply(
            "🖥️ Usage: /start_screen_share <monitor_index>\n"
            "Use /list_monitors to see available monitors"
        )
    
    try:
        monitor_index = int(message.command[1])
        chat_id = message.chat.id
        
        if chat_id in active_shares:
            return await message.reply("🖥️ Screen sharing already active in this chat")
        
        # Create screen share streamer
        video_config = VideoConfig.hd_720p()
        streamer = ScreenShareStreamer(caller, chat_id)
        
        # Start streaming
        success = await streamer.start_streaming(
            video_config=video_config,
            monitor_index=monitor_index
        )
        
        if success:
            active_shares[chat_id] = streamer
            await message.reply(
                f"🖥️ Screen sharing started!\n"
                f"Monitor: {monitor_index}\n"
                f"Resolution: {video_config.width}x{video_config.height}"
            )
        else:
            await message.reply("❌ Failed to start screen sharing")
            
    except ValueError:
        await message.reply("❌ Invalid monitor index")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("start_region_share"))
async def start_region_share_command(client, message):
    """Start sharing specific screen region"""
    if len(message.command) < 5:
        return await message.reply(
            "🖥️ Usage: /start_region_share <left> <top> <width> <height>"
        )
    
    try:
        left = int(message.command[1])
        top = int(message.command[2])
        width = int(message.command[3])
        height = int(message.command[4])
        
        chat_id = message.chat.id
        
        if chat_id in active_shares:
            return await message.reply("🖥️ Screen sharing already active in this chat")
        
        # Create screen share streamer
        video_config = VideoConfig.hd_720p()
        streamer = ScreenShareStreamer(caller, chat_id)
        
        # Start streaming with custom region
        region = (left, top, width, height)
        success = await streamer.start_streaming(
            video_config=video_config,
            region=region
        )
        
        if success:
            active_shares[chat_id] = streamer
            await message.reply(
                f"🖥️ Region sharing started!\n"
                f"Region: {left}, {top}, {width}x{height}"
            )
        else:
            await message.reply("❌ Failed to start region sharing")
            
    except ValueError:
        await message.reply("❌ Invalid region coordinates")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("stop_screen_share"))
async def stop_screen_share_command(client, message):
    """Stop screen sharing"""
    chat_id = message.chat.id
    
    if chat_id not in active_shares:
        return await message.reply("🖥️ No active screen sharing in this chat")
    
    try:
        streamer = active_shares[chat_id]
        await streamer.stop_streaming()
        
        del active_shares[chat_id]
        
        await message.reply("🖥️ Screen sharing stopped")
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("screen_share_status"))
async def screen_share_status_command(client, message):
    """Get screen sharing status"""
    if not active_shares:
        return await message.reply("🖥️ No active screen shares")
    
    status_list = []
    for chat_id, streamer in active_shares.items():
        status = "🟢 Active" if streamer.is_streaming else "🔴 Inactive"
        status_list.append(f"Chat {chat_id}: {status}")
    
    await message.reply(
        "🖥️ **Screen Share Status:**\n\n" + "\n".join(status_list)
    )


async def main():
    """Start the screen sharing bot"""
    await caller.start()
    print("🖥️ Screen sharing bot started!")
    
    await app.start()
    print("🤖 Bot is running...")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
    finally:
        # Stop all active shares
        for streamer in active_shares.values():
            await streamer.stop_streaming()
        
        await caller.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())