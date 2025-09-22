"""
Novel Splitter module for the novel translation tool.

This module provides functionality for:
- Splitting novel text files into chapters
- Fetching chapter names from Novelpia
- Managing chapter organization and output
"""

import wx
import requests
import re
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

class TextSplitterApp(wx.Frame):
    """
    GUI application for splitting novel text files into chapters.

    This class provides functionality for:
    - Loading configuration from config.txt
    - Fetching chapter names from Novelpia
    - Splitting input text files into chapter files
    - Managing user interface and file operations
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the TextSplitterApp.

        Args:
            parent: The parent window (optional)
        """
        super().__init__(parent, title="Novelpia Scraper Splitter", size=(600, 600))

        # Variables
        self.input_file = ""
        self.output_dir = ""
        self.start_index = 1
        self.novel_no = ""
        self.login_key = ""  # Will be autofilled from config
        self.chapter_names: List[str] = []

        # Attempt to read config.txt from two folders up and autofill the login key
        self.load_config()

        # Build the UI
        self.create_widgets()

    def load_config(self) -> None:
        """
        Reads config.txt from two folders up (../../config.txt)
        and extracts the line starting with 'login_key=' to autofill self.login_key.
        """
        # Compute the path to config.txt two folders above this file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "..", "..", "config.txt")

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    for line in f:
                        # Expect lines like: login_key=YOUR_KEY_HERE
                        if line.startswith("login_key="):
                            value = line.split("=", 1)[1].strip()
                            self.login_key = value
                            break
            except Exception as e:
                self.log_status(f"Error reading config file: {e}")

    def create_widgets(self) -> None:
        """Create and arrange all GUI widgets."""
        # Create main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Input file selection
        input_box = wx.StaticBox(main_panel, label="Input File")
        input_sizer = wx.StaticBoxSizer(input_box, wx.HORIZONTAL)

        input_sizer.Add(wx.StaticText(main_panel, label="Selected File:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.input_file_ctrl = wx.TextCtrl(main_panel, value=self.input_file, size=(300, -1))
        input_sizer.Add(self.input_file_ctrl, 1, wx.ALL, 5)

        input_browse_btn = wx.Button(main_panel, label="Browse")
        input_browse_btn.Bind(wx.EVT_BUTTON, self.select_input_file)
        input_sizer.Add(input_browse_btn, 0, wx.ALL, 5)

        main_sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Output directory selection
        output_box = wx.StaticBox(main_panel, label="Output Directory")
        output_sizer = wx.StaticBoxSizer(output_box, wx.HORIZONTAL)

        output_sizer.Add(wx.StaticText(main_panel, label="Save to:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.output_dir_ctrl = wx.TextCtrl(main_panel, value=self.output_dir, size=(300, -1))
        output_sizer.Add(self.output_dir_ctrl, 1, wx.ALL, 5)

        output_browse_btn = wx.Button(main_panel, label="Browse")
        output_browse_btn.Bind(wx.EVT_BUTTON, self.select_output_dir)
        output_sizer.Add(output_browse_btn, 0, wx.ALL, 5)

        main_sizer.Add(output_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Settings frame
        settings_box = wx.StaticBox(main_panel, label="Settings")
        settings_sizer = wx.StaticBoxSizer(settings_box, wx.HORIZONTAL)

        settings_sizer.Add(wx.StaticText(main_panel, label="Start Index:"), 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.start_index_ctrl = wx.SpinCtrl(main_panel, value=str(self.start_index), min=1, max=9999)
        settings_sizer.Add(self.start_index_ctrl, 0, wx.ALL, 5)

        main_sizer.Add(settings_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Scraper settings frame
        scraper_box = wx.StaticBox(main_panel, label="Novelpia Scraper Settings")
        scraper_sizer = wx.StaticBoxSizer(scraper_box, wx.VERTICAL)

        scraper_sizer.Add(wx.StaticText(main_panel, label="Novel Number:"), 0, wx.ALL, 5)
        self.novel_no_ctrl = wx.TextCtrl(main_panel, value=self.novel_no)
        scraper_sizer.Add(self.novel_no_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        scraper_sizer.Add(wx.StaticText(main_panel, label="Login Key:"), 0, wx.ALL, 5)
        self.login_key_ctrl = wx.TextCtrl(main_panel, value=self.login_key, style=wx.TE_PASSWORD)
        scraper_sizer.Add(self.login_key_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        # Button to fetch chapter names
        fetch_btn = wx.Button(main_panel, label="Fetch Chapter Names")
        fetch_btn.Bind(wx.EVT_BUTTON, self.fetch_chapter_names)
        scraper_sizer.Add(fetch_btn, 0, wx.ALL, 5)

        main_sizer.Add(scraper_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Process button
        process_btn = wx.Button(main_panel, label="Process File")
        process_btn.Bind(wx.EVT_BUTTON, self.process_file)
        main_sizer.Add(process_btn, 0, wx.ALL, 10)

        # Status text box
        self.status_text = wx.TextCtrl(main_panel, style=wx.TE_MULTILINE | wx.TE_READONLY, size=(-1, 150))
        main_sizer.Add(self.status_text, 1, wx.EXPAND | wx.ALL, 10)

        # Set main panel sizer
        main_panel.SetSizer(main_sizer)

    def select_input_file(self, event) -> None:
        """Open file dialog to select input text file."""
        with wx.FileDialog(self, "Select Input File",
                          wildcard="Text files (*.txt)|*.txt|All files (*.*)|*.*") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                filename = dialog.GetPath()
                self.input_file = filename
                self.input_file_ctrl.SetValue(filename)

    def select_output_dir(self, event) -> None:
        """Open directory dialog to select output directory."""
        with wx.DirDialog(self, "Select Output Directory") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                dirname = dialog.GetPath()
                self.output_dir = dirname
                self.output_dir_ctrl.SetValue(dirname)

    def log_status(self, message: str) -> None:
        """
        Log a message to the status text box.

        Args:
            message: The message to log
        """
        self.status_text.AppendText(message + "\n")
        self.status_text.SetInsertionPointEnd()

    def fetch_chapter_names(self, event) -> None:
        """
        Fetches the chapter names from Novelpia using the user-provided
        novel number and the login key (already read from config, if found).
        """
        try:
            novel_no = self.novel_no_ctrl.GetValue().strip()
            login_key = self.login_key_ctrl.GetValue().strip()

            if not novel_no or not login_key:
                wx.MessageBox("Please enter both Novel Number and Login Key.", "Error", wx.OK | wx.ICON_ERROR)
                return

            self.chapter_names = []
            page = 0
            previous_chapters = None

            while True:
                self.log_status(f"Fetching page {page}...")
                chapters = self.fetch_chapters_page(novel_no, page, login_key)

                # If no new chapters or repeated set, break out.
                if not chapters or chapters == previous_chapters:
                    break

                previous_chapters = chapters
                self.chapter_names.extend(chapters)
                page += 1

            self.log_status(f"Successfully fetched {len(self.chapter_names)} chapter names.")
            wx.MessageBox(f"Fetched {len(self.chapter_names)} chapter names.", "Success", wx.OK | wx.ICON_INFORMATION)

        except Exception as e:
            self.log_status(f"Error fetching chapters: {str(e)}")
            wx.MessageBox(f"Failed to fetch chapters: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def fetch_chapters_page(self, novel_no: str, page: int, login_key: str) -> List[str]:
        """
        Helper to fetch one page of chapter listings from Novelpia.
        
        Args:
            novel_no: The novel number to fetch chapters for
            page: The page number to fetch
            login_key: The login key for authentication
            
        Returns:
            List of chapter names from the page
        """
        episode_list_url = "https://novelpia.com/proc/episode_list"
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        }
        data = {"novel_no": novel_no, "sort": "DOWN", "page": page}
        cookies = {"LOGINKEY": login_key}

        response = requests.post(episode_list_url, headers=headers, data=data, cookies=cookies)
        if response.status_code != 200:
            return []

        matches = re.findall(r'id="bookmark_(\d+)"></i>(.+?)</b>', response.text)
        return [match[1].strip() for match in matches]

    def process_file(self, event) -> None:
        """
        Processes the input file by splitting it at the exact lines
        that match the fetched chapter names.
        """
        input_file = self.input_file_ctrl.GetValue()
        output_dir = self.output_dir_ctrl.GetValue()

        if not input_file or not output_dir:
            self.log_status("Please select both input file and output directory.")
            return

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            with open(input_file, 'r', encoding='utf-8', errors='replace') as infile:
                lines = infile.readlines()

            file_index = self.start_index_ctrl.GetValue()
            section = []
            inside_section = False
            current_chapter_index = 0

            for line in lines:
                is_new_section = False

                # The only logic we keep: if the line matches chapter_names[current_chapter_index],
                # we start a new section.
                if self.chapter_names and current_chapter_index < len(self.chapter_names):
                    if line.strip() == self.chapter_names[current_chapter_index]:
                        is_new_section = True
                        current_chapter_index += 1

                if is_new_section:
                    # Write the previous section out
                    if inside_section:
                        output_filename = os.path.join(output_dir, f"{file_index}.txt")
                        with open(output_filename, 'w', encoding='utf-8') as outfile:
                            outfile.writelines(section)
                        self.log_status(f"Section written to {output_filename}")
                        file_index += 1
                        section = []

                    section.append(line)
                    inside_section = True
                else:
                    if inside_section:
                        section.append(line)

            # Write the last section (if it exists)
            if section:
                output_filename = os.path.join(output_dir, f"{file_index}.txt")
                with open(output_filename, 'w', encoding='utf-8') as outfile:
                    outfile.writelines(section)
                self.log_status(f"Section written to {output_filename}")

            self.log_status("Processing completed successfully!")

        except Exception as e:
            self.log_status(f"An error occurred: {e}")

def main() -> None:
    """Entry point for the application."""
    app = wx.App()
    frame = TextSplitterApp()
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()
