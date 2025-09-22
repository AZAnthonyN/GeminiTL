
"""Refactored main_ph.py — Main entry point for the translation workflow."""

import os
import re
import time
from translation.translator import Translator
from glossary.glossary import Glossary
from proofing.proofing import Proofreader
from translation.image_ocr import ImageOCR
from glossary.glossary_splitter import split_glossary
from proofing.utils import is_image_only_chapter

# Try to import the new multi-provider translator
try:
    from translation.multi_provider_translator import MultiProviderTranslator
    MULTI_PROVIDER_AVAILABLE = True
except ImportError:
    MULTI_PROVIDER_AVAILABLE = False

def create_translator(glossary_file, source_lang='Japanese', preferred_provider=None):
    """Create the appropriate translator instance."""
    if MULTI_PROVIDER_AVAILABLE:
        return MultiProviderTranslator(glossary_file, source_lang, preferred_provider)
    else:
        return Translator(glossary_file, source_lang)

def setup_glossary(glossary_file, input_folder, log_message):
    glossary = Glossary()

    if glossary_file:
        glossary.set_current_glossary_file(glossary_file)
    else:
        glossary.create_named_glossary_if_none(input_folder, log_message)

    log_message(f"[GLOSSARY] Using glossary file: {glossary.get_current_glossary_file()}")

    try:
        split_glossary(glossary.get_current_glossary_file())
        log_message("[GLOSSARY] Ensured name/context subfiles exist.")
    except Exception as e:
        log_message(f"[GLOSSARY] Split error or missing glossary: {e}")
    return glossary

def run_glossary_phase(text_files, glossary, log_message, pause_event=None, cancel_flag=None):
    log_message("\n=== Phase 1: Building Glossary ===")
    for idx, filename in enumerate(text_files, 1):
        # Check for cancel/pause before processing each file
        if cancel_flag and cancel_flag():
            log_message("[CONTROL] Glossary building canceled.")
            break
            
        if pause_event and not pause_event.is_set():
            log_message("[CONTROL] Paused during glossary building. Waiting...")
            pause_event.wait()
            log_message("[CONTROL] Resumed glossary building.")
            if cancel_flag and cancel_flag():
                log_message("[CONTROL] Glossary building canceled after resume.")
                break
                
        input_path = os.path.join("input", filename)
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Check for cancel/pause after file reading
            if cancel_flag and cancel_flag():
                log_message("[CONTROL] Glossary building canceled after file reading.")
                break
                
            if pause_event and not pause_event.is_set():
                log_message("[CONTROL] Paused after file reading. Waiting...")
                pause_event.wait()
                log_message("[CONTROL] Resumed glossary building.")
                if cancel_flag and cancel_flag():
                    log_message("[CONTROL] Glossary building canceled after resume.")
                    break
                
            # Skip image-only chapters
            if is_image_only_chapter(content):
                log_message(f"[SKIP] {filename} contains only image embeds. Skipping glossary extraction.")
                continue
                
            glossary.build_glossary(content, log_message, split_glossary=False)
            log_message(f"Processed {filename} for glossary")
            
            # Add a 3-second delay between chapters
            if idx < len(text_files):
                log_message(f"[DELAY] Waiting 3 seconds before next chapter...")
                from proofing.utils import cancellable_sleep
                if not cancellable_sleep(3, cancel_flag):
                    log_message("[CONTROL] Glossary building cancelled during chapter delay.")
                    break
                
        except Exception as e:
            log_message(f"[ERROR] {filename}: {e}")

    log_message("\n--- Glossary Proofreading ---")
    proofreader = Proofreader(log_message, glossary.get_current_glossary_file())
    proofreader.proof_glossary_file(glossary.get_current_glossary_file())
    
    # Add glossary cleaning step
    log_message("\n--- Glossary Cleaning ---")
    try:
        from glossary.glossary_cleaner import clean_glossary
        clean_result = clean_glossary(glossary.get_current_glossary_file(), log_message)
        if clean_result:
            log_message("[GLOSSARY] Cleaning completed successfully.")
        else:
            log_message("[GLOSSARY] Cleaning failed or no changes needed.")
    except Exception as e:
        log_message(f"[GLOSSARY] Cleaning error: {e}")
    
    try:
        split_glossary(glossary.get_current_glossary_file())
        log_message("[GLOSSARY] Split into name/context glossaries.")
    except Exception as e:
        log_message(f"[GLOSSARY] Split error: {e}")
    
    log_message("========= glossary phase end =========\n")

