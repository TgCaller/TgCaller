#!/usr/bin/env python3
"""
TgCaller CLI Tool - Professional Command Line Interface
"""

import argparse
import asyncio
import sys
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.text import Text
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from . import __version__
from .client import TgCaller

console = Console() if RICH_AVAILABLE else None


def show_banner():
    """Show TgCaller ASCII banner"""
    if RICH_AVAILABLE:
        banner_text = """
[bold purple]████████╗ ██████╗  ██████╗ █████╗ ██╗     ██╗     ███████╗██████╗ [/bold purple]
[bold purple]╚══██╔══╝██╔════╝ ██╔════╝██╔══██╗██║     ██║     ██╔════╝██╔══██╗[/bold purple]
[bold purple]   ██║   ██║  ███╗██║     ███████║██║     ██║     █████╗  ██████╔╝[/bold purple]
[bold purple]   ██║   ██║   ██║██║     ██╔══██║██║     ██║     ██╔══╝  ██╔══██╗[/bold purple]
[bold purple]   ██║   ╚██████╔╝╚██████╗██║  ██║███████╗███████╗███████╗██║  ██║[/bold purple]
[bold purple]   ╚═╝    ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝  ╚═╝[/bold purple]

[bold white]🎯 Modern, Fast, and Reliable Telegram Group Calls Library[/bold white]
[dim]Built for developers who need a simple yet powerful solution[/dim]
"""
        
        console.print(Panel.fit(
            banner_text,
            title=f"[bold blue]TgCaller CLI v{__version__}[/bold blue]",
            subtitle="[dim]by TgCaller Team[/dim]",
            border_style="purple"
        ))
    else:
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                        TgCaller CLI v{__version__}                        ║
║          Modern Telegram Group Calls Library                ║
╚══════════════════════════════════════════════════════════════╝
""")


def show_links():
    """Show important links"""
    if RICH_AVAILABLE:
        links_table = Table(show_header=False, box=None, padding=(0, 2))
        links_table.add_column("Icon", style="bold blue")
        links_table.add_column("Description", style="white")
        links_table.add_column("URL", style="cyan")
        
        links_table.add_row("📦", "GitHub Repository", "https://github.com/TgCaller/TgCaller")
        links_table.add_row("📚", "Documentation", "https://tgcaller.github.io/TgCaller/")
        links_table.add_row("💬", "Telegram Support", "https://t.me/TgCallerOfficial")
        links_table.add_row("🐍", "PyPI Package", "https://pypi.org/project/tgcaller/")
        
        console.print("\n")
        console.print(Panel(links_table, title="[bold green]🔗 Quick Links[/bold green]", border_style="green"))
    else:
        print("""
🔗 Quick Links:
  📦 GitHub:    https://github.com/TgCaller/TgCaller
  📚 Docs:      https://tgcaller.github.io/TgCaller/
  💬 Support:   https://t.me/TgCallerOfficial
  🐍 PyPI:      https://pypi.org/project/tgcaller/
""")


def check_dependencies():
    """Check system dependencies"""
    deps = {
        "Python": {
            "command": [sys.executable, "--version"],
            "required": True
        },
        "FFmpeg": {
            "command": ["ffmpeg", "-version"],
            "required": True
        },
        "Pyrogram": {
            "module": "pyrogram",
            "required": True
        },
        "yt-dlp": {
            "module": "yt_dlp",
            "required": False
        },
        "OpenAI Whisper": {
            "module": "whisper",
            "required": False
        },
        "OpenCV": {
            "module": "cv2",
            "required": False
        }
    }
    
    results = {}
    
    for name, config in deps.items():
        try:
            if "command" in config:
                result = subprocess.run(
                    config["command"], 
                    capture_output=True, 
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0] if result.stdout else "Unknown"
                    results[name] = {"status": "✅", "version": version, "required": config["required"]}
                else:
                    results[name] = {"status": "❌", "version": "Not found", "required": config["required"]}
            elif "module" in config:
                __import__(config["module"])
                try:
                    module = __import__(config["module"])
                    version = getattr(module, "__version__", "Unknown")
                except:
                    version = "Installed"
                results[name] = {"status": "✅", "version": version, "required": config["required"]}
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ImportError, FileNotFoundError):
            results[name] = {"status": "❌", "version": "Not found", "required": config["required"]}
    
    return results


def show_system_info():
    """Show system information"""
    if RICH_AVAILABLE:
        # System Info Table
        sys_table = Table(show_header=False, box=None, padding=(0, 2))
        sys_table.add_column("Property", style="bold cyan")
        sys_table.add_column("Value", style="white")
        
        sys_table.add_row("TgCaller Version", __version__)
        sys_table.add_row("Python Version", f"{sys.version.split()[0]}")
        sys_table.add_row("Platform", platform.platform())
        sys_table.add_row("Architecture", platform.architecture()[0])
        sys_table.add_row("Processor", platform.processor() or "Unknown")
        
        console.print(Panel(sys_table, title="[bold blue]💻 System Information[/bold blue]", border_style="blue"))
        
        # Dependencies Table
        deps = check_dependencies()
        deps_table = Table(show_header=True, box=None, padding=(0, 2))
        deps_table.add_column("Component", style="bold")
        deps_table.add_column("Status", justify="center")
        deps_table.add_column("Version", style="dim")
        deps_table.add_column("Required", justify="center")
        
        for name, info in deps.items():
            required_icon = "🔴" if info["required"] else "🟡"
            deps_table.add_row(
                name,
                info["status"],
                info["version"][:50] + "..." if len(info["version"]) > 50 else info["version"],
                required_icon
            )
        
        console.print("\n")
        console.print(Panel(deps_table, title="[bold green]📦 Dependencies Status[/bold green]", border_style="green"))
        
        # Legend
        console.print("\n[dim]Legend: 🔴 Required | 🟡 Optional | ✅ Installed | ❌ Missing[/dim]")
        
    else:
        print(f"""
