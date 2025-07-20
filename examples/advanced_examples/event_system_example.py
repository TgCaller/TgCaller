#!/usr/bin/env python3
"""
Event System Example - Filter-based Handlers
"""

import asyncio
import os
from pyrogram import Client
from tgcaller import TgCaller, Filters, and_filter, or_filter
from tgcaller.types import CallUpdate, CallStatus

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("event_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)

# Test chat IDs
CHAT_1 = -1001234567890
CHAT_2 = -1009876543210


# Handler functions
async def general_handler(client, update):
    """General handler for all events"""
    print(f"🔔 General: {update.status} in chat {update.chat_id}")


async def chat1_handler(client, update):
    """Handler for specific chat only"""
    print(f"📱 Chat1 Handler: {update.status} in chat {update.chat_id}")


async def chat2_handler(client, update):
    """Handler for another specific chat"""
    print(f"📱 Chat2 Handler: {update.status} in chat {update.chat_id}")


async def playing_status_handler(client, update):
    """Handler for playing status only"""
    print(f"▶️ Playing Handler: Stream started in chat {update.chat_id}")


async def high_priority_handler(client, update):
    """High priority handler (called first)"""
    print(f"⚡ High Priority: {update.status} in chat {update.chat_id}")


async def combined_filter_handler(client, update):
    """Handler with combined filters"""
    print(f"🎯 Combined Filter: {update.status} in chat {update.chat_id}")


def sync_handler(client, update):
    """Synchronous handler example"""
    print(f"🔄 Sync Handler: {update.status} in chat {update.chat_id}")


async def setup_handlers():
    """Setup various handlers with different filters"""
    
    # General handler (no filter)
    caller.add_handler(general_handler, priority=0)
    print("✅ Added general handler")
    
    # Chat-specific handlers
    caller.add_handler(
        chat1_handler,
        filters=Filters.chat_id(CHAT_1),
        priority=5
    )
    print(f"✅ Added handler for chat {CHAT_1}")
    
    caller.add_handler(
        chat2_handler,
        filters=Filters.chat_id(CHAT_2),
        priority=5
    )
    print(f"✅ Added handler for chat {CHAT_2}")
    
    # Status-specific handler
    caller.add_handler(
        playing_status_handler,
        filters=Filters.status("playing"),
        priority=3
    )
    print("✅ Added playing status handler")
    
    # High priority handler
    caller.add_handler(
        high_priority_handler,
        priority=10
    )
    print("✅ Added high priority handler")
    
    # Combined filter (AND logic)
    caller.add_handler(
        combined_filter_handler,
        filters=and_filter(
            Filters.chat_id(CHAT_1),
            Filters.status("connected")
        ),
        priority=7
    )
    print("✅ Added combined filter handler (Chat1 AND Connected)")
    
    # Synchronous handler
    caller.add_handler(sync_handler, priority=1)
    print("✅ Added synchronous handler")
    
    print(f"\n📊 Total handlers registered: {caller._event_system.get_handlers_count()}")


async def simulate_events():
    """Simulate various events to test handlers"""
    await asyncio.sleep(2)  # Wait for setup
    
    print("\n🎬 Starting event simulation...\n")
    
    # Simulate events for Chat 1
    print("--- Events for Chat 1 ---")
    
    update1 = CallUpdate(
        chat_id=CHAT_1,
        status=CallStatus.CONNECTING,
        message="Connecting to call"
    )
    await caller._emit_event('test_event', update1)
    await asyncio.sleep(0.5)
    
    update2 = CallUpdate(
        chat_id=CHAT_1,
        status=CallStatus.CONNECTED,
        message="Connected to call"
    )
    await caller._emit_event('test_event', update2)
    await asyncio.sleep(0.5)
    
    update3 = CallUpdate(
        chat_id=CHAT_1,
        status=CallStatus.PLAYING,
        message="Playing media"
    )
    await caller._emit_event('test_event', update3)
    await asyncio.sleep(1)
    
    # Simulate events for Chat 2
    print("\n--- Events for Chat 2 ---")
    
    update4 = CallUpdate(
        chat_id=CHAT_2,
        status=CallStatus.CONNECTED,
        message="Connected to call"
    )
    await caller._emit_event('test_event', update4)
    await asyncio.sleep(0.5)
    
    update5 = CallUpdate(
        chat_id=CHAT_2,
        status=CallStatus.PLAYING,
        message="Playing media"
    )
    await caller._emit_event('test_event', update5)
    await asyncio.sleep(1)
    
    # Test handler removal
    print("\n--- Testing Handler Removal ---")
    success = caller.remove_handler(chat1_handler)
    print(f"Removed chat1_handler: {success}")
    print(f"Handlers remaining: {caller._event_system.get_handlers_count()}")
    
    # Test event after removal
    update6 = CallUpdate(
        chat_id=CHAT_1,
        status=CallStatus.ENDED,
        message="Call ended"
    )
    await caller._emit_event('test_event', update6)


async def test_or_filter():
    """Test OR filter functionality"""
    await asyncio.sleep(5)  # Wait for other tests
    
    print("\n--- Testing OR Filter ---")
    
    async def or_filter_handler(client, update):
        print(f"🔀 OR Filter: {update.status} in chat {update.chat_id}")
    
    # Add handler with OR filter (Chat1 OR Chat2)
    caller.add_handler(
        or_filter_handler,
        filters=or_filter(
            Filters.chat_id(CHAT_1),
            Filters.chat_id(CHAT_2)
        ),
        priority=8
    )
    
    # Test with different chats
    update_chat1 = CallUpdate(
        chat_id=CHAT_1,
        status=CallStatus.PAUSED,
        message="Paused"
    )
    await caller._emit_event('test_event', update_chat1)
    
    update_chat2 = CallUpdate(
        chat_id=CHAT_2,
        status=CallStatus.PAUSED,
        message="Paused"
    )
    await caller._emit_event('test_event', update_chat2)
    
    # Test with different chat (should not trigger OR filter)
    update_chat3 = CallUpdate(
        chat_id=-1005566778899,
        status=CallStatus.PAUSED,
        message="Paused"
    )
    await caller._emit_event('test_event', update_chat3)


async def main():
    """Start the event system example"""
    await caller.start()
    print("🚀 TgCaller started!")
    
    # Setup handlers
    await setup_handlers()
    
    # Start event simulation
    asyncio.create_task(simulate_events())
    asyncio.create_task(test_or_filter())
    
    print("\n🎯 Event System Features:")
    print("  ✅ Filter-based handler registration")
    print("  ✅ Priority-based handler ordering")
    print("  ✅ AND/OR filter combinations")
    print("  ✅ Synchronous and asynchronous handlers")
    print("  ✅ Dynamic handler removal")
    print("  ✅ Event propagation to matching handlers")
    
    try:
        await asyncio.sleep(10)  # Run for 10 seconds
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
    finally:
        await caller.stop()


if __name__ == "__main__":
    asyncio.run(main())