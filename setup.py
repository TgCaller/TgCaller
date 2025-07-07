"""
Setup script for backward compatibility and post-install hooks
"""
import os
import sys
from setuptools import setup
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    
    def run(self):
        install.run(self)
        
        # Show installation success message
        try:
            from rich.console import Console
            from rich.panel import Panel
            
            console = Console()
            
            success_message = """
[bold green]✅ TgCaller installed successfully![/bold green]

[bold white]🚀 Quick Start:[/bold white]
[cyan]  tgcaller test --api-id YOUR_API_ID --api-hash YOUR_API_HASH[/cyan]
[cyan]  tgcaller examples[/cyan]
[cyan]  tgcaller info[/cyan]

[bold white]📚 Resources:[/bold white]
[blue]  📖 Docs:    https://tgcaller.github.io/TgCaller/[/blue]
[blue]  💬 Support: https://t.me/TgCallerOfficial[/blue]
[blue]  📦 GitHub:  https://github.com/TgCaller/TgCaller[/blue]

[dim]Thank you for choosing TgCaller! 🎉[/dim]
"""
            
            console.print(Panel.fit(
                success_message,
                title="[bold blue]TgCaller Installation Complete[/bold blue]",
                border_style="green"
            ))
            
        except ImportError:
            # Fallback for systems without rich
            print("""
╔══════════════════════════════════════════════════════════════╗
║                 ✅ TgCaller Installed Successfully!           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  🚀 Quick Start:                                             ║
║    tgcaller test --api-id YOUR_API_ID --api-hash YOUR_HASH   ║
║    tgcaller examples                                         ║
║    tgcaller info                                             ║
║                                                              ║
║  📚 Resources:                                               ║
║    📖 Docs:    https://tgcaller.github.io/TgCaller/         ║
║    💬 Support: https://t.me/TgCallerOfficial                 ║
║    📦 GitHub:  https://github.com/TgCaller/TgCaller          ║
║                                                              ║
║              Thank you for choosing TgCaller! 🎉            ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    setup(
        cmdclass={
            'install': PostInstallCommand,
        }
    )