💻 System Information:
  TgCaller Version: {__version__}
  Python Version:   {sys.version.split()[0]}
  Platform:         {platform.platform()}
  Architecture:     {platform.architecture()[0]}

📦 Dependencies Status:""")
        
        deps = check_dependencies()
        for name, info in deps.items():
            required = "Required" if info["required"] else "Optional"
            print(f"  {info['status']} {name:<15} {info['version']:<20} ({required})")


async def test_installation(args):
    """Test TgCaller installation"""
    if RICH_AVAILABLE:
        console.print("\n[bold yellow]🧪 Testing TgCaller Installation...[/bold yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Test imports
            task1 = progress.add_task("Testing imports...", total=None)
            try:
                from pyrogram import Client
                progress.update(task1, description="✅ Pyrogram imported successfully")
                await asyncio.sleep(0.5)
                
                from .types import AudioConfig, VideoConfig
                progress.update(task1, description="✅ TgCaller types imported successfully")
                await asyncio.sleep(0.5)
                
                progress.remove_task(task1)
                
            except ImportError as e:
                progress.update(task1, description=f"❌ Import error: {e}")
                progress.remove_task(task1)
                return
            
            # Test basic functionality
            if args.api_id and args.api_hash:
                task2 = progress.add_task("Testing TgCaller client...", total=None)
                try:
                    app = Client("test_session", api_id=args.api_id, api_hash=args.api_hash)
                    caller = TgCaller(app)
                    progress.update(task2, description="✅ TgCaller client created successfully")
                    await asyncio.sleep(0.5)
                    progress.remove_task(task2)
                except Exception as e:
                    progress.update(task2, description=f"❌ Client error: {e}")
                    progress.remove_task(task2)
                    return
        
        console.print("\n[bold green]🎉 TgCaller installation test completed successfully![/bold green]")
        
    else:
        print("🧪 Testing TgCaller installation...")
        
        try:
            from pyrogram import Client
            print("✅ Pyrogram imported successfully")
            
            from .types import AudioConfig, VideoConfig
            print("✅ TgCaller types imported successfully")
            
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


def show_examples():
    """Show usage examples"""
    if RICH_AVAILABLE:
        examples = [
            ("Basic Usage", """
from pyrogram import Client
from tgcaller import TgCaller

app = Client("my_session", api_id=API_ID, api_hash=API_HASH)
caller = TgCaller(app)

@caller.on_stream_end
async def on_stream_end(client, update):
    print(f"Stream ended in {update.chat_id}")

async def main():
    await caller.start()
    await caller.join_call(-1001234567890)
    await caller.play(-1001234567890, "song.mp3")
"""),
            ("Music Bot", """
from pyrogram import Client, filters
from tgcaller import TgCaller

app = Client("music_bot")
caller = TgCaller(app)

