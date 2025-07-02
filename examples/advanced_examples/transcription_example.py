#!/usr/bin/env python3
"""
Whisper Transcription Example
"""

import asyncio
import os
from pyrogram import Client, filters
from tgcaller import TgCaller, AudioConfig
from tgcaller.advanced import WhisperTranscription, TranscriptionManager

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("transcription_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)
transcription_manager = TranscriptionManager(caller)


@app.on_message(filters.command("start_transcription"))
async def start_transcription_command(client, message):
    """Start transcription for current call"""
    if len(message.command) < 1:
        return await message.reply(
            "🎤 Usage: /start_transcription [model] [language]\n"
            "Models: tiny, base, small, medium, large\n"
            "Languages: en, es, fr, de, etc. (auto-detect if not specified)"
        )
    
    try:
        model_name = "base"  # Default model
        language = None  # Auto-detect
        
        if len(message.command) > 1:
            model_name = message.command[1]
        
        if len(message.command) > 2:
            language = message.command[2]
        
        chat_id = message.chat.id
        
        # Send loading message
        loading_msg = await message.reply("🔄 Loading Whisper model...")
        
        # Start transcription
        success = await transcription_manager.start_transcription_for_call(
            chat_id, model_name, language
        )
        
        if success:
            await loading_msg.edit_text(
                f"🎤 Transcription started!\n"
                f"Model: {model_name}\n"
                f"Language: {language or 'Auto-detect'}\n\n"
                f"Transcriptions will appear as messages in this chat."
            )
        else:
            await loading_msg.edit_text("❌ Failed to start transcription")
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("stop_transcription"))
async def stop_transcription_command(client, message):
    """Stop transcription"""
    chat_id = message.chat.id
    
    try:
        success = await transcription_manager.stop_transcription_for_call(chat_id)
        
        if success:
            await message.reply("🎤 Transcription stopped")
        else:
            await message.reply("❌ No active transcription in this chat")
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("transcribe_file"))
async def transcribe_file_command(client, message):
    """Transcribe audio file"""
    if not message.reply_to_message or not message.reply_to_message.audio:
        return await message.reply(
            "🎤 Reply to an audio message with /transcribe_file\n"
            "Optionally specify model: /transcribe_file base"
        )
    
    try:
        model_name = "base"
        if len(message.command) > 1:
            model_name = message.command[1]
        
        # Send processing message
        processing_msg = await message.reply("🔄 Transcribing audio file...")
        
        # Download audio file
        audio_file = await message.reply_to_message.download()
        
        # Create transcriber
        transcriber = WhisperTranscription(model_name)
        
        # Transcribe file
        result = await transcriber.transcribe_file(audio_file)
        
        if result:
            # Format result
            duration = result.get('duration', 0)
            duration_str = f"{duration//60:.0f}:{duration%60:02.0f}" if duration else "Unknown"
            
            transcription_text = (
                f"🎤 **Transcription Result**\n\n"
                f"**Language:** {result.get('language', 'Unknown')}\n"
                f"**Duration:** {duration_str}\n"
                f"**Model:** {model_name}\n\n"
                f"**Text:**\n{result['text']}"
            )
            
            await processing_msg.edit_text(transcription_text)
        else:
            await processing_msg.edit_text("❌ Failed to transcribe audio file")
        
        # Clean up downloaded file
        if os.path.exists(audio_file):
            os.unlink(audio_file)
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


@app.on_message(filters.command("transcription_status"))
async def transcription_status_command(client, message):
    """Get transcription status"""
    active_transcriptions = []
    
    for chat_id, transcriber in transcription_manager.transcribers.items():
        status = "🟢 Active" if transcriber.is_transcribing else "🔴 Inactive"
        active_transcriptions.append(f"Chat {chat_id}: {status}")
    
    if not active_transcriptions:
        await message.reply("🎤 No active transcriptions")
    else:
        await message.reply(
            "🎤 **Transcription Status:**\n\n" + "\n".join(active_transcriptions)
        )


@app.on_message(filters.command("test_transcription"))
async def test_transcription_command(client, message):
    """Test transcription with sample text"""
    try:
        # Create test transcriber
        transcriber = WhisperTranscription("tiny")  # Use tiny model for testing
        
        # Test if model loads
        loading_msg = await message.reply("🔄 Testing Whisper installation...")
        
        success = await transcriber.load_model()
        
        if success:
            await loading_msg.edit_text(
                "✅ **Whisper Test Successful!**\n\n"
                "Transcription is ready to use.\n"
                "Available models: tiny, base, small, medium, large\n\n"
                "Use /start_transcription to begin real-time transcription."
            )
        else:
            await loading_msg.edit_text(
                "❌ **Whisper Test Failed**\n\n"
                "Please install openai-whisper:\n"
                "`pip install openai-whisper`"
            )
            
    except Exception as e:
        await message.reply(f"❌ Error: {e}")


# Custom transcription handler
class CustomTranscriptionHandler:
    """Custom handler for transcription results"""
    
    def __init__(self, app):
        self.app = app
    
    async def handle_transcription(self, chat_id: int, result: dict):
        """Handle transcription result"""
        try:
            text = result['text'].strip()
            confidence = result.get('confidence', 0.0)
            language = result.get('language', 'unknown')
            
            if text and confidence > 0.5:  # Only send if confidence is good
                # Format transcription message
                transcription_msg = (
                    f"🎤 **Live Transcription** ({language})\n"
                    f"Confidence: {confidence:.1%}\n\n"
                    f"{text}"
                )
                
                # Send to chat
                await self.app.send_message(chat_id, transcription_msg)
                
        except Exception as e:
            print(f"Error handling transcription: {e}")


# Override transcription manager's handler
custom_handler = CustomTranscriptionHandler(app)
transcription_manager._handle_transcription = custom_handler.handle_transcription


async def main():
    """Start the transcription bot"""
    await caller.start()
    print("🎤 Transcription bot started!")
    
    await app.start()
    print("🤖 Bot is running...")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("🛑 Stopping bot...")
    finally:
        await transcription_manager.cleanup()
        await caller.stop()
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())