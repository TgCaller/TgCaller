#!/usr/bin/env python3
"""
Custom HTTP API Example - External Control
"""

import asyncio
import os
import json
import aiohttp
from pyrogram import Client
from tgcaller import TgCaller, AudioConfig

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("api_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)


@caller.on_custom_update
async def handle_custom_request(client, data):
    """Handle custom API requests"""
    try:
        action = data.get('action')
        chat_id = data.get('chat_id')
        
        if action == 'join_call':
            if not chat_id:
                return {"error": "chat_id required for join_call"}
            
            success = await caller.join_call(chat_id)
            return {
                "action": "join_call",
                "chat_id": chat_id,
                "success": success,
                "message": "Joined call" if success else "Failed to join call"
            }
        
        elif action == 'leave_call':
            if not chat_id:
                return {"error": "chat_id required for leave_call"}
            
            success = await caller.leave_call(chat_id)
            return {
                "action": "leave_call", 
                "chat_id": chat_id,
                "success": success,
                "message": "Left call" if success else "Failed to leave call"
            }
        
        elif action == 'play_media':
            source = data.get('source')
            if not chat_id or not source:
                return {"error": "chat_id and source required for play_media"}
            
            # Join call if not connected
            if not caller.is_connected(chat_id):
                await caller.join_call(chat_id)
            
            audio_config = AudioConfig.high_quality()
            success = await caller.play(chat_id, source, audio_config=audio_config)
            return {
                "action": "play_media",
                "chat_id": chat_id,
                "source": source,
                "success": success,
                "message": f"Playing {source}" if success else "Failed to play media"
            }
        
        elif action == 'pause':
            if not chat_id:
                return {"error": "chat_id required for pause"}
            
            success = await caller.pause(chat_id)
            return {
                "action": "pause",
                "chat_id": chat_id,
                "success": success
            }
        
        elif action == 'resume':
            if not chat_id:
                return {"error": "chat_id required for resume"}
            
            success = await caller.resume(chat_id)
            return {
                "action": "resume",
                "chat_id": chat_id,
                "success": success
            }
        
        elif action == 'set_volume':
            volume = data.get('volume')
            if not chat_id or volume is None:
                return {"error": "chat_id and volume required for set_volume"}
            
            success = await caller.set_volume(chat_id, volume)
            return {
                "action": "set_volume",
                "chat_id": chat_id,
                "volume": volume,
                "success": success
            }
        
        elif action == 'get_status':
            active_calls = caller.get_active_calls()
            return {
                "action": "get_status",
                "caller_running": caller.is_running,
                "active_calls": active_calls,
                "total_calls": len(active_calls)
            }
        
        else:
            return {
                "error": "Unknown action",
                "available_actions": [
                    "join_call", "leave_call", "play_media", 
                    "pause", "resume", "set_volume", "get_status"
                ]
            }
            
    except Exception as e:
        return {"error": f"Handler error: {str(e)}"}


async def test_api_client():
    """Test the API with sample requests"""
    await asyncio.sleep(2)  # Wait for server to start
    
    base_url = "http://localhost:8080"
    
    async with aiohttp.ClientSession() as session:
        # Test health check
        print("🔍 Testing health check...")
        async with session.get(f"{base_url}/health") as resp:
            health_data = await resp.json()
            print(f"Health: {health_data}")
        
        # Test get status
        print("\n📊 Testing get status...")
        async with session.post(f"{base_url}/", json={
            "action": "get_status"
        }) as resp:
            status_data = await resp.json()
            print(f"Status: {status_data}")
        
        # Test join call
        print("\n📞 Testing join call...")
        async with session.post(f"{base_url}/", json={
            "action": "join_call",
            "chat_id": -1001234567890
        }) as resp:
            join_data = await resp.json()
            print(f"Join: {join_data}")
        
        # Test play media
        print("\n🎵 Testing play media...")
        async with session.post(f"{base_url}/", json={
            "action": "play_media",
            "chat_id": -1001234567890,
            "source": "test_audio.mp3"
        }) as resp:
            play_data = await resp.json()
            print(f"Play: {play_data}")
        
        # Test invalid JSON
        print("\n❌ Testing invalid JSON...")
        async with session.post(f"{base_url}/", data="invalid json") as resp:
            error_data = await resp.json()
            print(f"Error: {error_data}")
        
        # Test unknown action
        print("\n❓ Testing unknown action...")
        async with session.post(f"{base_url}/", json={
            "action": "unknown_action"
        }) as resp:
            unknown_data = await resp.json()
            print(f"Unknown: {unknown_data}")


async def main():
    """Start the custom API bot"""
    await caller.start()
    print("🚀 TgCaller started!")
    
    # Enable custom API
    api_server = caller.enable_custom_api(host="localhost", port=8080)
    await caller.start_custom_api()
    print("🌐 Custom API server started on http://localhost:8080")
    
    # Start test client
    asyncio.create_task(test_api_client())
    
    print("\n📡 API Endpoints:")
    print("  GET  /health - Health check")
    print("  POST /       - Custom requests")
    print("\n📝 Example requests:")
    print('  {"action": "get_status"}')
    print('  {"action": "join_call", "chat_id": -1001234567890}')
    print('  {"action": "play_media", "chat_id": -1001234567890, "source": "song.mp3"}')
    print('  {"action": "set_volume", "chat_id": -1001234567890, "volume": 0.8}')
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        await caller.stop_custom_api()
        await caller.stop()


if __name__ == "__main__":
    asyncio.run(main())