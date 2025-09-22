
import os
import shutil
import sys
import wx
import threading
import json
import time
from datetime import datetime

# Ensure src/ is in sys.path so imports work correctly if run from GUI
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chapter_splitting_tools.epub_separator import EPUBSeparator
from chapter_splitting_tools.novel_splitter import TextSplitterApp
from chapter_splitting_tools.output_combiner import OutputCombiner
from chapter_splitting_tools.folder_manager import FolderManager
from chapter_splitting_tools.epuboutputcreator import show_gui_epub_dialog
from translation.translationManager import main as translation_main

class TranslationApp(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Novel Translation Tool", size=(1200, 700))  # Increased height for better layout

        # Threading flags
        self.pause_event = threading.Event()
        self.pause_event.set()
        self.cancel_requested = False

        self.input_folder = None
        self.glossary_file = None

        # GUI state variables
        self.skip_to_proofing = False
        self.skip_to_translation = False
        self.language_var = "Japanese"
        self.current_run_button = None  # Track which run button is active
        self.is_running = False  # Track if any operation is running

        self._build_ui()
        self._create_default_folders()
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        self.cancel_requested = True
        self.pause_event.set()  # Resume anything paused
        self.log_message("[CONTROL] Shutting down.")
        self.Destroy()

    def _build_ui(self):
        # Create main panel
        main_panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)  # Changed to horizontal for sidebar layout

        # Create sidebar panel
        sidebar_panel = wx.Panel(main_panel)
        sidebar_panel.SetBackgroundColour(wx.Colour(240, 240, 240))  # Light gray background
        sidebar_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create content panel (for text area and bulk jobs)
        content_panel = wx.Panel(main_panel)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create text area with scrollbar
        self.text_area = wx.TextCtrl(content_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP)
        content_sizer.Add(self.text_area, 1, wx.EXPAND | wx.ALL, 10)

        # === SIDEBAR CONTENT ===

        # Title for sidebar
        sidebar_title = wx.StaticText(sidebar_panel, label="Translation Tools")
        sidebar_title.SetFont(wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sidebar_sizer.Add(sidebar_title, 0, wx.ALL | wx.ALIGN_CENTER, 5)

        # Add separator line
        line = wx.StaticLine(sidebar_panel)
        sidebar_sizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        # Main action buttons
        main_actions_label = wx.StaticText(sidebar_panel, label="Main Actions:")
        main_actions_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sidebar_sizer.Add(main_actions_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        run_btn = wx.Button(sidebar_panel, label="Run Translation", size=(170, 28))
        run_btn.Bind(wx.EVT_BUTTON, self.run_translation)
        sidebar_sizer.Add(run_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 3)

        # Control buttons
        controls_label = wx.StaticText(sidebar_panel, label="Controls:")
        controls_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sidebar_sizer.Add(controls_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        self.pause_button = wx.Button(sidebar_panel, label="Pause", size=(170, 24))
        self.pause_button.Bind(wx.EVT_BUTTON, self.toggle_pause)
        self.pause_button.Enable(False)  # Disabled until something is running
        sidebar_sizer.Add(self.pause_button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        self.stop_button = wx.Button(sidebar_panel, label="Stop", size=(170, 24))
        self.stop_button.Bind(wx.EVT_BUTTON, self.stop_translation)
        self.stop_button.Enable(False)  # Disabled until something is running
        sidebar_sizer.Add(self.stop_button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Text processing tools
        tools_label = wx.StaticText(sidebar_panel, label="Text Processing:")
        tools_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sidebar_sizer.Add(tools_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        split_btn = wx.Button(sidebar_panel, label="Split Chapters", size=(170, 24))
        split_btn.Bind(wx.EVT_BUTTON, self.show_splitter_dialog)
        sidebar_sizer.Add(split_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        combine_btn = wx.Button(sidebar_panel, label="Combine Output", size=(170, 24))
        combine_btn.Bind(wx.EVT_BUTTON, self.run_output_combiner)
        sidebar_sizer.Add(combine_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        epub_btn = wx.Button(sidebar_panel, label="Make EPUB", size=(170, 24))
        epub_btn.Bind(wx.EVT_BUTTON, self.run_epub_creator)
        sidebar_sizer.Add(epub_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Management tools
        mgmt_label = wx.StaticText(sidebar_panel, label="Management:")
        mgmt_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sidebar_sizer.Add(mgmt_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        organize_btn = wx.Button(sidebar_panel, label="Organize Folders", size=(170, 24))
        organize_btn.Bind(wx.EVT_BUTTON, self.organize_translated_folders)
        sidebar_sizer.Add(organize_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        clear_btn = wx.Button(sidebar_panel, label="Clear Folders", size=(170, 24))
        clear_btn.Bind(wx.EVT_BUTTON, self.clear_folders)
        sidebar_sizer.Add(clear_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        config_btn = wx.Button(sidebar_panel, label="Config", size=(170, 24))
        config_btn.Bind(wx.EVT_BUTTON, self.show_config_dialog)
        sidebar_sizer.Add(config_btn, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Settings section
        settings_label = wx.StaticText(sidebar_panel, label="Settings:")
        settings_label.SetFont(wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sidebar_sizer.Add(settings_label, 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)

        # Phase selection dropdown
        phase_label = wx.StaticText(sidebar_panel, label="Start From Phase:")
        phase_label.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sidebar_sizer.Add(phase_label, 0, wx.LEFT | wx.RIGHT, 3)

        self.phase_var = "Phase 1: Glossary"
        self.phase_choice = wx.Choice(sidebar_panel, choices=[
            "Phase 1: Glossary",
            "Phase 2: Translation",
            "Phase 3.1: Non-English Check",
            "Phase 3.2: Gender Proofing",
            "Phase 3.3: Final Proofing"
        ], size=(170, 22))
        self.phase_choice.SetSelection(0)
        sidebar_sizer.Add(self.phase_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Language selector
        lang_label = wx.StaticText(sidebar_panel, label="Source Language:")
        lang_label.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sidebar_sizer.Add(lang_label, 0, wx.LEFT | wx.RIGHT, 3)

        self.language_choice = wx.Choice(sidebar_panel, choices=["Japanese", "Chinese", "Korean"], size=(170, 22))
        self.language_choice.SetSelection(0)  # Default to Japanese
        sidebar_sizer.Add(self.language_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # AI Provider selector
        provider_label = wx.StaticText(sidebar_panel, label="AI Provider:")
        provider_label.SetFont(wx.Font(7, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sidebar_sizer.Add(provider_label, 0, wx.LEFT | wx.RIGHT, 3)

        self.provider_choice = wx.Choice(sidebar_panel, choices=["Auto (Fallback)", "Gemini", "OpenAI", "Anthropic"], size=(170, 22))
        self.provider_choice.SetSelection(0)  # Default to Auto
        sidebar_sizer.Add(self.provider_choice, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 2)

        # Add flexible space to push everything to top
        sidebar_sizer.AddStretchSpacer(1)

        # Set sidebar sizer
        sidebar_panel.SetSizer(sidebar_sizer)

        # === Bulk Translation Job Panel ===
        bulk_label = wx.StaticText(content_panel, label="Bulk Translation Jobs")
        bulk_label.SetFont(wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        content_sizer.Add(bulk_label, 0, wx.ALL, 10)

        # Create list control for jobs
        self.job_list = wx.ListCtrl(content_panel, style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        self.job_list.AppendColumn("Job", width=400)
        self.job_list.AppendColumn("Status", width=150)
        content_sizer.Add(self.job_list, 0, wx.EXPAND | wx.ALL, 10)

        bulk_btn = wx.Button(content_panel, label="Run Bulk Translation (Select Folders)")
        bulk_btn.Bind(wx.EVT_BUTTON, self.run_bulk_translation)
        content_sizer.Add(bulk_btn, 0, wx.ALL, 10)

        # Set content panel sizer
        content_panel.SetSizer(content_sizer)

        # Add panels to main sizer
        main_sizer.Add(sidebar_panel, 0, wx.EXPAND | wx.ALL, 5)  # Sidebar on left
        main_sizer.Add(content_panel, 1, wx.EXPAND | wx.ALL, 5)  # Content takes remaining space

        # Set main panel sizer
        main_panel.SetSizer(main_sizer)


    def _create_default_folders(self):
        for folder in ["input", "output", "translation", os.path.join("translation", "glossary")]:
            os.makedirs(folder, exist_ok=True)
            self.log_message(f"[INIT] Ensured folder exists: {folder}")

    def log_message(self, *args):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        message = f"{timestamp} " + " ".join(str(arg) for arg in args)

        try:
            self.text_area.AppendText(message + "\n")
            # Scroll to bottom
            self.text_area.SetInsertionPointEnd()
        except Exception:
            print("[LOG]", message)

    def run_translation(self, event):
        # Disable the run button during translation
        run_btn = event.GetEventObject()
        run_btn.Enable(False)

        # Store reference for pause/stop buttons
        self.current_run_button = run_btn
        self.is_running = True

        # Enable pause/stop buttons
        self.pause_button.Enable(True)
        self.stop_button.Enable(True)

        input_folder = self.select_input_folder()
        if not input_folder:
            self.log_message("No input folder selected. Aborting.")
            run_btn.Enable(True)
            return
        self._move_files_to_input(input_folder)

        glossary_file = self.select_glossary_file()
        self.glossary_file = glossary_file
        if not glossary_file:
            self.glossary_file = None  # Ensure it's recognized as "no glossary selected"

        selected_lang = self.language_choice.GetStringSelection()
        selected_provider = self.provider_choice.GetStringSelection()

        def worker():
            try:
                selected_phase = self.phase_choice.GetStringSelection()

                # Map dropdown selection to parameters
                skip_to_proofing = selected_phase.startswith("Phase 3")
                skip_to_translation = selected_phase.startswith("Phase 2") or skip_to_proofing

                # For sub-phases of proofing
                proofing_subphase = None
                if "3.1" in selected_phase:
                    proofing_subphase = "non_english"
                elif "3.2" in selected_phase:
                    proofing_subphase = "gender"
                elif "3.3" in selected_phase:
                    proofing_subphase = "final"

                translation_main(
                    log_message=self.log_message,
                    glossary_file=self.glossary_file or None,
                    proofing_only=skip_to_proofing,
                    skip_phase1=skip_to_translation,
                    proofing_subphase=proofing_subphase,
                    pause_event=self.pause_event,
                    cancel_flag=lambda: self.cancel_requested,
                    source_lang=selected_lang,
                    input_folder=self.input_folder,
                    preferred_provider=selected_provider if selected_provider != "Auto (Fallback)" else None
                )

                # Update reference to glossary file in case one was auto-created
                if not self.glossary_file and os.path.exists("input"):
                    input_name = os.path.basename(self.input_folder.rstrip("/\\"))
                    auto_gloss_path = os.path.join("translation", "glossary", f"{input_name}.txt")
                    if os.path.exists(auto_gloss_path):
                        self.glossary_file = auto_gloss_path
                        self.log_message(f"[INFO] Glossary file set to auto-created: {self.glossary_file}")

            except Exception as e:
                self.log_message("[ERROR]", e)
            finally:
                # Reset UI state
                self.pause_event.set()
                self.cancel_requested = False
                self.is_running = False
                wx.CallAfter(self.pause_button.SetLabel, "Pause")
                wx.CallAfter(self.pause_button.Enable, False)
                wx.CallAfter(self.stop_button.Enable, False)
                if self.current_run_button:
                    wx.CallAfter(self.current_run_button.Enable, True)
                self.current_run_button = None

        threading.Thread(target=worker, daemon=True).start()

    def select_input_folder(self):
        with wx.DirDialog(self, "Select Input Folder", defaultPath="input") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                folder = dialog.GetPath()
                self.input_folder = folder
                self.log_message(f"Selected input folder: {os.path.basename(folder)}")
                return folder
        return None

    def select_glossary_file(self):
        default_dir = os.path.join(os.path.dirname(__file__), "..", "translation")
        with wx.FileDialog(self, "Select Glossary", defaultDir=default_dir,
                          wildcard="Text files (*.txt)|*.txt") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                return dialog.GetPath()
        return None

    def _move_files_to_input(self, src):
        for filename in os.listdir(src):
            shutil.move(os.path.join(src, filename), os.path.join("input", filename))
            self.log_message(f"Moved {filename} to input folder")

    def show_splitter_dialog(self, event):
        choices = ["Novel Splitter", "EPUB Separator", "Bulk EPUB Separator"]
        with wx.SingleChoiceDialog(self, "Choose splitter type:", "Choose Splitter", choices) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                selection = dialog.GetSelection()
                if selection == 0:
                    self.run_novel_splitter()
                elif selection == 1:
                    self.run_epub_separator()
                elif selection == 2:
                    self.run_bulk_epub_separator()

    def run_novel_splitter(self):
        self.log_message("Starting Novel Splitter")
        # Create a new TextSplitterApp frame
        splitter_frame = TextSplitterApp(self)
        splitter_frame.Show()

    def run_epub_separator(self):
        with wx.FileDialog(self, "Select EPUB", wildcard="EPUB files (*.epub)|*.epub") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                epub_file = dialog.GetPath()
                epub_name = os.path.splitext(os.path.basename(epub_file))[0]
                input_subdir = os.path.join("input", epub_name)

                self.log_message(f"Running EPUB Separator for {epub_name}")
                separator = EPUBSeparator(self.log_message)
                separator.separate(epub_file, input_subdir)

    def run_output_combiner(self, event):
        with wx.DirDialog(self, "Select Output Folder", defaultPath="output") as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                folder = dialog.GetPath()
                combiner = OutputCombiner(self.log_message)
                combiner.show_save_dialog(folder)

    def run_epub_creator(self, event):
        """Launch the EPUB creation dialog."""
        try:
            show_gui_epub_dialog()
        except Exception as e:
            self.log_message(f"[ERROR] Failed to create EPUB: {e}")
            wx.MessageBox(f"Failed to create EPUB: {str(e)}", "Error", wx.OK | wx.ICON_ERROR)

    def clear_folders(self, event):
        manager = FolderManager(self.log_message)
        manager.show_clear_dialog()

    def toggle_pause(self, event):
        if not self.is_running:
            self.log_message("[CONTROL] No operation is currently running.")
            return

        if self.pause_event.is_set():
            self.pause_event.clear()
            self.pause_button.SetLabel("Resume")
            self.log_message("[CONTROL] Paused")
        else:
            self.pause_event.set()
            self.pause_button.SetLabel("Pause")
            self.log_message("[CONTROL] Resumed")

    def stop_translation(self, event):
        if not self.is_running:
            self.log_message("[CONTROL] No operation is currently running.")
            return

        self.cancel_requested = True
        self.pause_event.set()  # Resume if paused so it can process the cancel
        self.log_message("[CONTROL] Stop requested. Will stop after current chapter.")

        # Reset UI after a short delay to ensure the worker thread has time to respond
        wx.CallLater(2000, self.reset_ui_after_cancel)

    def reset_ui_after_cancel(self):
        # Reset UI state regardless of worker thread status
        self.cancel_requested = False
        self.is_running = False
        self.pause_button.SetLabel("Pause")
        self.pause_button.Enable(False)
        self.stop_button.Enable(False)
        if self.current_run_button:
            self.current_run_button.Enable(True)
        self.current_run_button = None
        self.log_message("[CONTROL] Translation stopped. UI reset.")

    def organize_translated_folders(self, event):
        # Prompt if no input folder or if "input" base folder is selected
        if not self.input_folder or os.path.basename(self.input_folder.rstrip("/\\")) == "input":
            with wx.DirDialog(self, "Select Specific Input Subfolder", defaultPath="input") as dialog:
                if dialog.ShowModal() == wx.ID_OK:
                    selected_folder = dialog.GetPath()
                    self.input_folder = selected_folder
                    self.log_message(f"[SELECTED] Input folder set to: {os.path.basename(selected_folder)}")
                else:
                    self.log_message("[CANCELLED] No valid input folder selected.")
                    return

        input_name = os.path.basename(self.input_folder.rstrip("/\\"))
        try:
            from chapter_splitting_tools.organize_translated_folders import move_translated_content
            move_translated_content(input_name, log=self.log_message)
        except Exception as e:
            self.log_message(f"[ERROR] Failed to run folder organizer: {e}")

    def run_bulk_epub_separator(self):
        separator = EPUBSeparator(self.log_message)
        separator.bulk_split_with_dialog(base_output_dir="input")


    def run_bulk_translation(self, event):
        # Check if already running
        if self.is_running:
            self.log_message("[CONTROL] Another operation is already running.")
            return

        # Check if input folder exists
        input_dir = "input"
        if not os.path.exists(input_dir):
            wx.MessageBox("Input folder does not exist!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # Set running state
        self.is_running = True
        bulk_btn = event.GetEventObject()
        bulk_btn.Enable(False)
        self.current_run_button = bulk_btn

        # Enable pause/stop buttons
        self.pause_button.Enable(True)
        self.stop_button.Enable(True)

        # Get all subfolders in input directory that contain .txt files
        all_subdirs = [d for d in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, d))]
        subdirs = []

        for subdir in all_subdirs:
            # Skip folders that start with "processed_" as they've already been translated
            if subdir.startswith("processed_"):
                self.log_message(f"[DEBUG] Skipping already processed folder: {subdir}")
                continue

            subdir_path = os.path.join(input_dir, subdir)
            try:
                # Check if folder contains any .txt files
                txt_files = [f for f in os.listdir(subdir_path) if f.endswith('.txt')]
                if txt_files:
                    subdirs.append(subdir)
                    self.log_message(f"[DEBUG] Found translatable folder: {subdir} ({len(txt_files)} .txt files)")
            except Exception as e:
                self.log_message(f"[DEBUG] Error checking folder {subdir}: {e}")

        if not subdirs:
            wx.MessageBox("No subfolders with .txt files found in input directory!", "Error", wx.OK | wx.ICON_ERROR)
            return

        # First, let user select the source language
        languages = ["Japanese", "Chinese", "Korean", "Other"]
        with wx.SingleChoiceDialog(self, "Select source language:", "Language Selection", languages) as lang_dialog:
            if lang_dialog.ShowModal() != wx.ID_OK:
                self.log_message("[CANCELLED] No language selected.")
                return
            selected_lang = lang_dialog.GetStringSelection()

        # Show dialog to choose between all folders or select specific ones
        choices = ["Translate all folders", "Select specific folders"]
        with wx.SingleChoiceDialog(self, "Choose translation method:", "Bulk Translation Setup", choices) as choice_dialog:
            if choice_dialog.ShowModal() != wx.ID_OK:
                self.log_message("[CANCELLED] No selection method chosen.")
                return
            selection_method = choice_dialog.GetSelection()

        selected_folders = []

        if selection_method == 0:
            # Translate all folders
            for sub in subdirs:
                path = os.path.join(input_dir, sub)
                selected_folders.append((sub, path))
            self.log_message(f"[INFO] Selected all {len(selected_folders)} folders for translation.")

        else:
            # Let user select specific folders from input directory
            with wx.MultiChoiceDialog(self, "Select folders to translate:", "Choose Input Folders", subdirs) as dialog:
                if dialog.ShowModal() != wx.ID_OK:
                    self.log_message("[CANCELLED] No folders selected.")
                    return

                selections = dialog.GetSelections()
                if not selections:
                    self.log_message("[CANCELLED] No folders selected.")
                    return

                for i in selections:
                    folder_name = subdirs[i]
                    path = os.path.join(input_dir, folder_name)
                    selected_folders.append((folder_name, path))

                self.log_message(f"[INFO] Selected {len(selected_folders)} folders for translation: {', '.join([name for name, _ in selected_folders])}")

        # Clear job list
        self.job_list.DeleteAllItems()

        # Enqueue jobs
        jobs = []
        for i, (name, path) in enumerate(selected_folders):
            jobs.append((name, path))
            index = self.job_list.InsertItem(i, name)
            self.job_list.SetItem(index, 1, "Pending")

        def worker():
            skip_remaining_glossary = False

            for i, (name, folder_path) in enumerate(jobs):
                # Check if cancel was requested before starting a new job
                if self.cancel_requested:
                    self.log_message("[CONTROL] Bulk translation cancelled.")
                    break

                # Update job status in list
                wx.CallAfter(self.job_list.SetItem, i, 1, "Glossary Selection")
                self.input_folder = folder_path  # needed for organizing later

                # Check for pause before file operations
                if not self.pause_event.is_set():
                    self.log_message("[CONTROL] Paused before processing folder: " + name)
                    self.pause_event.wait()
                    if self.cancel_requested:
                        self.log_message("[CONTROL] Cancelled after pause.")
                        break

                # Handle glossary selection for this folder
                current_glossary = None
                if not skip_remaining_glossary:
                    # Use a threading event to get the dialog result
                    dialog_result = threading.Event()
                    glossary_choice = [None]  # Use list to allow modification from callback

                    def show_dialog():
                        choice = self.show_bulk_glossary_dialog(name, i + 1, len(jobs))
                        glossary_choice[0] = choice
                        dialog_result.set()

                    wx.CallAfter(show_dialog)

                    # Wait for dialog result
                    dialog_result.wait()

                    if self.cancel_requested:
                        break

                    choice = glossary_choice[0]
                    if choice == "skip_folder":
                        wx.CallAfter(self.job_list.SetItem, i, 1, "Skipped")
                        self.log_message(f"[SKIP] Skipped folder: {name}")
                        continue
                    elif choice == "skip_remaining":
                        skip_remaining_glossary = True
                        current_glossary = None  # Use auto-creation for remaining
                    else:
                        current_glossary = choice  # Could be a file path or None

                wx.CallAfter(self.job_list.SetItem, i, 1, "Moving Files")

                # Clear the main input directory first (but preserve subfolders)
                self.log_message(f"[SETUP] Clearing main input directory for: {name}")
                for item in os.listdir("input"):
                    item_path = os.path.join("input", item)
                    if os.path.isfile(item_path) and item.endswith('.txt'):
                        os.remove(item_path)
                        self.log_message(f"[SETUP] Removed: {item}")

                # Move files from subfolder to main input directory
                self.log_message(f"[SETUP] Moving files from {folder_path} to main input directory")
                self._move_files_to_input(folder_path)

                # Update status to translating
                wx.CallAfter(self.job_list.SetItem, i, 1, "Translating")

                try:
                    # Check for pause/cancel again before starting translation
                    if self.cancel_requested:
                        self.log_message("[CONTROL] Cancelled before translation.")
                        break
                        
                    if not self.pause_event.is_set():
                        self.log_message("[CONTROL] Paused before translation.")
                        self.pause_event.wait()
                        if self.cancel_requested:
                            self.log_message("[CONTROL] Cancelled after pause.")
                            break
                    
                    # Run translation with pause_event and cancel_flag on main input directory
                    translation_main(
                        log_message=self.log_message,
                        glossary_file=current_glossary,  # Use selected glossary or None for auto-creation
                        proofing_only=False,
                        skip_phase1=False,
                        proofing_subphase=None,
                        pause_event=self.pause_event,
                        cancel_flag=lambda: self.cancel_requested,
                        source_lang=selected_lang,
                        input_folder=folder_path,  # Use the actual folder path for proper glossary naming
                        preferred_provider=None  # Use default provider for bulk operations
                    )
                    
                    # Check if cancelled after translation
                    if self.cancel_requested:
                        self.log_message("[CONTROL] Cancelled after translation.")
                        break
                        
                    wx.CallAfter(self.job_list.SetItem, i, 1, "Organizing")

                    # Check for pause before organizing
                    if not self.pause_event.is_set():
                        self.log_message("[CONTROL] Paused before organizing.")
                        self.pause_event.wait()
                        if self.cancel_requested:
                            self.log_message("[CONTROL] Cancelled after pause.")
                            break

                    from chapter_splitting_tools.organize_translated_folders import move_translated_content
                    move_translated_content(name, log=self.log_message)
                    wx.CallAfter(self.job_list.SetItem, i, 1, "Done")
                except Exception as e:
                    self.log_message(f"[ERROR] Failed to translate {name}: {e}")
                    wx.CallAfter(self.job_list.SetItem, i, 1, "Error")
                    
            # After all jobs or after cancellation, reset UI
            was_cancelled = self.cancel_requested
            self.is_running = False
            self.cancel_requested = False
            wx.CallAfter(self.pause_button.SetLabel, "Pause")
            wx.CallAfter(self.pause_button.Enable, False)
            wx.CallAfter(self.stop_button.Enable, False)
            if self.current_run_button:
                wx.CallAfter(self.current_run_button.Enable, True)
            self.current_run_button = None

            if was_cancelled:
                self.log_message("[CONTROL] Bulk translation cancelled.")
            else:
                self.log_message("[CONTROL] Bulk translation completed.")

        # Start worker thread
        threading.Thread(target=worker, daemon=True).start()

    def show_bulk_glossary_dialog(self, folder_name: str, current_index: int, total_folders: int):
        """Show glossary selection dialog for bulk translation."""
        dialog_title = f"Glossary Selection - Folder {current_index}/{total_folders}: {folder_name}"

        choices = [
            "Create new glossary (auto-generate)",
            "Select existing glossary file",
            "Skip this folder",
            "Skip remaining folders (auto-generate for all)"
        ]

        message = f"""Choose glossary option for folder: {folder_name}

• Create new glossary: Will auto-generate a glossary for this folder
• Select existing: Choose an existing glossary file to use
• Skip this folder: Skip translation for this folder only
• Skip remaining: Use auto-generation for this and all remaining folders"""

        with wx.SingleChoiceDialog(self, message, dialog_title, choices) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                selection = dialog.GetSelection()

                if selection == 0:  # Create new glossary
                    return None  # None triggers auto-creation
                elif selection == 1:  # Select existing glossary
                    return self.select_glossary_file()  # Returns file path or None
                elif selection == 2:  # Skip this folder
                    return "skip_folder"
                elif selection == 3:  # Skip remaining folders
                    return "skip_remaining"
            else:
                # User cancelled - treat as skip this folder
                return "skip_folder"

    def show_config_dialog(self, event):
        """Show configuration dialog for updating AI service settings."""
        try:
            from gui.multi_provider_config_dialog import MultiProviderConfigDialog
            dialog = MultiProviderConfigDialog(self)
            if dialog.ShowModal() == wx.ID_OK:
                # Configuration was saved, reinitialize providers
                try:
                    from ai_providers.provider_manager import provider_manager
                    provider_manager.reinitialize_all_providers()
                    self.log_message("[CONFIG] Configuration updated and providers reinitialized successfully.")

                    # Show provider status
                    status = provider_manager.get_provider_status()
                    for provider_name, info in status.items():
                        if info["enabled"]:
                            status_msg = "✓" if info["available"] else "✗"
                            self.log_message(f"[CONFIG] {provider_name}: {status_msg} ({info['model']})")

                except Exception as e:
                    self.log_message(f"[CONFIG] Error reinitializing providers: {e}")
                    wx.MessageBox(f"Configuration saved but failed to reinitialize providers:\n{e}",
                                 "Configuration Warning", wx.OK | wx.ICON_WARNING)
            dialog.Destroy()
        except ImportError:
            # Fall back to legacy config dialog
            dialog = ConfigDialog(self)
            if dialog.ShowModal() == wx.ID_OK:
                try:
                    from config.config import initialize_vertexai
                    initialize_vertexai()
                    self.log_message("[CONFIG] Configuration updated and VertexAI reinitialized successfully.")
                except Exception as e:
                    self.log_message(f"[CONFIG] Error reinitializing VertexAI: {e}")
                    wx.MessageBox(f"Configuration saved but failed to reinitialize VertexAI:\n{e}",
                                 "Configuration Warning", wx.OK | wx.ICON_WARNING)
            dialog.Destroy()


class ConfigDialog(wx.Dialog):
    """Configuration dialog for AI service settings."""

    def __init__(self, parent):
        super().__init__(parent, title="Configuration Settings", size=(500, 400))

        # Load current configuration
        self.config_file = os.path.join("src", "config", "config.txt")
        self.service_account_file = os.path.join("src", "config", "service_account.json")
        self.current_config = self.load_current_config()

        self.create_ui()
        self.load_values()

    def load_current_config(self):
        """Load current configuration from config.txt"""
        config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            config[key.strip()] = value.strip()
            except Exception as e:
                wx.MessageBox(f"Error reading config file: {e}", "Error", wx.OK | wx.ICON_ERROR)
        return config

    def create_ui(self):
        """Create the user interface."""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Title
        title = wx.StaticText(panel, label="Google Cloud AI Configuration")
        title_font = title.GetFont()
        title_font.SetPointSize(12)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)

        # Configuration fields
        form_sizer = wx.FlexGridSizer(4, 2, 10, 10)
        form_sizer.AddGrowableCol(1)

        # Project ID
        form_sizer.Add(wx.StaticText(panel, label="Project ID:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.project_id_ctrl = wx.TextCtrl(panel, size=(300, -1))
        form_sizer.Add(self.project_id_ctrl, 1, wx.EXPAND)

        # Location
        form_sizer.Add(wx.StaticText(panel, label="Location:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.location_ctrl = wx.TextCtrl(panel, size=(300, -1))
        form_sizer.Add(self.location_ctrl, 1, wx.EXPAND)

        # Login Key
        form_sizer.Add(wx.StaticText(panel, label="Login Key:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.login_key_ctrl = wx.TextCtrl(panel, size=(300, -1), style=wx.TE_PASSWORD)
        form_sizer.Add(self.login_key_ctrl, 1, wx.EXPAND)

        # Service Account File
        form_sizer.Add(wx.StaticText(panel, label="Service Account:"), 0, wx.ALIGN_CENTER_VERTICAL)
        sa_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.service_account_label = wx.StaticText(panel, label="No file selected")
        sa_sizer.Add(self.service_account_label, 1, wx.ALIGN_CENTER_VERTICAL)
        self.browse_btn = wx.Button(panel, label="Browse...")
        self.browse_btn.Bind(wx.EVT_BUTTON, self.on_browse_service_account)
        sa_sizer.Add(self.browse_btn, 0, wx.LEFT, 5)
        form_sizer.Add(sa_sizer, 1, wx.EXPAND)

        main_sizer.Add(form_sizer, 1, wx.ALL | wx.EXPAND, 20)

        # Help text
        help_text = wx.StaticText(panel, label=
            "• Project ID: Your Google Cloud project ID\n"
            "• Location: Google Cloud region (e.g., us-central1)\n"
            "• Login Key: API authentication key (optional)\n"
            "• Service Account: JSON file with service account credentials")
        help_text.SetForegroundColour(wx.Colour(100, 100, 100))
        main_sizer.Add(help_text, 0, wx.ALL | wx.EXPAND, 10)

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()

        save_btn = wx.Button(panel, wx.ID_OK, "Save")
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)
        btn_sizer.AddButton(save_btn)

        cancel_btn = wx.Button(panel, wx.ID_CANCEL, "Cancel")
        btn_sizer.AddButton(cancel_btn)

        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALL | wx.CENTER, 10)

        panel.SetSizer(main_sizer)

    def load_values(self):
        """Load current values into the form."""
        self.project_id_ctrl.SetValue(self.current_config.get("PROJECT_ID", ""))
        self.location_ctrl.SetValue(self.current_config.get("LOCATION", "us-central1"))
        self.login_key_ctrl.SetValue(self.current_config.get("LOGIN_KEY", ""))

        # Check if service account file exists
        if os.path.exists(self.service_account_file):
            try:
                with open(self.service_account_file, "r", encoding="utf-8") as f:
                    sa_data = json.load(f)
                    project_id = sa_data.get("project_id", "Unknown")
                    client_email = sa_data.get("client_email", "Unknown")
                    self.service_account_label.SetLabel(f"Current: {project_id} ({client_email})")
            except Exception:
                self.service_account_label.SetLabel("Current: service_account.json (invalid)")
        else:
            self.service_account_label.SetLabel("No service account file found")

    def on_browse_service_account(self, event):
        """Browse for service account JSON file."""
        with wx.FileDialog(self, "Select Service Account JSON File",
                          wildcard="JSON files (*.json)|*.json",
                          style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_OK:
                path = dialog.GetPath()
                try:
                    # Validate the JSON file
                    with open(path, "r", encoding="utf-8") as f:
                        sa_data = json.load(f)

                    # Check if it looks like a service account file
                    if "type" not in sa_data or sa_data["type"] != "service_account":
                        wx.MessageBox("This doesn't appear to be a valid service account JSON file.",
                                    "Invalid File", wx.OK | wx.ICON_ERROR)
                        return

                    # Store the path for later use
                    self.temp_service_account_path = path

                    # Update the label
                    project_id = sa_data.get("project_id", "Unknown")
                    client_email = sa_data.get("client_email", "Unknown")
                    self.service_account_label.SetLabel(f"Selected: {project_id} ({client_email})")

                    # Auto-fill project ID if empty
                    if not self.project_id_ctrl.GetValue() and project_id != "Unknown":
                        self.project_id_ctrl.SetValue(project_id)

                except Exception as e:
                    wx.MessageBox(f"Error reading service account file: {e}",
                                "Error", wx.OK | wx.ICON_ERROR)

    def on_save(self, event):
        """Save the configuration."""
        # Validate required fields
        project_id = self.project_id_ctrl.GetValue().strip()
        location = self.location_ctrl.GetValue().strip()

        if not project_id:
            wx.MessageBox("Project ID is required.", "Validation Error", wx.OK | wx.ICON_ERROR)
            return

        if not location:
            wx.MessageBox("Location is required.", "Validation Error", wx.OK | wx.ICON_ERROR)
            return

        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # Save config.txt
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(f"PROJECT_ID={project_id}\n")
                f.write(f"LOCATION={location}\n")
                login_key = self.login_key_ctrl.GetValue().strip()
                if login_key:
                    f.write(f"LOGIN_KEY={login_key}\n")

            # Copy service account file if a new one was selected
            if hasattr(self, 'temp_service_account_path'):
                shutil.copy2(self.temp_service_account_path, self.service_account_file)

            wx.MessageBox("Configuration saved successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
            self.EndModal(wx.ID_OK)

        except Exception as e:
            wx.MessageBox(f"Error saving configuration: {e}", "Error", wx.OK | wx.ICON_ERROR)
