"""
Utility functions shared across the proofing pipeline.
"""

import os
import re
import time
import unicodedata
import threading
from typing import List

def split_into_sentences(text: str) -> List[str]:
    """Basic sentence splitter using punctuation."""
    return re.split(r'(?<=[.!?])\s+', text)

def contains_non_english_letters(text: str) -> bool:
    """
    Return True if 'text' contains any letters that are not LATIN.
    Ignores common Asian symbols and full-width punctuation.
    """
    ignore_chars = set("「」『』【】（）〈〉《》・ー〜～！？、。．，：；“”‘’・…—–‐≪≫〈〉『』【】〔〕（）［］｛｝｢｣ ㄴ ㅡ ㅋ ㅣ")
    for char in text:
        if char in ignore_chars:
            continue
        if char.isalpha():
            name = unicodedata.name(char, "")
            if "LATIN" not in name:
                return True
    return False

def inject_context(input_text: str, context_dict: dict) -> str:
    """
    Inject context as a header for use in debugging or AI prompting.
    """
    injected_lines = [f"{name} is {desc}." for name, desc in context_dict.items()]
    context_header = "Context: " + " ".join(injected_lines)
    return f"{context_header}\n\n{input_text}"

def split_text_into_chunks(text: str, max_bytes: int = 10240) -> List[str]:
    """
    Splits text into chunks of approximately max_bytes size without breaking lines.
    """
    lines = text.splitlines(keepends=True)
    chunks = []
    current_chunk = ''
    current_size = 0

    for line in lines:
        line_size = len(line.encode('utf-8'))
        if current_size + line_size > max_bytes and current_chunk:
            chunks.append(current_chunk)
            current_chunk = ''
            current_size = 0
        current_chunk += line
        current_size += line_size

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def call_with_timeout(func, args=(), kwargs=None, timeout=120, cancel_flag=None):
    """
    Runs a function with timeout and optional cancellation check.
    Returns (success, result or exception).
    """
    if kwargs is None:
        kwargs = {}

    result_container = {}

    def wrapper():
        try:
            result_container["result"] = func(*args, **kwargs)
        except Exception as e:
            result_container["exception"] = e

    thread = threading.Thread(target=wrapper, daemon=True)  # Make daemon to prevent hanging
    thread.start()

    # If we have a cancel flag, check it periodically
    if cancel_flag:
        elapsed = 0
        check_interval = 1  # Check every second

        while elapsed < timeout and thread.is_alive():
            if cancel_flag():
                # Don't wait for thread, just return cancellation
                return False, Exception("Operation cancelled by user")

            thread.join(check_interval)
            elapsed += check_interval
    else:
        # Original behavior - just wait for timeout
        thread.join(timeout)

    if thread.is_alive():
        # Thread will be cleaned up automatically as daemon
        return False, TimeoutError(f"Function call exceeded {timeout} seconds.")
    if "exception" in result_container:
        return False, result_container["exception"]
    return True, result_container["result"]


