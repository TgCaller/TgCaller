#!/usr/bin/env python3
"""
Internal Systems Example - Demonstrate TgCaller's internal architecture
"""

import asyncio
import os
from pyrogram import Client
from tgcaller import TgCaller, AudioConfig

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("internal_systems_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)


async def demonstrate_connection_manager():
    """Demonstrate connection manager features"""
    print("\n🔗 Connection Manager Demo:")
    print("=" * 50)
    
    chat_id = -1001234567890
    
    # Test connection
    print("📞 Connecting to call...")
    success = await caller.connection_manager.connect_call(chat_id)
    print(f"Connection result: {'✅ Success' if success else '❌ Failed'}")
    
    # Check connection state
    state = caller.connection_manager.get_connection_state(chat_id)
    print(f"Connection state: {state.value}")
    
    # Get active connections
    active = caller.connection_manager.get_active_connections()
    print(f"Active connections: {len(active)}")
    
    # Disconnect
    print("📞 Disconnecting from call...")
    success = await caller.connection_manager.disconnect_call(chat_id)
    print(f"Disconnect result: {'✅ Success' if success else '❌ Failed'}")


async def demonstrate_cache_manager():
    """Demonstrate cache manager features"""
    print("\n💾 Cache Manager Demo:")
    print("=" * 50)
    
    cache = caller.cache_manager
    
    # Basic caching
    print("📝 Testing basic cache operations...")
    cache.set("test_key", "test_value", ttl=60.0)
    value = cache.get("test_key")
    print(f"Cached value: {value}")
    
    # Peer caching
    print("👤 Testing peer caching...")
    chat_id = -1001234567890
    peer_data = {"id": 123456, "access_hash": 789012}
    
    cache.cache_user_peer(chat_id, peer_data)
    cached_peer = cache.get_user_peer(chat_id)
    print(f"Cached peer: {cached_peer}")
    
    # Cache statistics
    stats = cache.get_stats()
    print("📊 Cache Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def demonstrate_stream_handler():
    """Demonstrate stream handler features"""
    print("\n🎵 Stream Handler Demo:")
    print("=" * 50)
    
    from tgcaller.types import MediaStream, Device, DeviceType
    
    chat_id = -1001234567890
    stream = MediaStream("demo_audio.mp3")
    device = Device(device_type=DeviceType.FILE, name="Demo File")
    
    # Start stream
    print("▶️ Starting stream...")
    success = await caller.stream_handler.start_stream(chat_id, stream, device)
    print(f"Stream start result: {'✅ Success' if success else '❌ Failed'}")
    
    # Check stream state
    state = caller.stream_handler.get_stream_state(chat_id)
    print(f"Stream state: {state.value if state else 'None'}")
    
    # Get stream stats
    await asyncio.sleep(2)  # Let it run for a bit
    stats = caller.stream_handler.get_stream_stats(chat_id)
    if stats:
        print("📊 Stream Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # Stop stream
    print("⏹️ Stopping stream...")
    success = await caller.stream_handler.stop_stream(chat_id)
    print(f"Stream stop result: {'✅ Success' if success else '❌ Failed'}")


async def demonstrate_call_holder():
    """Demonstrate call holder features"""
    print("\n📞 Call Holder Demo:")
    print("=" * 50)
    
    from tgcaller.utilities import CallHolder
    
    call_holder = CallHolder(max_concurrent_calls=5)
    chat_id = -1001234567890
    audio_config = AudioConfig.high_quality()
    
    # Create call session
    print("🆕 Creating call session...")
    success = await call_holder.create_call(chat_id, audio_config)
    print(f"Call creation result: {'✅ Success' if success else '❌ Failed'}")
    
    # Connect call
    print("🔗 Connecting call...")
    success = await call_holder.connect_call(chat_id)
    print(f"Call connection result: {'✅ Success' if success else '❌ Failed'}")
    
    # Get session info
    session = call_holder.get_session(chat_id)
    if session:
        print(f"📊 Session Info:")
        print(f"  State: {session.state.value}")
        print(f"  Duration: {session.duration:.1f}s")
        print(f"  Has Video: {session.has_video}")
        print(f"  Volume: {session.volume}")
    
    # Update session
    call_holder.update_volume(chat_id, 0.8)
    call_holder.set_muted(chat_id, True)
    
    # Get statistics
    stats = call_holder.get_statistics()
    print("📊 Call Holder Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # End call
    print("📞 Ending call...")
    success = await call_holder.end_call(chat_id, success=True)
    print(f"Call end result: {'✅ Success' if success else '❌ Failed'}")


async def demonstrate_cpu_monitor():
    """Demonstrate CPU monitoring"""
    print("\n💻 CPU Monitor Demo:")
    print("=" * 50)
    
    from tgcaller.utilities import CpuMonitor
    
    cpu_monitor = CpuMonitor(update_interval=2.0)
    
    # Add callback
    def cpu_callback(stats):
        print(f"🔄 CPU: {stats.overall_percent:.1f}%, Memory: {stats.memory_mb:.1f}MB")
    
    cpu_monitor.add_callback(cpu_callback)
    
    # Start monitoring
    print("🚀 Starting CPU monitoring...")
    await cpu_monitor.start_monitoring()
    
    # Let it run for a few cycles
    await asyncio.sleep(6)
    
    # Get current stats
    current_stats = cpu_monitor.get_current_stats()
    if current_stats:
        print("📊 Current CPU Stats:")
        print(f"  Overall CPU: {current_stats.overall_percent:.1f}%")
        print(f"  Process CPU: {current_stats.process_percent:.1f}%")
        print(f"  Memory: {current_stats.memory_mb:.1f}MB ({current_stats.memory_percent:.1f}%)")
        print(f"  Load Average: {current_stats.load_average}")
    
    # Stop monitoring
    await cpu_monitor.stop_monitoring()
    print("⏹️ CPU monitoring stopped")


async def demonstrate_ping_monitor():
    """Demonstrate ping monitoring"""
    print("\n🌐 Ping Monitor Demo:")
    print("=" * 50)
    
    from tgcaller.utilities import PingMonitor
    
    ping_monitor = PingMonitor(
        hosts=["8.8.8.8", "1.1.1.1"],
        interval=3.0
    )
    
    # Add callback
    def ping_callback(results):
        for result in results:
            status = "✅" if result.success else "❌"
            latency = f"{result.latency_ms:.1f}ms" if result.latency_ms else "N/A"
            print(f"🏓 {result.host}: {status} {latency}")
    
    ping_monitor.add_callback(ping_callback)
    
    # Start monitoring
    print("🚀 Starting ping monitoring...")
    await ping_monitor.start_monitoring()
    
    # Let it run for a few cycles
    await asyncio.sleep(10)
    
    # Get network health
    is_healthy = ping_monitor.is_network_healthy()
    print(f"🌐 Network Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
    
    # Get best host
    best_host = ping_monitor.get_best_host()
    print(f"🎯 Best Host: {best_host}")
    
    # Stop monitoring
    await ping_monitor.stop_monitoring()
    print("⏹️ Ping monitoring stopped")


async def demonstrate_retry_manager():
    """Demonstrate retry manager"""
    print("\n🔄 Retry Manager Demo:")
    print("=" * 50)
    
    retry_manager = caller.retry_manager
    
    # Test successful operation
    print("✅ Testing successful operation...")
    
    async def successful_op():
        return "Operation completed successfully"
    
    result = await retry_manager.retry_operation(successful_op, "success_test")
    print(f"Result: {result}")
    
    # Test operation with retries
    print("🔄 Testing operation with retries...")
    
    attempt_count = 0
    
    async def failing_then_success():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception(f"Attempt {attempt_count} failed")
        return f"Success on attempt {attempt_count}"
    
    from tgcaller.internal.retry_manager import RetryConfig
    config = RetryConfig(max_attempts=5, base_delay=0.5)
    
    try:
        result = await retry_manager.retry_operation(
            failing_then_success, 
            "retry_test", 
            config
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed after retries: {e}")


async def main():
    """Demonstrate all internal systems"""
    await caller.start()
    print("🚀 TgCaller started!")
    
    print("\n🏗️ TgCaller Internal Systems Demonstration")
    print("=" * 60)
    
    # Demonstrate each system
    await demonstrate_connection_manager()
    await demonstrate_cache_manager()
    await demonstrate_stream_handler()
    await demonstrate_call_holder()
    await demonstrate_cpu_monitor()
    await demonstrate_ping_monitor()
    await demonstrate_retry_manager()
    
    print("\n✅ All internal systems demonstrated!")
    print("\n🎯 Key Features:")
    print("  ✅ Connection management with auto-reconnection")
    print("  ✅ Intelligent caching for performance")
    print("  ✅ Advanced stream processing")
    print("  ✅ Call lifecycle management")
    print("  ✅ System resource monitoring")
    print("  ✅ Network connectivity monitoring")
    print("  ✅ Robust retry mechanisms")
    
    await caller.stop()


if __name__ == "__main__":
    asyncio.run(main())