def run_translation_phase(text_files, glossary, log_message, pause_event, cancel_flag, source_lang, preferred_provider=None):
    translator = create_translator(glossary.get_current_glossary_file(), source_lang, preferred_provider)
    if hasattr(translator, 'glossary'):
        translator.glossary = glossary
    if not os.path.exists("output"):
        os.makedirs("output")
        log_message("Created 'output' directory")

    for i, filename in enumerate(text_files, 1):
        input_path = os.path.join("input", filename)
        output_path = os.path.join("output", f"translated_{filename}")
        log_message(f"\nTranslating file {i} of {len(text_files)}: {filename}")

        # Check for cancel/pause before processing each file
        if cancel_flag and cancel_flag():
            log_message("[CONTROL] Translation canceled before processing.")
            break
        if pause_event and not pause_event.is_set():
            log_message("[CONTROL] Paused. Waiting...")
            pause_event.wait()
            log_message("[CONTROL] Resumed.")
            if cancel_flag and cancel_flag():
                log_message("[CONTROL] Translation canceled after resume.")
                break

        try:
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add check for cancel/pause after file reading
            if cancel_flag and cancel_flag():
                log_message("[CONTROL] Translation canceled after file reading.")
                break
            if pause_event and not pause_event.is_set():
                log_message("[CONTROL] Paused after file reading. Waiting...")
                pause_event.wait()
                log_message("[CONTROL] Resumed.")
                if cancel_flag and cancel_flag():
                    log_message("[CONTROL] Translation canceled after resume.")
                    break

            if not content.strip():
                log_message(f"[SKIP] {filename} is empty.")
                continue

            # Skip image-only chapters
            if is_image_only_chapter(content):
                log_message(f"[SKIP] {filename} contains only image embeds. Copying without translation...")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                continue

            html_only = re.sub(r"<[^>]+>", "", content).strip() == ""
            if html_only:
                log_message(f"[SKIP] {filename} is HTML only. Copying...")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                continue

            if "<img" in content:
                log_message(f"[INFO] Running OCR for {filename}...")
                image_ocr = ImageOCR(log_function=log_message)
                content = image_ocr.replace_image_tags_with_ocr(content, os.path.join("input", "images"))

            translated = translator.translate(content, log_message, cancel_flag)
            if translated is None:
                log_message(f"[ERROR] Failed to translate {filename}")
                continue

            original_size = len(content.encode("utf-8"))
            translated_size = len(translated.encode("utf-8"))
            retry_threshold_percent = 115.0
            retry_threshold_kb = 7.0  # Add absolute threshold in KB
            percent_diff = ((translated_size - original_size) / original_size * 100) if original_size else 0
            diff_kb = abs(translated_size - original_size) / 1024.0  # Calculate KB difference
            final_translation = translated
            max_retries = 4
            retry_count = 0

            while (abs(percent_diff) > retry_threshold_percent or diff_kb > retry_threshold_kb) and retry_count < max_retries:
                retry_count += 1
                # Exponential backoff: 30s, 60s, 120s, 240s
                retry_delay = 30 * (2 ** (retry_count - 1))
                log_message(f"[RETRY] Translation size mismatch for {filename}: {percent_diff:.2f}%, {diff_kb:.2f} KB. Retrying {retry_count}/{max_retries} in {retry_delay}s...")

                # Use cancellable sleep for exponential backoff
                from proofing.utils import cancellable_sleep
                if not cancellable_sleep(retry_delay, cancel_flag):
                    log_message("[CONTROL] Retry cancelled during exponential backoff delay.")
                    break

                translated_retry = translator.translate(content, log_message, cancel_flag)
                if translated_retry:
                    retry_size = len(translated_retry.encode("utf-8"))
                    retry_percent_diff = ((retry_size - original_size) / original_size * 100) if original_size else 0
                    retry_diff_kb = abs(retry_size - original_size) / 1024.0
                    if abs(retry_percent_diff) <= retry_threshold_percent and retry_diff_kb <= retry_threshold_kb:
                        final_translation = translated_retry
                        log_message("[OK] Retry successful.")
                        break
                    percent_diff = retry_percent_diff
                    diff_kb = retry_diff_kb
                else:
                    log_message("[ERROR] Retry translation failed.")
                    break
            
            # Only show this message if we still have size issues after all retries
            if abs(percent_diff) > retry_threshold_percent or diff_kb > retry_threshold_kb:
                log_message("[NOTICE] Using original translation result despite size deviation.")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_translation)
            log_message(f"[OK] Translated output saved: {output_path}")

            placeholder_pattern = re.compile(r'__IMAGE_TAG_(\d+)__')
            original_placeholders = set(placeholder_pattern.findall(content))
            translated_placeholders = set(placeholder_pattern.findall(final_translation))
            if original_placeholders != translated_placeholders:
                log_message(f"[WARNING] Placeholder mismatch in {filename}: Original={len(original_placeholders)}, Translated={len(translated_placeholders)}")

        except Exception as e:
            log_message(f"[ERROR] Failed during {filename}: {e}")