def cancellable_sleep(duration, cancel_flag=None, check_interval=0.5):
    """
    Sleep for the specified duration, but check for cancellation periodically.
    Returns True if sleep completed, False if cancelled.
    """
    if not cancel_flag:
        time.sleep(duration)
        return True

    elapsed = 0
    while elapsed < duration:
        if cancel_flag():
            return False

        sleep_time = min(check_interval, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time

    return True


def call_with_cancellation(func, args=(), kwargs=None, timeout=120, cancel_flag=None):
    """
    Runs a function with timeout and true VertexAI operation cancellation support.
    Attempts to cancel the actual server-side operation when cancel_flag is set.
    Returns (success, result or exception).
    """
    if kwargs is None:
        kwargs = {}

    result_container = {}
    operation_container = {}
    thread_finished = threading.Event()

    def wrapper():
        try:
            # Call the function and capture the result
            result = func(*args, **kwargs)
            result_container["result"] = result

            # Store operation reference for potential cancellation
            # VertexAI operations may have different ways to access the operation
            if hasattr(result, '_operation'):
                operation_container["operation"] = result._operation
            elif hasattr(result, 'operation'):
                operation_container["operation"] = result.operation
            elif hasattr(result, '_request_id'):
                operation_container["request_id"] = result._request_id

        except Exception as e:
            result_container["exception"] = e
        finally:
            thread_finished.set()

    # Use daemon thread to prevent hanging on app exit
    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()

    # Check for cancellation periodically while waiting
    elapsed = 0
    check_interval = 0.5  # Check every 500ms for more responsive cancellation

    while elapsed < timeout and not thread_finished.is_set():
        if cancel_flag and cancel_flag():
            # Attempt to cancel the server-side operation
            cancelled = False

            if "operation" in operation_container:
                try:
                    operation = operation_container["operation"]
                    if hasattr(operation, 'cancel'):
                        operation.cancel()
                        cancelled = True
                        print(f"[CANCEL] Successfully cancelled VertexAI operation")
                except Exception as cancel_error:
                    print(f"[CANCEL] Failed to cancel operation: {cancel_error}")

            # Wait a short time for the operation to actually cancel
            if cancelled:
                thread_finished.wait(timeout=2)

            return False, Exception("Operation cancelled by user")

        # Wait for thread or timeout
        thread_finished.wait(timeout=check_interval)
        elapsed += check_interval

    # Handle timeout case
    if not thread_finished.is_set():
        # Try to cancel operation on timeout as well
        if "operation" in operation_container:
            try:
                operation = operation_container["operation"]
                if hasattr(operation, 'cancel'):
                    operation.cancel()
                    print(f"[TIMEOUT] Cancelled operation due to timeout")
            except Exception:
                pass

        return False, TimeoutError(f"Function call exceeded {timeout} seconds.")

    # Return the result
    if "exception" in result_container:
        return False, result_container["exception"]
    return True, result_container["result"]


def is_image_only_chapter(content: str) -> bool:
    """
    Determines if a chapter contains only image-related markup (e.g., <image> tags and <<<IMAGE>>> blocks).
    Returns True if no meaningful text remains after ignoring image structures.
    """
    # Check if content is empty after stripping
    stripped = content.strip()
    if not stripped:
        return False

    # Remove <<<IMAGE_START>>>...<<<IMAGE_END>>> blocks
    content_no_image_blocks = re.sub(r'<<<IMAGE_START>>>.*?<<<IMAGE_END>>>', '', stripped, flags=re.DOTALL)

    # Remove <image ... /> tags (double/single quotes, extra spacing, optional closing slash)
    content_no_images = re.sub(
        r'<image\s+[^>]*src\s*=\s*["\'][^"\']+["\'][^>]*\/?>',
        '',
        content_no_image_blocks,
        flags=re.IGNORECASE
    )

    # Final check: is there any non-image content left?
    return not content_no_images.strip()

def extract_image_blocks(text: str) -> List[str]:
    """Extract all <<<IMAGE_START>>>...<<<IMAGE_END>>> image blocks from the text."""
    return re.findall(r'<<<IMAGE_START>>>.*?<<<IMAGE_END>>>', text, flags=re.DOTALL)

def find_missing_image_blocks(input_text: str, output_text: str) -> List[str]:
    """Return a list of image blocks that are in the input but missing from the output."""
    input_blocks = extract_image_blocks(input_text)
    output_blocks = extract_image_blocks(output_text)
    return [block for block in input_blocks if block not in output_blocks]

def insert_missing_image_blocks(input_text: str, output_text: str) -> str:
    """
    Reinsert missing image blocks from input into output in approximate positions.
    If location can't be determined, they are appended at the end.
    """
    missing_blocks = find_missing_image_blocks(input_text, output_text)
    if not missing_blocks:
        return output_text

    # Build line-wise maps to guess placement
    input_lines = input_text.splitlines()
    output_lines = output_text.splitlines()
    patched_lines = output_lines[:]
    
    for block in missing_blocks:
        # Try to locate the original line in input
        for i, line in enumerate(input_lines):
            if block in line:
                # Try to find a nearby similar line in output
                context_line = input_lines[i - 1] if i > 0 else ""
                insert_index = next((j for j, l in enumerate(output_lines) if context_line.strip() and context_line.strip() in l), None)
                if insert_index is not None:
                    patched_lines.insert(insert_index + 1, block)
                else:
                    patched_lines.append(block)
                break
        else:
            patched_lines.append(block)

    return "\n".join(patched_lines)

def patch_image_blocks_if_missing(fname: str, input_text: str, output_text: str, log_message=print) -> str:
    if "- image" not in fname:
        return output_text

    has_input_images = re.search(r'<image\s+[^>]*\/>|<<<IMAGE_START>>>', input_text, re.IGNORECASE)
    has_output_images = re.search(r'<image\s+[^>]*\/>|<<<IMAGE_START>>>', output_text, re.IGNORECASE)

    if has_input_images and not has_output_images:
        patched = insert_missing_image_blocks(input_text, output_text)
        log_message(f"[PATCHED] {fname} — missing image blocks patched.")
        return patched

    return output_text

import re

def remove_image_blocks_if_unexpected(fname: str, output_text: str, log_message=print) -> str:
    """
    Removes <image ... /> tags and <<<IMAGE_START>>>...<<<IMAGE_END>>> blocks if
    the filename does NOT contain '- image'.
    Logs cleanup if changes are made.
    """
    if "- image" in fname:
        return output_text  # Skip removal for expected image chapters

    original_text = output_text

    # Remove all <image ... /> tags (HTML self-closing style)
    output_text = re.sub(
        r'<image\s+[^>]*src\s*=\s*["\'][^"\']+["\'][^>]*\/?>',
        '',
        output_text,
        flags=re.IGNORECASE
    )

    # Remove all <<<IMAGE_START>>> ... <<<IMAGE_END>>> blocks (even multiline)
    output_text = re.sub(
        r'<<<IMAGE_START>>>\s*.*?\s*<<<IMAGE_END>>>',
        '',
        output_text,
        flags=re.DOTALL
    )

    if output_text != original_text:
        log_message(f"[CLEANUP] {fname} — removed image blocks.")
    
    return output_text


def validate_image_blocks_all(input_dir="input", output_dir="output", log_message=print):
    """
    For all translated files:
    - Patch missing image blocks if '- image' is in the filename.
    - Remove unintended image blocks otherwise.
    - Log actions if changes were made.
    """
    translated_files = [f for f in os.listdir(output_dir) if f.endswith(".txt")]

    for fname in translated_files:
        input_path = os.path.join(input_dir, fname.replace("translated_", "", 1))
        output_path = os.path.join(output_dir, fname)

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                input_text = f.read()
            with open(output_path, "r", encoding="utf-8") as f:
                output_text = f.read()

            patched = patch_image_blocks_if_missing(fname, input_text, output_text, log_message=log_message)
            cleaned = remove_image_blocks_if_unexpected(fname, patched, log_message=log_message)

            if cleaned != output_text:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)

        except Exception as e:
            log_message(f"[ERROR] Failed image block validation for {fname}: {e}")

def patch_missing_images(input_dir="input", output_dir="output", log_message=print):
    """
    Patches missing image blocks in all translated files that are expected to contain images.
    """
    translated_files = [f for f in os.listdir(output_dir) if f.endswith(".txt") and "- image" in f]

    for fname in translated_files:
        input_path = os.path.join(input_dir, fname.replace("translated_", "", 1))
        output_path = os.path.join(output_dir, fname)

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                input_text = f.read()
            with open(output_path, "r", encoding="utf-8") as f:
                output_text = f.read()

            patched = insert_missing_image_blocks(input_text, output_text)
            if patched != output_text:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(patched)
                log_message(f"[PATCHED] {fname} — missing image blocks inserted.")

        except Exception as e:
            log_message(f"[ERROR] Failed to patch image blocks in {fname}: {e}")
