#!/usr/bin/env python3
"""
Custom Filters Example - Audio and Video Effects
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig, VideoConfig
from tgcaller.advanced import AudioFilters, VideoFilters, FilterChain

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("filters_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)

# Filter instances
audio_filters = AudioFilters()
video_filters = VideoFilters()
filter_chains = {}  # chat_id -> FilterChain


@app.on_message(filters.command("add_echo"))
async def add_echo_command(client, message):
    """Add echo effect to audio"""
    if len(message.command) < 1:
        return await message.reply(
            "🎵 Usage: /add_echo [delay] [decay]\n"
            "Example: /add_echo 0.3 0.5\n"
            "Default: delay=0.3s, decay=0.3"
        )
    
    try:
        delay = 0.3
        decay = 0.3
        
        if len(message.command) > 1:
            delay = float(message.command[1])
        
        if len(message.command) > 2:
            decay = float(message.command[2])
        
        chat_id = message.chat.id
        
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add echo filter
        filter_chains[chat_id].add_audio_filter(
            audio_filters.apply_echo,
            delay=delay,
            decay=decay
        )
        
        await message.reply(
            f"🎵 Echo effect added!\n"
            f"Delay: {delay}s\n"
            f"Decay: {decay}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid parameters")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_reverb"))
async def add_reverb_command(client, message):
    """Add reverb effect to audio"""
    if len(message.command) < 1:
        return await message.reply(
            "🎵 Usage: /add_reverb [room_size] [damping]\n"
            "Example: /add_reverb 0.7 0.4\n"
            "Default: room_size=0.5, damping=0.5"
        )
    
    try:
        room_size = 0.5
        damping = 0.5
        
        if len(message.command) > 1:
            room_size = float(message.command[1])
        
        if len(message.command) > 2:
            damping = float(message.command[2])
        
        chat_id = message.chat.id
        
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add reverb filter
        filter_chains[chat_id].add_audio_filter(
            audio_filters.apply_reverb,
            room_size=room_size,
            damping=damping
        )
        
        await message.reply(
            f"🎵 Reverb effect added!\n"
            f"Room size: {room_size}\n"
            f"Damping: {damping}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid parameters")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_pitch_shift"))
async def add_pitch_shift_command(client, message):
    """Add pitch shift effect"""
    if len(message.command) < 2:
        return await message.reply(
            "🎵 Usage: /add_pitch_shift <semitones>\n"
            "Example: /add_pitch_shift 2 (raise by 2 semitones)\n"
            "Example: /add_pitch_shift -3 (lower by 3 semitones)"
        )
    
    try:
        semitones = float(message.command[1])
        chat_id = message.chat.id
        
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add pitch shift filter
        filter_chains[chat_id].add_audio_filter(
            audio_filters.apply_pitch_shift,
            semitones=semitones
        )
        
        direction = "higher" if semitones > 0 else "lower"
        await message.reply(
            f"🎵 Pitch shift added!\n"
            f"Shift: {abs(semitones)} semitones {direction}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid semitones value")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_distortion"))
async def add_distortion_command(client, message):
    """Add distortion effect"""
    if len(message.command) < 1:
        return await message.reply(
            "🎵 Usage: /add_distortion [gain] [threshold]\n"
            "Example: /add_distortion 3.0 0.6\n"
            "Default: gain=2.0, threshold=0.7"
        )
    
    try:
        gain = 2.0
        threshold = 0.7
        
        if len(message.command) > 1:
            gain = float(message.command[1])
        
        if len(message.command) > 2:
            threshold = float(message.command[2])
        
        chat_id = message.chat.id
        
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add distortion filter
        filter_chains[chat_id].add_audio_filter(
            audio_filters.apply_distortion,
            gain=gain,
            threshold=threshold
        )
        
        await message.reply(
            f"🎵 Distortion effect added!\n"
            f"Gain: {gain}\n"
            f"Threshold: {threshold}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid parameters")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_blur"))
async def add_blur_command(client, message):
    """Add blur effect to video"""
    if len(message.command) < 1:
        return await message.reply(
            "📹 Usage: /add_blur [kernel_size]\n"
            "Example: /add_blur 21\n"
            "Default: kernel_size=15"
        )
    
    try:
        kernel_size = 15
        
        if len(message.command) > 1:
            kernel_size = int(message.command[1])
            
        # Ensure odd number
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        chat_id = message.chat.id
        
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add blur filter
        filter_chains[chat_id].add_video_filter(
            video_filters.apply_blur,
            kernel_size=kernel_size
        )
        
        await message.reply(
            f"📹 Blur effect added!\n"
            f"Kernel size: {kernel_size}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid kernel size")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_sepia"))
async def add_sepia_command(client, message):
    """Add sepia effect to video"""
    chat_id = message.chat.id
    
    try:
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add sepia filter
        filter_chains[chat_id].add_video_filter(video_filters.apply_sepia)
        
        await message.reply("📹 Sepia effect added!")
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_grayscale"))
async def add_grayscale_command(client, message):
    """Add grayscale effect to video"""
    chat_id = message.chat.id
    
    try:
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add grayscale filter
        filter_chains[chat_id].add_video_filter(video_filters.apply_grayscale)
        
        await message.reply("📹 Grayscale effect added!")
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_cartoon"))
async def add_cartoon_command(client, message):
    """Add cartoon effect to video"""
    chat_id = message.chat.id
    
    try:
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add cartoon filter
        filter_chains[chat_id].add_video_filter(video_filters.apply_cartoon)
        
        await message.reply("📹 Cartoon effect added!")
        
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("add_color_balance"))
async def add_color_balance_command(client, message):
    """Add color balance effect"""
    if len(message.command) < 4:
        return await message.reply(
            "📹 Usage: /add_color_balance <red> <green> <blue>\n"
            "Example: /add_color_balance 1.2 1.0 0.8\n"
            "Values: 0.0-2.0 (1.0 = no change)"
        )
    
    try:
        red_gain = float(message.command[1])
        green_gain = float(message.command[2])
        blue_gain = float(message.command[3])
        
        chat_id = message.chat.id
        
        # Get or create filter chain
        if chat_id not in filter_chains:
            filter_chains[chat_id] = FilterChain()
        
        # Add color balance filter
        filter_chains[chat_id].add_video_filter(
            video_filters.apply_color_balance,
            red_gain=red_gain,
            green_gain=green_gain,
            blue_gain=blue_gain
        )
        
        await message.reply(
            f"📹 Color balance added!\n"
            f"Red: {red_gain}\n"
            f"Green: {green_gain}\n"
            f"Blue: {blue_gain}"
        )
        
    except ValueError:
        await message.reply("❌ Invalid color values")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("clear_filters"))
async def clear_filters_command(client, message):
    """Clear all filters"""
    chat_id = message.chat.id
    
    if chat_id in filter_chains:
        filter_chains[chat_id].clear_filters()
        await message.reply("🧹 All filters cleared!")
    else:
        await message.reply("❌ No filters to clear")


@app.on_message(filters.command("list_filters"))
async def list_filters_command(client, message):
    """List active filters"""
    chat_id = message.chat.id
    
    if chat_id not in filter_chains:
        return await message.reply("❌ No filters active")
    
    filter_chain = filter_chains[chat_id]
    
    audio_count = len(filter_chain.audio_filters)
    video_count = len(filter_chain.video_filters)
    
    if audio_count == 0 and video_count == 0:
        return await message.reply("❌ No filters active")
    
    filter_info = f"🎛️ **Active Filters:**\n\n"
    filter_info += f"🎵 Audio filters: {audio_count}\n"
    filter_info += f"📹 Video filters: {video_count}\n\n"
    filter_info += "Use /clear_filters to remove all filters"
    
    await message.reply(filter_info)


@app.on_message(filters.command("filter_presets"))
async def filter_presets_command(client, message):
    """Show available filter presets"""
    presets_text = (
        "🎛️ **Available Filter Effects:**\n\n"
        
        "**🎵 Audio Effects:**\n"
        "• `/add_echo` - Echo effect\n"
        "• `/add_reverb` - Reverb effect\n"
        "• `/add_pitch_shift` - Pitch shifting\n"
        "• `/add_distortion` - Distortion effect\n\n"
        
        "**📹 Video Effects:**\n"
        "• `/add_blur` - Blur effect\n"
        "• `/add_sepia` - Sepia tone\n"
        "• `/add_grayscale` - Black & white\n"
        "• `/add_cartoon` - Cartoon effect\n"
        "• `/add_color_balance` - Color adjustment\n\n"
        
        "**🛠️ Management:**\n"
        "• `/list_filters` - Show active filters\n"
        "• `/clear_filters` - Remove all filters"
    )
    
    await message.reply(presets_text)


async def main():
    """Start the filters bot"""
    await caller.start()
    print("🎛️ Custom filters bot started!")
    
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