def run_proofing_phase(glossary, log_message, pause_event=None, cancel_flag=None, subphase=None):
    proofreader = Proofreader(log_message, glossary.get_current_glossary_file())

    log_message("\n========= proofing phase start =========")
    
    from proofing.utils import patch_missing_images, validate_image_blocks_all

    patch_missing_images()
    validate_image_blocks_all(log_message=log_message)

    # If no specific subphase is selected, or if we're starting from the beginning
    if subphase is None or subphase == "non_english":
        # --- Non-English Proofing
        log_message("=== Subphase: Non-English Check ===")
        non_english_log = os.path.join("output", "non_english_lines.log")
        
        # Process files in output directory
        translated_files = sorted(f for f in os.listdir("output") if f.endswith(".txt"))
        
        # Skip image-only chapters and small files for non-English check
        for fname in translated_files:
            try:
                file_path = os.path.join("output", fname)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Skip files that are 1KB or smaller
                file_size_bytes = len(content.encode("utf-8"))
                if file_size_bytes <= 1024:
                    log_message(f"[SKIP] {fname} is too small ({file_size_bytes} bytes). Skipping non-English check.")
                    continue

                if is_image_only_chapter(content):
                    log_message(f"[SKIP] {fname} contains only image embeds. Skipping non-English check.")
                    continue
            except Exception as e:
                log_message(f"[ERROR] Failed to check {fname}: {e}")
        
        proofreader.detect_and_log_non_english_sentences(
            "output", non_english_log, "input", pause_event, cancel_flag
        )
        

    # COMMENTED OUT: Gender proofing section - diminishing returns
    # if subphase is None or subphase == "gender":
    #     # --- Gender Proofing
    #     log_message("=== Subphase: Gender Proofing ===")

    #     context_dict = proofreader.load_context_glossary()
    #     translated_files = sorted(f for f in os.listdir("output") if f.endswith(".txt"))

    #     for fname in translated_files:
    #         if cancel_flag and cancel_flag():
    #             log_message("[CONTROL] Cancel requested during gender proofing.")
    #             break

    #         if pause_event and not pause_event.is_set():
    #             log_message("[CONTROL] Paused during gender proofing.")
    #             pause_event.wait()
    #             log_message("[CONTROL] Resumed.")

    #         try:
    #             file_path = os.path.join("output", fname)
    #             with open(file_path, "r", encoding="utf-8") as f:
    #                 translated = f.read()

    #             # Skip files that are 1KB or smaller
    #             file_size_bytes = len(translated.encode("utf-8"))
    #             if file_size_bytes <= 1024:
    #                 log_message(f"[SKIP] {fname} is too small ({file_size_bytes} bytes). Skipping gender proofing.")
    #                 continue

    #             # Skip image-only chapters
    #             if is_image_only_chapter(translated):
    #                 log_message(f"[SKIP] {fname} contains only image embeds. Skipping gender proofing.")
    #                 continue

    #             proofed = proofreader.proof_gender_pronouns(
    #                 translated,
    #                 context_dict,
    #                 glossary_path=glossary.get_current_glossary_file()
    #             )

    #             with open(file_path, "w", encoding="utf-8") as f:
    #                 f.write(proofed)
    #             log_message(f"[OK] Gender fix done for {fname}")
    #         except Exception as e:
    #             log_message(f"[ERROR] Gender fix failed for {fname}: {e}")

    # Skip gender proofing - commented out above
    if subphase == "gender":
        log_message("=== Subphase: Gender Proofing ===")
        log_message("[SKIP] Gender proofing is disabled - provides diminishing returns")


    if subphase is None or subphase == "final":
        # --- Final AI Proofing
        log_message("=== Subphase: Final AI Proofing ===")
        
        translated_files = [f for f in os.listdir("output") if f.endswith(".txt")]
        translated_files.sort()
        
        # Create proofed_ai directory
        proofed_dir = os.path.join("output", "proofed_ai")
        os.makedirs(proofed_dir, exist_ok=True)
        log_message(f"[INFO] AI-proofed files will be saved to: {proofed_dir}")
        
        for fname in translated_files:
            if cancel_flag and cancel_flag():
                log_message("[CONTROL] Cancel requested during AI proofing.")
                break

            if pause_event and not pause_event.is_set():
                log_message("[CONTROL] Paused during AI proofing.")
                pause_event.wait()
                log_message("[CONTROL] Resumed.")
                
            try:
                file_path = os.path.join("output", fname)

                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Skip files that are 1KB or smaller
                file_size_bytes = len(content.encode("utf-8"))
                if file_size_bytes <= 1024:
                    log_message(f"[SKIP] {fname} is too small ({file_size_bytes} bytes). Copying to proofed directory...")
                    with open(os.path.join(proofed_dir, fname), "w", encoding="utf-8") as f:
                        f.write(content)
                    continue

                # Skip image-only chapters
                if is_image_only_chapter(content):
                    log_message(f"[SKIP] {fname} contains only image embeds. Copying to proofed directory...")
                    with open(os.path.join(proofed_dir, fname), "w", encoding="utf-8") as f:
                        f.write(content)
                    continue
                
                ai_proofed = proofreader.proofread_with_ai(file_path)
                
                if ai_proofed:
                    # Save to proofed_ai directory
                    with open(os.path.join(proofed_dir, fname), "w", encoding="utf-8") as f:
                        f.write(ai_proofed)
                    log_message(f"[OK] AI proofing done for {fname}")
                else:
                    log_message(f"[ERROR] AI proofing failed for {fname}")
            except Exception as e:
                log_message(f"[ERROR] AI proofing failed for {fname}: {e}")

    log_message("========= proofing phase end =========\n")


def main(log_message=None, glossary_file=None, proofing_only=False,
         skip_phase1=False, pause_event=None, cancel_flag=None,
         source_lang="Japanese", proofing_subphase=None, input_folder=None,
         preferred_provider=None):

    if log_message is None:
        log_message = print

    folder_to_use = input_folder or os.path.abspath("input")
    glossary = setup_glossary(glossary_file, folder_to_use, log_message)


    input_files = [f for f in os.listdir("input") if f.endswith(".txt")] if os.path.exists("input") else []
    run_translation = bool(input_files)
    text_files = sorted(input_files if run_translation else
                        [f for f in os.listdir("output") if f.endswith(".txt")])

    if not proofing_only:
        if run_translation and not skip_phase1:
            run_glossary_phase(text_files, glossary, log_message, pause_event, cancel_flag)
        if run_translation:
            run_translation_phase(text_files, glossary, log_message, pause_event, cancel_flag, source_lang, preferred_provider)

    # Run proofing phase with subphase control
    run_proofing_phase(glossary, log_message, pause_event, cancel_flag, subphase=proofing_subphase)

if __name__ == "__main__":
    main()














