#!/usr/bin/env python3
"""
Media Devices Example - Device Detection and Listing
"""

import asyncio
import os
from pyrogram import Client
from tgcaller import TgCaller, MediaDevices

# Configuration
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Initialize
app = Client("devices_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
caller = TgCaller(app)


def display_microphones():
    """Display available microphone devices"""
    print("🎤 Microphone Devices:")
    print("=" * 50)
    
    microphones = MediaDevices.microphone_devices()
    
    if not microphones:
        print("  ❌ No microphone devices found")
        print("  💡 Install pyaudio: pip install pyaudio")
        return
    
    for mic in microphones:
        default_marker = " (DEFAULT)" if mic.is_default else ""
        print(f"  📱 Device {mic.index}: {mic.name}{default_marker}")
        print(f"     Channels: {mic.channels}")
        print(f"     Sample Rate: {mic.sample_rate:.0f} Hz")
        print(f"     Metadata: {mic.metadata}")
        print()
    
    # Show default microphone
    default_mic = MediaDevices.get_default_microphone()
    if default_mic:
        print(f"🎯 Default Microphone: {default_mic.name} (Device {default_mic.index})")
    else:
        print("❌ No default microphone found")


def display_speakers():
    """Display available speaker devices"""
    print("\n🔊 Speaker Devices:")
    print("=" * 50)
    
    speakers = MediaDevices.speaker_devices()
    
    if not speakers:
        print("  ❌ No speaker devices found")
        print("  💡 Install pyaudio: pip install pyaudio")
        return
    
    for speaker in speakers:
        default_marker = " (DEFAULT)" if speaker.is_default else ""
        print(f"  🔊 Device {speaker.index}: {speaker.name}{default_marker}")
        print(f"     Channels: {speaker.channels}")
        print(f"     Sample Rate: {speaker.sample_rate:.0f} Hz")
        print(f"     Metadata: {speaker.metadata}")
        print()
    
    # Show default speaker
    default_speaker = MediaDevices.get_default_speaker()
    if default_speaker:
        print(f"🎯 Default Speaker: {default_speaker.name} (Device {default_speaker.index})")
    else:
        print("❌ No default speaker found")


def display_cameras():
    """Display available camera devices"""
    print("\n📹 Camera Devices:")
    print("=" * 50)
    
    cameras = MediaDevices.camera_devices()
    
    if not cameras:
        print("  ❌ No camera devices found")
        print("  💡 Install opencv-python: pip install opencv-python")
        return
    
    for camera in cameras:
        default_marker = " (DEFAULT)" if camera.is_default else ""
        print(f"  📹 Device {camera.index}: {camera.name}{default_marker}")
        print(f"     Resolution: {camera.width}x{camera.height}")
        print(f"     FPS: {camera.fps}")
        print(f"     Metadata: {camera.metadata}")
        print()
    
    # Show default camera
    default_camera = MediaDevices.get_default_camera()
    if default_camera:
        print(f"🎯 Default Camera: {default_camera.name} (Device {default_camera.index})")
    else:
        print("❌ No default camera found")


def display_screens():
    """Display available screen devices"""
    print("\n🖥️ Screen Devices:")
    print("=" * 50)
    
    screens = MediaDevices.screen_devices()
    
    if not screens:
        print("  ❌ No screen devices found")
        print("  💡 Install mss: pip install mss")
        return
    
    for screen in screens:
        primary_marker = " (PRIMARY)" if screen.is_primary else ""
        print(f"  🖥️ Screen {screen.index}: {screen.name}{primary_marker}")
        print(f"     Resolution: {screen.width}x{screen.height}")
        print(f"     Position: ({screen.x}, {screen.y})")
        print(f"     Metadata: {screen.metadata}")
        print()
    
    # Show primary screen
    primary_screen = MediaDevices.get_primary_screen()
    if primary_screen:
        print(f"🎯 Primary Screen: {primary_screen.name} (Screen {primary_screen.index})")
    else:
        print("❌ No primary screen found")


def display_device_summary():
    """Display device summary"""
    print("\n📊 Device Summary:")
    print("=" * 50)
    
    mic_count = len(MediaDevices.microphone_devices())
    speaker_count = len(MediaDevices.speaker_devices())
    camera_count = len(MediaDevices.camera_devices())
    screen_count = len(MediaDevices.screen_devices())
    
    print(f"  🎤 Microphones: {mic_count}")
    print(f"  🔊 Speakers: {speaker_count}")
    print(f"  📹 Cameras: {camera_count}")
    print(f"  🖥️ Screens: {screen_count}")
    print(f"  📱 Total Devices: {mic_count + speaker_count + camera_count + screen_count}")


def test_device_access():
    """Test accessing devices through TgCaller"""
    print("\n🧪 Testing Device Access through TgCaller:")
    print("=" * 50)
    
    # Access through caller.media_devices
    print("📱 Accessing via caller.media_devices...")
    
    mics = caller.media_devices.microphone_devices()
    print(f"  🎤 Found {len(mics)} microphones")
    
    speakers = caller.media_devices.speaker_devices()
    print(f"  🔊 Found {len(speakers)} speakers")
    
    cameras = caller.media_devices.camera_devices()
    print(f"  📹 Found {len(cameras)} cameras")
    
    screens = caller.media_devices.screen_devices()
    print(f"  🖥️ Found {len(screens)} screens")


def show_installation_tips():
    """Show installation tips for missing dependencies"""
    print("\n💡 Installation Tips:")
    print("=" * 50)
    print("  For audio devices: pip install pyaudio")
    print("  For video devices: pip install opencv-python")
    print("  For screen capture: pip install mss")
    print("  For all features: pip install tgcaller[all]")
    print("\n🔧 Troubleshooting:")
    print("  • On Ubuntu/Debian: sudo apt install portaudio19-dev")
    print("  • On macOS: brew install portaudio")
    print("  • On Windows: Install Microsoft Visual C++ Build Tools")


async def main():
    """Start the media devices example"""
    await caller.start()
    print("🚀 TgCaller started!")
    
    print("\n🔍 Detecting Media Devices...")
    print("This may take a few seconds...\n")
    
    # Display all device types
    display_microphones()
    display_speakers()
    display_cameras()
    display_screens()
    
    # Show summary
    display_device_summary()
    
    # Test device access
    test_device_access()
    
    # Show tips
    show_installation_tips()
    
    print("\n✅ Device detection complete!")
    print("\n🎯 Use these devices with TgCaller:")
    print("  • Microphone streaming: MicrophoneStreamer(caller, chat_id)")
    print("  • Screen sharing: ScreenShareStreamer(caller, chat_id)")
    print("  • Camera streaming: CameraStreamer(caller, chat_id)")
    
    await caller.stop()


if __name__ == "__main__":
    asyncio.run(main())