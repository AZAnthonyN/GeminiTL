#!/usr/bin/env python3
"""
Command-line interface for GeminiTL - Novel Translation Tool

This CLI provides access to all major features of the translation tool:
- EPUB processing (separation, combination)
- Novel splitting
- Translation workflow (glossary building, translation, proofing)
- Multi-provider AI translation support
"""

import argparse
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
if src_path.exists() and str(src_path.resolve()) not in sys.path:
    sys.path.insert(0, str(src_path.resolve()))


def setup_epub_parser(subparsers):
    """Setup EPUB-related commands."""
    epub_parser = subparsers.add_parser(
        'epub-separate',
        help='Separate EPUB file into text chapters'
    )
    epub_parser.add_argument('epub_file', help='Path to the EPUB file')
    epub_parser.add_argument('output_dir', help='Directory to save separated chapters')
    epub_parser.add_argument('--max-bytes', type=int, help='Maximum bytes per chapter file')
    
    epub_combine_parser = subparsers.add_parser(
        'epub-combine',
        help='Combine translated chapters into EPUB'
    )
    epub_combine_parser.add_argument('input_dir', help='Directory containing translated chapters')
    epub_combine_parser.add_argument('output_file', help='Output EPUB file path')
    epub_combine_parser.add_argument('--reference-epub', help='Reference EPUB for structure')





def setup_translate_parser(subparsers):
    """Setup translation workflow commands."""
    translate_parser = subparsers.add_parser(
        'translate',
        help='Run translation workflow'
    )
    translate_parser.add_argument(
        '--input-folder',
        default='input',
        help='Input folder containing text files (default: input)'
    )
    translate_parser.add_argument(
        '--glossary',
        help='Path to glossary file'
    )
    translate_parser.add_argument(
        '--source-lang',
        default='Japanese',
        choices=['Japanese', 'Korean', 'Chinese'],
        help='Source language (default: Japanese)'
    )
    translate_parser.add_argument(
        '--provider',
        choices=['gemini', 'openai', 'anthropic'],
        help='Preferred AI provider (default: auto-fallback)'
    )
    translate_parser.add_argument(
        '--skip-glossary',
        action='store_true',
        help='Skip glossary building phase'
    )
    translate_parser.add_argument(
        '--glossary-only',
        action='store_true',
        help='Only build glossary, skip translation'
    )
    translate_parser.add_argument(
        '--no-proofing',
        action='store_true',
        help='Skip proofing phase'
    )


def setup_proof_parser(subparsers):
    """Setup proofing command."""
    proof_parser = subparsers.add_parser(
        'proof',
        help='Run proofing on translated files'
    )
    proof_parser.add_argument(
        '--glossary',
        help='Path to glossary file'
    )
    proof_parser.add_argument(
        '--subphase',
        choices=['gender', 'glossary', 'style', 'non-english'],
        help='Run specific proofing subphase only'
    )


