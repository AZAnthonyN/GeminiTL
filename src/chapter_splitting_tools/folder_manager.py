"""
Folder Manager module for the novel translation tool.

Added 2025‑05‑09:
    • When clearing Output, also empties output/proofed_ai
      and removes output/images.
    • When clearing Input, removes input/images.
"""

import wx
import os
from typing import Optional, Callable
from pathlib import Path
from send2trash import send2trash
import shutil


class FolderManager:
    """Handles folder‑management operations."""

    def __init__(self, log_function: Optional[Callable] = None):
        self.log = log_function or print

        # Get the correct project directory (where the src folder is)
        # Instead of going up two levels from this file, use the current working directory
        script_dir = Path(os.getcwd())
        self.input_dir = script_dir / "input"
        self.output_dir = script_dir / "output"

        # constant sub‑folder names
        self.proofed_ai = self.output_dir / "proofed_ai"
        self.images_name = "images"

    # ---------- internal helpers ---------- #

    def _trash_path(self, path: Path) -> None:
        try:
            send2trash(str(path))
            self.log(f"Sent to Recycle Bin: {path}")
        except Exception as e:
            self.log(f"Failed to delete {path}: {e}")

    def _clear_folder_contents(self, folder: Path, display: str) -> None:
        if not folder.exists():
            self.log(f"Warning: {display} does not exist.")
            return
        for item in folder.iterdir():
            self._trash_path(item)
        self.log(f"Cleared all contents of {display}.")

    def _remove_images_folder(self, parent: Path, context: str) -> None:
        images = parent / self.images_name
        if images.exists():
            self._trash_path(images)
            self.log(f"Removed '{self.images_name}' folder inside {context} folder.")

    # ---------- public operations ---------- #

    def clear_top_level_files(self, folder: Path, display: str) -> None:
        if not folder.exists():
            self.log(f"Warning: {display} folder does not exist.")
            return
        for item in folder.iterdir():
            if item.is_file():
                self._trash_path(item)
            else:
                self.log(f"Skipped sub‑folder: {item}")
        self.log(f"Top‑level files in {display} folder sent to Recycle Bin.")

    def clear_input(self) -> None:
        self.clear_top_level_files(self.input_dir, "Input")
        self._remove_images_folder(self.input_dir, "Input")

    def clear_output(self) -> None:
        self.clear_top_level_files(self.output_dir, "Output")
        self._clear_folder_contents(self.proofed_ai, "'proofed_ai'")
        self._remove_images_folder(self.output_dir, "Output")

    # ---------- UI ---------- #

    def show_clear_dialog(self) -> None:
        # Create a simple choice dialog
        choices = ["Input", "Output", "Both"]

        # Create a temporary app if one doesn't exist
        app = wx.App.Get()
        if not app:
            app = wx.App()

        with wx.SingleChoiceDialog(None, "Select a folder to clear:", "Clear Folders", choices) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                selection = dialog.GetStringSelection()

                plural = "s" if selection == "Both" else ""

                # Confirm the action
                if wx.MessageBox(f"Are you sure you want to clear the {selection} folder{plural}?",
                               "Confirm", wx.YES_NO | wx.ICON_QUESTION) != wx.YES:
                    return

                if selection == "Input":
                    self.clear_input()
                elif selection == "Output":
                    self.clear_output()
                elif selection == "Both":
                    self.clear_input()
                    self.clear_output()

                wx.MessageBox(f"{selection} folder{plural} cleared.", "Success", wx.OK | wx.ICON_INFORMATION)


def main() -> None:
    app = wx.App()
    FolderManager().show_clear_dialog()
    app.MainLoop()


if __name__ == "__main__":
    main()
