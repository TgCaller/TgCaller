#!/usr/bin/env python3
"""
TgCaller CLI Tool
"""

import argparse
import asyncio
import sys
from pathlib import Path

from . import __version__
from .client import TgCaller


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="tgcaller",
        description="TgCaller - Modern Telegram Group Calls Library"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"TgCaller {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test TgCaller installation")
    test_parser.add_argument("--api-id", type=int, help="Telegram API ID")
    test_parser.add_argument("--api-hash", help="Telegram API Hash")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show system information")
    
    args = parser.parse_args()
    
    if args.command == "test":
        asyncio.run(test_installation(args))
    elif args.command == "info":
        show_info()
    else:
        parser.print_help()


async def test_installation(args):
    """Test TgCaller installation"""
    print("🧪 Testing TgCaller installation...")
    
    try:
        # Test imports
        from pyrogram import Client
        print("✅ Pyrogram imported successfully")
        
        from .types import AudioConfig, VideoConfig
        print("✅ TgCaller types imported successfully")
        
        # Test basic functionality
        if args.api_id and args.api_hash:
            app = Client("test_session", api_id=args.api_id, api_hash=args.api_hash)
            caller = TgCaller(app)
            print("✅ TgCaller client created successfully")
        
        print("🎉 TgCaller installation test completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def show_info():
    """Show system information"""
    import platform
    import sys
    
    print("📊 TgCaller System Information")
    print("=" * 40)
    print(f"TgCaller Version: {__version__}")
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()[0]}")
    
    # Check dependencies
    print("\n📦 Dependencies:")
    dependencies = [
        "pyrogram", "aiortc", "aiofiles", "aiohttp",
        "ffmpeg", "numpy", "pyaudio", "soundfile"
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} (not installed)")


if __name__ == "__main__":
    main()