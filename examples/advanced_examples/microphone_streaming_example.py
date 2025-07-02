#!/usr/bin/env python3
"""
Microphone Streaming Example
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig
from tgcaller.advanced import MicrophoneCapture, MicrophoneStreamer

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("mic_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)

# Active microphone streams
active_streams = {}


@app.on_message(filters.command("list_devices"))
async def list_devices_command(client, message):
    """List available audio devices"""
    try:
        mic_capture = MicrophoneCapture()
        devices = mic_capture.list_devices()
        
        if not devices:
            return await message.reply("❌ No audio devices found")
        
        device_list = []
        for device in devices:
            device_list.append(
                f"**Device {device['index']}**\n"
                f"Name: {device['name']}\n"
                f"Channels: {device['channels']}\n"
                f"Sample Rate: {device['sample_rate']:.0f} Hz"
            )
        
        await message.reply(
            "🎤 **Available Audio Devices:**\n\n" + "\n\n".join(device_list)
        )
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("start_mic"))
async def start_mic_command(client, message):
    """Start microphone streaming"""
    if len(message.command) < 1:
        return await message.reply(
            "🎤 Usage: /start_mic [device_index]\n"
            "Use /list_devices to see available devices"
        )
    
    try:
        device_index = None
        if len(message.command) > 1:
            device_index = int(message.command[1])
        
        chat_id = message.chat.id
        
        if chat_id in active_streams:
            return await message.reply("🎤 Microphone streaming already active in this chat")
        
        # Create microphone streamer
        audio_config = AudioConfig.high_quality()
        streamer = MicrophoneStreamer(caller, chat_id)
        
        # Start streaming
        success = await streamer.start_streaming(
            audio_config=audio_config,
            device_index=device_index
        )
        
        if success:
            active_streams[chat_id] = streamer
            device_text = f"Device {device_index}" if device_index is not None else "Default device"
            await message.reply(
                f"🎤 Microphone streaming started!\n"
                f"Device: {device_text}\n"
                f"Quality: {audio_config.bitrate} bps, {audio_config.channels} channels"
            )
        else:
            await message.reply("❌ Failed to start microphone streaming")
            
    except ValueError:
        await message.reply("❌ Invalid device index")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("stop_mic"))
async def stop_mic_command(client, message):
    """Stop microphone streaming"""
    chat_id = message.chat.id
    
    if chat_id not in active_streams:
        return await message.reply("🎤 No active microphone streaming in this chat")
    
    try:
        streamer = active_streams[chat_id]
        await streamer.stop_streaming()
        
        del active_streams[chat_id]
        
        await message.reply("🎤 Microphone streaming stopped")
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("mic_status"))
async def mic_status_command(client, message):
    """Get microphone streaming status"""
    if not active_streams:
        return await message.reply("🎤 No active microphone streams")
    
    status_list = []
    for chat_id, streamer in active_streams.items():
        status = "🟢 Active" if streamer.is_streaming else "🔴 Inactive"
        status_list.append(f"Chat {chat_id}: {status}")
    
    await message.reply(
        "🎤 **Microphone Stream Status:**\n\n" + "\n".join(status_list)
    )


@app.on_message(filters.command("test_mic"))
async def test_mic_command(client, message):
    """Test microphone capture"""
    if len(message.command) < 1:
        return await message.reply(
            "🎤 Usage: /test_mic [device_index] [duration_seconds]\n"
            "Example: /test_mic 0 5"
        )
    
    try:
        device_index = None
        duration = 5  # Default 5 seconds
        
        if len(message.command) > 1:
            device_index = int(message.command[1])
        
        if len(message.command) > 2:
            duration = int(message.command[2])
        
        # Send testing message
        testing_msg = await message.reply(f"🎤 Testing microphone for {duration} seconds...")
        
        # Create microphone capture
        audio_config = AudioConfig()
        mic_capture = MicrophoneCapture(audio_config)
        
        # Test callback to count frames
        frame_count = 0
        def test_callback(audio_data):
            nonlocal frame_count
            frame_count += 1
        
        mic_capture.add_callback(test_callback)
        
        # Start capture
        success = await mic_capture.start_capture(device_index)
        
        if not success:
            await testing_msg.edit_text("❌ Failed to start microphone capture")
            return
        
        # Wait for test duration
        await asyncio.sleep(duration)
        
        # Stop capture
        await mic_capture.stop_capture()
        
        # Report results
        device_text = f"Device {device_index}" if device_index is not None else "Default device"
        await testing_msg.edit_text(
            f"🎤 **Microphone Test Results**\n\n"
            f"Device: {device_text}\n"
            f"Duration: {duration} seconds\n"
            f"Frames captured: {frame_count}\n"
            f"Status: {'✅ Working' if frame_count > 0 else '❌ No audio detected'}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid parameters")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


async def main():
    """Start the microphone streaming bot"""
    await caller.start()
    print("🎤 Microphone streaming bot started!")
    
    await app.start()
    print("🤖 Bot is running...")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
    finally:
        # Stop all active streams
        for streamer in active_streams.values():
            await streamer.stop_streaming()
        
        await caller.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())