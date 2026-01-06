"""
Utility functions for safe file and folder operations on Windows.

This module provides robust file operations that handle common Windows issues
like permission errors, file locks, and OneDrive sync conflicts.
"""

import os
import shutil
import time
import gc
from typing import Callable, Optional


def safe_rename_folder(old_path: str, new_path: str, log: Callable = print, max_retries: int = 5) -> bool:
    """
    Safely rename a folder with retry logic for Windows issues.
    
    This function handles common Windows file system issues:
    - Permission errors (antivirus, file explorer locks)
    - OneDrive sync conflicts
    - Temporary file locks
    - Long path names
    
    Args:
        old_path: Source folder path
        new_path: Destination folder path  
        log: Logging function (default: print)
        max_retries: Maximum number of retry attempts (default: 5)
        
    Returns:
        bool: True if successful, False if failed after all retries
    """
    if not os.path.exists(old_path):
        log(f"[RENAME] Source folder does not exist: {old_path}")
        return False
    
    for attempt in range(max_retries):
        try:
            # Force garbage collection to close any file handles
            gc.collect()
            
            # If destination exists, remove it first
            if os.path.exists(new_path):
                log(f"[RENAME] Removing existing destination: {new_path}")
                shutil.rmtree(new_path)
                time.sleep(0.5)  # Give Windows time to release handles
            
            # Attempt the rename
            os.rename(old_path, new_path)
            log(f"[RENAME] Successfully renamed: {os.path.basename(old_path)} → {os.path.basename(new_path)}")
            return True
            
        except PermissionError as e:
            log(f"[RENAME] Attempt {attempt + 1}/{max_retries} failed - Permission denied: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2, 4, 6, 8 seconds
                log(f"[RENAME] Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                log(f"[RENAME] FAILED after {max_retries} attempts. Folder may be in use by another process.")
                log(f"[RENAME] Common causes: File Explorer open, antivirus scanning, OneDrive syncing")
                log(f"[RENAME] You can manually rename '{os.path.basename(old_path)}' to '{os.path.basename(new_path)}' later.")
                return False
                
        except OSError as e:
            log(f"[RENAME] Attempt {attempt + 1}/{max_retries} failed - OS Error: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                log(f"[RENAME] Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                log(f"[RENAME] FAILED after {max_retries} attempts due to OS error.")
                return False
                
        except Exception as e:
            log(f"[RENAME] Unexpected error: {e}")
            return False
    
    return False


def safe_move_folder(src_path: str, dst_path: str, log: Callable = print, max_retries: int = 3) -> bool:
    """
    Safely move a folder with retry logic for Windows issues.
    
    Args:
        src_path: Source folder path
        dst_path: Destination folder path
        log: Logging function (default: print)
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        bool: True if successful, False if failed after all retries
    """
    if not os.path.exists(src_path):
        log(f"[MOVE] Source folder does not exist: {src_path}")
        return False
    
    for attempt in range(max_retries):
        try:
            # Force garbage collection to close any file handles
            gc.collect()
            
            # If destination exists, remove it first
            if os.path.exists(dst_path):
                log(f"[MOVE] Removing existing destination: {dst_path}")
                shutil.rmtree(dst_path)
                time.sleep(0.5)
            
            # Attempt the move
            shutil.move(src_path, dst_path)
            log(f"[MOVE] Successfully moved: {os.path.basename(src_path)} → {dst_path}")
            return True
            
        except (PermissionError, OSError) as e:
            log(f"[MOVE] Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                log(f"[MOVE] Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                log(f"[MOVE] FAILED after {max_retries} attempts.")
                return False
                
        except Exception as e:
            log(f"[MOVE] Unexpected error: {e}")
            return False
    
    return False


def ensure_folder_writable(folder_path: str, log: Callable = print) -> bool:
    """
    Ensure a folder is writable by attempting to create a test file.
    
    Args:
        folder_path: Path to the folder to test
        log: Logging function (default: print)
        
    Returns:
        bool: True if folder is writable, False otherwise
    """
    if not os.path.exists(folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            log(f"[WRITE_TEST] Cannot create folder {folder_path}: {e}")
            return False
    
    test_file = os.path.join(folder_path, ".write_test")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except Exception as e:
        log(f"[WRITE_TEST] Folder not writable {folder_path}: {e}")
        return False
