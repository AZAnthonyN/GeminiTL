"""
Output Combiner module for the novel translation tool.

This module provides functionality for:
- Combining multiple text files into a single output
- Creating EPUB files from combined text
- Managing file organization and output formats
"""

import os
import re
import wx
from typing import List, Optional, Callable, Any
from pathlib import Path
from .epuboutputcreator import EPUBOutputCreator

class OutputCombiner:
    """
    Handles combining and outputting text files.
    
    This class provides functionality for:
    - Combining multiple text files into a single output
    - Creating EPUB files from combined text
    - Managing file organization and output formats
    """
    
    def __init__(self, log_function: Optional[Callable] = None):
        """
        Initialize the OutputCombiner.
        
        Args:
            log_function: Optional function to use for logging (defaults to print)
        """
        self.log_function = log_function or print
        self.epub_creator = EPUBOutputCreator(log_function)

    @staticmethod
    def natural_sort_key(key: str) -> List[Any]:
        """
        Helper function to generate a key for natural sorting (e.g., 1, 2, 10 instead of 1, 10, 2).
        
        Args:
            key: The string to generate a sort key for
            
        Returns:
            List of parts for natural sorting
        """
        return [int(c) if c.isdigit() else c.lower() for c in re.split('([0-9]+)', key)]
    
    def concatenate_files(self, folder_name: str, output_file: str, 
                         save_as_epub: bool = True, reference_epub: Optional[str] = None,
                         image_dir: Optional[str] = None) -> None:
        """
        Creates an EPUB from text files in a folder.

        Args:
            folder_name: Path to the folder containing text files
            output_file: Path to save the output EPUB file
            save_as_epub: Always True, kept for backward compatibility
            reference_epub: Path to a reference EPUB for ordering (optional)
            image_dir: Path to image directory for EPUB (required)
        """
        if not os.path.exists(folder_name):
            wx.MessageBox(f"Folder '{folder_name}' does not exist.", "Error", wx.OK | wx.ICON_ERROR)
            return

        txt_files = [f for f in os.listdir(folder_name) if f.endswith('.txt')]
        if not txt_files:
            wx.MessageBox("No .txt files found.", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # Check if the output file already exists
        if os.path.exists(output_file):
            overwrite = wx.MessageBox(f"{output_file} already exists. Overwrite?", "Overwrite Confirmation", wx.YES_NO | wx.ICON_QUESTION)
            if overwrite != wx.YES:
                return

        if not image_dir:
            wx.MessageBox("No image directory provided. EPUB creation canceled.", "Error", wx.OK | wx.ICON_ERROR)
            return

        try:
            self.log_function(f"Creating EPUB from {len(txt_files)} files in {folder_name}")

            # Show user-friendly output path
            try:
                relative_output = os.path.relpath(output_file, os.getcwd())
                self.log_function(f"Output will be saved to: {relative_output}")
            except ValueError:
                self.log_function(f"Output will be saved to: {output_file}")

            # Create EPUB using EPUBOutputCreator
            self.epub_creator.create_epub(
                output_dir=folder_name,
                epub_name=output_file,
                image_dir=image_dir,
                reference_epub=reference_epub
            )

            # Show user-friendly completion message
            try:
                relative_output = os.path.relpath(output_file, os.getcwd())
                self.log_function(f"EPUB creation complete: {relative_output}")
            except ValueError:
                self.log_function(f"EPUB creation complete: {output_file}")
        except Exception as e:
            self.log_function(f"Error creating EPUB: {str(e)}")
            wx.MessageBox(f"Failed to create EPUB: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)
            raise

    def show_save_dialog(self, folder_name: str) -> None:
        """
        Launches a GUI to save concatenated text as EPUB.
        
        Args:
            folder_name: Path to the folder containing text files
        """
        # Get the selected folder name for the EPUB name
        selected_folder_name = os.path.basename(os.path.normpath(folder_name))
        
        # Create the compiled_epubs directory if it doesn't exist
        compiled_dir = os.path.join(os.getcwd(), "compiled_epubs")
        os.makedirs(compiled_dir, exist_ok=True)
        
        # Set the default EPUB filename based on the selected folder name
        epub_filename = f"{selected_folder_name}.epub"
        output_file_epub = os.path.join(compiled_dir, epub_filename)
        
        # Check if file already exists and handle accordingly
        if os.path.exists(output_file_epub):
            response = wx.MessageBox(
                f"The file {epub_filename} already exists in the compiled_epubs folder. Overwrite?",
                "File Exists",
                wx.YES_NO | wx.ICON_QUESTION
            )
            if response != wx.YES:
                # Generate a unique filename with timestamp
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                epub_filename = f"{selected_folder_name}_{timestamp}.epub"
                output_file_epub = os.path.join(compiled_dir, epub_filename)

        # Select image directory
        with wx.DirDialog(None, "Select Image Directory for EPUB") as dialog:
            if dialog.ShowModal() != wx.ID_OK:
                wx.MessageBox("No image directory selected. EPUB creation canceled.", "Error", wx.OK | wx.ICON_ERROR)
                return
            image_dir = dialog.GetPath()
        
        # Skip reference EPUB selection
        reference_epub = None
        
        # Create the EPUB
        try:
            self.concatenate_files(
                folder_name, output_file_epub, 
                save_as_epub=True, reference_epub=reference_epub, image_dir=image_dir
            )
            
            # Show success message with user-friendly file path
            try:
                relative_path = os.path.relpath(output_file_epub, os.getcwd())
                display_path = relative_path
            except ValueError:
                display_path = str(output_file_epub)

            wx.MessageBox(
                f"EPUB successfully created!\n\nLocation: {display_path}",
                "EPUB Created",
                wx.OK | wx.ICON_INFORMATION
            )
        except Exception as e:
            wx.MessageBox(f"Failed to create EPUB: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

def main() -> None:
    """Entry point for the application."""
    app = wx.App()

    with wx.DirDialog(None, "Select Folder Containing Text Files") as dialog:
        if dialog.ShowModal() != wx.ID_OK:
            print("No folder selected. Exiting.")
            return
        folder_name = dialog.GetPath()

    combiner = OutputCombiner()
    combiner.show_save_dialog(folder_name)

    app.MainLoop()

if __name__ == "__main__":
    main()
