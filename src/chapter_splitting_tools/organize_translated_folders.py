import os
import shutil
from tkinter import filedialog

def move_translated_content(input_folder_name=None, log=print):
    # Set up correct paths based on script location
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

    input_root = os.path.join(PROJECT_ROOT, "input")
    output_root = os.path.join(PROJECT_ROOT, "output")

    # Step 0: Prompt for folder if none provided or default
    if not input_folder_name or input_folder_name.lower() == "input":
        selected = filedialog.askdirectory(title="Select Input Subfolder", initialdir=input_root)
        if not selected:
            log("[CANCELLED] No input folder selected.")
            return
        input_folder_name = os.path.basename(selected)

    input_subfolder = os.path.join(input_root, input_folder_name)
    unproofed_dir = os.path.join(output_root, "unproofed")
    proofed_dir = os.path.join(output_root, "proofed_ai")
    translated_dir = os.path.join(output_root, f"translated_{input_folder_name}")

    did_move_anything = False

    # Step 1: Move output/*.txt → output/unproofed/ (only if files exist)
    if os.path.exists(output_root):
        files_to_move = [
            f for f in os.listdir(output_root)
            if f.startswith("translated_") and f.endswith(".txt") and os.path.isfile(os.path.join(output_root, f))
        ]
        if files_to_move:
            os.makedirs(unproofed_dir, exist_ok=True)
            for fname in files_to_move:
                shutil.move(os.path.join(output_root, fname), os.path.join(unproofed_dir, fname))
                log(f"[MOVE] {fname} → unproofed/")
            did_move_anything = True
        else:
            log("[SKIP] No .txt files found to move into unproofed/.")
    else:
        log("[SKIP] output/ folder not found.")


    # Step 2: Move unproofed/ and proofed_ai/ into output/translated_[inputname]
    folders_to_move = [("unproofed", unproofed_dir), ("proofed_ai", proofed_dir)]
    for folder_name, folder_path in folders_to_move:
        if os.path.exists(folder_path):
            os.makedirs(translated_dir, exist_ok=True)
            dst = os.path.join(translated_dir, folder_name)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(folder_path, dst)
            log(f"[MOVE] {folder_name}/ → {translated_dir}")
            did_move_anything = True
        else:
            log(f"[SKIP] {folder_name}/ not found")

    # Step 3: Move files from input/ back into input_subfolder
    if os.path.exists(input_subfolder):
        for fname in os.listdir(input_root):
            src = os.path.join(input_root, fname)
            dst = os.path.join(input_subfolder, fname)
            if os.path.isfile(src):
                shutil.move(src, dst)
                log(f"[RESTORE] {fname} → {input_folder_name}/")
                did_move_anything = True

        # Step 4: Move images/ into input_subfolder
        images_path = os.path.join(input_root, "images")
        if os.path.exists(images_path):
            dst = os.path.join(input_subfolder, "images")
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.move(images_path, dst)
            log(f"[RESTORE] images/ → {input_folder_name}/images/")
            did_move_anything = True

        # Step 5: Rename folder unless already processed
        if not input_folder_name.startswith("processed_"):
            new_name = f"processed_{input_folder_name}"
            new_path = os.path.join(input_root, new_name)
            if os.path.exists(new_path):
                shutil.rmtree(new_path)
            os.rename(input_subfolder, new_path)
            log(f"[RENAME] {input_folder_name}/ → {new_name}/")
        else:
            log("[SKIP] Already processed. No rename.")
    else:
        log(f"[SKIP] Input subfolder not found: {input_subfolder}")

    if did_move_anything:
        log(f"[DONE] Organization complete for: {input_folder_name}")
    else:
        log("[SKIP] No content to organize. Nothing moved.")