def setup_gui_parser(subparsers):
    """Setup GUI launch command."""
    subparsers.add_parser(
        'gui',
        help='Launch the graphical user interface'
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='GeminiTL - Novel Translation Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Separate EPUB into chapters
  python main.py epub-separate novel.epub ./input

  # Combine translated chapters into EPUB
  python main.py epub-combine ./output translated_novel.epub

  # Translate with specific provider
  python main.py translate --provider openai --source-lang Japanese

  # Build glossary only
  python main.py translate --glossary-only

  # Run proofing only
  python main.py proof --glossary my_glossary.txt

  # Launch GUI (or just run without arguments)
  python main.py gui
  python main.py
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='GeminiTL 1.0.0'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup all command parsers
    setup_epub_parser(subparsers)
    setup_translate_parser(subparsers)
    setup_proof_parser(subparsers)
    setup_gui_parser(subparsers)
    
    args = parser.parse_args()
    
    # If no command specified, show help
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Execute the appropriate command
    execute_command(args)


def execute_command(args):
    """Execute the command based on parsed arguments."""

    if args.command == 'epub-separate':
        execute_epub_separate(args)
    elif args.command == 'epub-combine':
        execute_epub_combine(args)
    elif args.command == 'translate':
        execute_translate(args)
    elif args.command == 'proof':
        execute_proof(args)
    elif args.command == 'gui':
        execute_gui(args)
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


def execute_epub_separate(args):
    """Execute EPUB separation."""
    from chapter_splitting_tools.epub_separator import EPUBSeparator

    print(f"Separating EPUB: {args.epub_file}")
    print(f"Output directory: {args.output_dir}")

    separator = EPUBSeparator(log_function=print)
    if args.max_bytes:
        separator.max_byte_limit = args.max_bytes

    try:
        separator.separate(args.epub_file, args.output_dir, max_bytes=args.max_bytes)
        print(f"\n✓ EPUB separated successfully!")
        print(f"  Output saved to: {args.output_dir}")
    except Exception as e:
        print(f"\n✗ Error separating EPUB: {e}")
        sys.exit(1)


def execute_epub_combine(args):
    """Execute EPUB combination."""
    from chapter_splitting_tools.output_combiner import OutputCombiner

    print(f"Combining chapters from: {args.input_dir}")
    print(f"Output file: {args.output_file}")

    combiner = OutputCombiner()

    try:
        combiner.combine(
            args.input_dir,
            args.output_file,
            'epub',
            reference_epub=args.reference_epub
        )
        print(f"\n✓ EPUB created successfully!")
        print(f"  Output saved to: {args.output_file}")
    except Exception as e:
        print(f"\n✗ Error creating EPUB: {e}")
        sys.exit(1)


def execute_translate(args):
    """Execute translation workflow."""
    from translation.translationManager import main as translation_main

    print("=" * 60)
    print("GeminiTL Translation Workflow")
    print("=" * 60)
    print(f"Input folder: {args.input_folder}")
    print(f"Source language: {args.source_lang}")
    if args.glossary:
        print(f"Glossary file: {args.glossary}")
    if args.provider:
        print(f"AI Provider: {args.provider}")
    print("=" * 60)
    print()

    # Determine workflow flags
    proofing_only = False
    skip_phase1 = args.skip_glossary

    if args.glossary_only:
        # For glossary-only, we need to run phase 1 but skip translation
        # This requires a custom approach
        from translation.translationManager import setup_glossary, run_glossary_phase
        import os

        glossary = setup_glossary(args.glossary, args.input_folder, print)
        input_files = [f for f in os.listdir(args.input_folder) if f.endswith(".txt")]
        text_files = sorted(input_files)

        run_glossary_phase(text_files, glossary, print)
        print("\n✓ Glossary building completed!")
        return

    try:
        translation_main(
            log_message=print,
            glossary_file=args.glossary,
            proofing_only=proofing_only,
            skip_phase1=skip_phase1,
            source_lang=args.source_lang,
            input_folder=args.input_folder,
            preferred_provider=args.provider,
            proofing_subphase=None if not args.no_proofing else 'skip'
        )
        print("\n✓ Translation workflow completed!")
    except KeyboardInterrupt:
        print("\n\n⚠ Translation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error during translation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def execute_proof(args):
    """Execute proofing workflow."""
    from translation.translationManager import main as translation_main

    print("=" * 60)
    print("GeminiTL Proofing Workflow")
    print("=" * 60)
    if args.glossary:
        print(f"Glossary file: {args.glossary}")
    if args.subphase:
        print(f"Subphase: {args.subphase}")
    print("=" * 60)
    print()

    try:
        translation_main(
            log_message=print,
            glossary_file=args.glossary,
            proofing_only=True,
            proofing_subphase=args.subphase
        )
        print("\n✓ Proofing completed!")
    except Exception as e:
        print(f"\n✗ Error during proofing: {e}")
        sys.exit(1)


def execute_gui(args):
    """Launch the GUI application."""
    import wx
    from gui.app import TranslationApp

    print("Launching GUI...")

    # Ensure we're in the correct working directory
    os.chdir(Path(__file__).parent)

    app = wx.App()
    frame = TranslationApp()
    frame.Show()
    app.MainLoop()


if __name__ == '__main__':
    main()

