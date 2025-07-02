#!/usr/bin/env python3
"""
Bridged Calls Example - Connect multiple chats
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig
from tgcaller.advanced import BridgedCallManager

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("bridged_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)
bridge_manager = BridgedCallManager(caller)


@app.on_message(filters.command("create_bridge"))
async def create_bridge_command(client, message):
    """Create bridge between chats"""
    if len(message.command) < 3:
        return await message.reply(
            "🌉 Usage: /create_bridge <bridge_name> <chat_id1> <chat_id2> ..."
        )
    
    try:
        bridge_name = message.command[1]
        chat_ids = [int(chat_id) for chat_id in message.command[2:]]
        
        audio_config = AudioConfig.high_quality()
        success = await bridge_manager.create_bridge(
            bridge_name, chat_ids, audio_config
        )
        
        if success:
            await message.reply(
                f"🌉 Bridge '{bridge_name}' created successfully!\n"
                f"Connected chats: {', '.join(map(str, chat_ids))}"
            )
        else:
            await message.reply("❌ Failed to create bridge")
            
    except ValueError:
        await message.reply("❌ Invalid chat IDs")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("destroy_bridge"))
async def destroy_bridge_command(client, message):
    """Destroy bridge"""
    if len(message.command) < 2:
        return await message.reply("🌉 Usage: /destroy_bridge <bridge_name>")
    
    bridge_name = message.command[1]
    success = await bridge_manager.destroy_bridge(bridge_name)
    
    if success:
        await message.reply(f"🌉 Bridge '{bridge_name}' destroyed")
    else:
        await message.reply("❌ Bridge not found")


@app.on_message(filters.command("list_bridges"))
async def list_bridges_command(client, message):
    """List all bridges"""
    bridges = bridge_manager.list_bridges()
    
    if not bridges:
        return await message.reply("🌉 No active bridges")
    
    bridge_info = []
    for bridge_name in bridges:
        info = bridge_manager.get_bridge_info(bridge_name)
        if info:
            status = "🟢 Active" if info['active'] else "🔴 Inactive"
            bridge_info.append(
                f"**{bridge_name}** - {status}\n"
                f"Chats: {len(info['chat_ids'])} connected"
            )
    
    await message.reply(
        "🌉 **Active Bridges:**\n\n" + "\n\n".join(bridge_info)
    )


@app.on_message(filters.command("add_to_bridge"))
async def add_to_bridge_command(client, message):
    """Add chat to bridge"""
    if len(message.command) < 3:
        return await message.reply(
            "🌉 Usage: /add_to_bridge <bridge_name> <chat_id>"
        )
    
    try:
        bridge_name = message.command[1]
        chat_id = int(message.command[2])
        
        success = await bridge_manager.add_chat_to_bridge(bridge_name, chat_id)
        
        if success:
            await message.reply(
                f"🌉 Chat {chat_id} added to bridge '{bridge_name}'"
            )
        else:
            await message.reply("❌ Failed to add chat to bridge")
            
    except ValueError:
        await message.reply("❌ Invalid chat ID")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


async def main():
    """Start the bridged calls bot"""
    await caller.start()
    print("🌉 Bridged calls bot started!")
    
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