@app.on_message(filters.command("play"))
async def play_music(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /play <song_name>")
    
    song = message.command[1]
    chat_id = message.chat.id
    
    if not caller.is_connected(chat_id):
        await caller.join_call(chat_id)
    
    await caller.play(chat_id, f"music/{song}.mp3")
    await message.reply(f"🎵 Playing: {song}")

app.run()
"""),
            ("Advanced Features", """
from tgcaller.advanced import (
    YouTubeStreamer,
    ScreenShareStreamer,
    WhisperTranscription
)

# Stream YouTube videos
youtube = YouTubeStreamer(caller)
await youtube.play_youtube_url(chat_id, "https://youtube.com/watch?v=...")

# Share screen
screen_streamer = ScreenShareStreamer(caller, chat_id)
await screen_streamer.start_streaming(monitor_index=1)

# Real-time transcription
transcriber = WhisperTranscription("base")
await transcriber.start_transcription()
""")
        ]
        
        for title, code in examples:
            console.print(f"\n[bold cyan]📝 {title}[/bold cyan]")
            console.print(Panel(code.strip(), border_style="dim"))
    else:
        print("""
📝 Usage Examples:

1. Basic Usage:
   from tgcaller import TgCaller
   caller = TgCaller(app)
   await caller.play(chat_id, "song.mp3")

2. Music Bot:
   @app.on_message(filters.command("play"))
   async def play_music(client, message):
       await caller.play(chat_id, "music.mp3")

3. Advanced Features:
   - YouTube streaming
   - Screen sharing
   - Real-time transcription
   - Audio/video filters
""")


def show_diagnose():
    """Show diagnostic information"""
    if RICH_AVAILABLE:
        console.print("\n[bold yellow]🔍 TgCaller Diagnostic Report[/bold yellow]\n")
    else:
        print("\n🔍 TgCaller Diagnostic Report\n")
    
    show_system_info()
    
    if RICH_AVAILABLE:
        console.print("\n[bold blue]💡 Recommendations:[/bold blue]")
        
        deps = check_dependencies()
        missing_required = [name for name, info in deps.items() if info["status"] == "❌" and info["required"]]
        missing_optional = [name for name, info in deps.items() if info["status"] == "❌" and not info["required"]]
        
        if missing_required:
            console.print(f"[red]🔴 Install required dependencies: {', '.join(missing_required)}[/red]")
        
        if missing_optional:
            console.print(f"[yellow]🟡 Optional features available: {', '.join(missing_optional)}[/yellow]")
        
        if not missing_required:
            console.print("[green]✅ All required dependencies are installed![/green]")
    else:
        print("\n💡 Recommendations:")
        deps = check_dependencies()
        missing_required = [name for name, info in deps.items() if info["status"] == "❌" and info["required"]]
        
        if missing_required:
            print(f"🔴 Install required dependencies: {', '.join(missing_required)}")
        else:
            print("✅ All required dependencies are installed!")


def show_secret():
    """Easter egg function"""
    if RICH_AVAILABLE:
        secret_text = """
[bold purple]🚀 You found the secret developer mode![/bold purple]

[bold white]Special thanks to:[/bold white]
[cyan]• Ahmad Raza - Project Creator[/cyan]
[cyan]• TgCaller Team - Core Development[/cyan]
[cyan]• Community Contributors[/cyan]

[bold yellow]🎯 Fun Facts:[/bold yellow]
[white]• TgCaller is 3x faster than pytgcalls[/white]
[white]• Built with ❤️ for the Telegram community[/white]
[white]• Over 25+ advanced features included[/white]

[dim]Say hi to the team at @TgCallerOfficial! 👋[/dim]
"""
        console.print(Panel.fit(secret_text, title="[bold red]🎉 Secret Mode Activated[/bold red]", border_style="red"))
    else:
        print("""
🚀 You found the secret developer mode!

Special thanks to:
• Ahmad Raza - Project Creator
• TgCaller Team - Core Development
• Community Contributors

🎯 Fun Facts:
• TgCaller is 3x faster than pytgcalls
• Built with ❤️ for the Telegram community
• Over 25+ advanced features included

Say hi to the team at @TgCallerOfficial! 👋
""")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="tgcaller",
        description="TgCaller - Modern Telegram Group Calls Library",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  tgcaller test --api-id 12345 --api-hash "your_hash"
  tgcaller info
  tgcaller diagnose
  tgcaller examples

For more information, visit: https://tgcaller.github.io/TgCaller/
"""
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"TgCaller {__version__}"
    )
    
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Don't show the banner"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test TgCaller installation")
    test_parser.add_argument("--api-id", type=int, help="Telegram API ID")
    test_parser.add_argument("--api-hash", help="Telegram API Hash")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show system information")
    
    # Diagnose command
    diagnose_parser = subparsers.add_parser("diagnose", help="Run diagnostic checks")
    
    # Examples command
    examples_parser = subparsers.add_parser("examples", help="Show usage examples")
    
    # Links command
    links_parser = subparsers.add_parser("links", help="Show important links")
    
    # Secret command (easter egg)
    secret_parser = subparsers.add_parser("secret", help="🤫")
    
    args = parser.parse_args()
    
    # Show banner unless disabled
    if not args.no_banner and args.command != "secret":
        show_banner()
    
    if args.command == "test":
        asyncio.run(test_installation(args))
    elif args.command == "info":
        show_system_info()
    elif args.command == "diagnose":
        show_diagnose()
    elif args.command == "examples":
        show_examples()
    elif args.command == "links":
        show_links()
    elif args.command == "secret":
        show_secret()
    else:
        if not args.no_banner:
            show_links()
        parser.print_help()


if __name__ == "__main__":
    main()