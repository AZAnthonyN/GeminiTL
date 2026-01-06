
"""
Main entry point for the GeminiTL Novel Translation Tool.

This script can be run in two modes:
1. GUI mode (default): Launches the graphical user interface
2. CLI mode: Runs command-line interface when arguments are provided

Usage:
    python main.py              # Launch GUI
    python main.py --help       # Show CLI help
    python main.py translate    # Run translation via CLI
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path if it's not already there
src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path.resolve()) not in sys.path:
    sys.path.insert(0, str(src_path.resolve()))


def main():
    """
    Main entry point that routes to either CLI or GUI mode.

    If command-line arguments are provided, use CLI mode.
    Otherwise, launch the GUI.
    """
    # Ensure we're in the correct working directory (project root)
    # This is important for relative paths used in the application
    os.chdir(Path(__file__).parent)

    # Check if CLI arguments are provided (excluding the script name)
    if len(sys.argv) > 1:
        # CLI mode - import and run CLI
        from cli import main as cli_main
        cli_main()
    else:
        # GUI mode - launch the graphical interface
        import wx
        from gui.app import TranslationApp

        app = wx.App()
        frame = TranslationApp()
        frame.Show()
        app.MainLoop()


if __name__ == "__main__":
    main()
    

