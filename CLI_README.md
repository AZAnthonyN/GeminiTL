# GeminiTL Command-Line Interface

GeminiTL now supports both GUI and CLI modes for maximum flexibility in your translation workflow.

## Quick Start

### GUI Mode (Default)
Simply run the program without arguments to launch the graphical interface:
```bash
python main.py
```

### CLI Mode
Pass any command to use the command-line interface:
```bash
python main.py --help
```

## Available Commands

### 1. EPUB Separation
Extract chapters from an EPUB file into text files for translation:

```bash
python main.py epub-separate <epub_file> <output_dir> [--max-bytes SIZE]
```

**Example:**
```bash
python main.py epub-separate novel.epub ./input
python main.py epub-separate novel.epub ./input --max-bytes 30000
```

### 2. EPUB Combination
Combine translated text files back into an EPUB:

```bash
python main.py epub-combine <input_dir> <output_file> [--reference-epub FILE]
```

**Example:**
```bash
python main.py epub-combine ./output translated_novel.epub
python main.py epub-combine ./output translated_novel.epub --reference-epub original.epub
```

### 3. Translation Workflow
Run the complete translation workflow with various options:

```bash
python main.py translate [OPTIONS]
```

**Options:**
- `--input-folder PATH` - Input folder containing text files (default: `input`)
- `--glossary PATH` - Path to glossary file
- `--source-lang LANG` - Source language: Japanese, Korean, or Chinese (default: Japanese)
- `--provider PROVIDER` - AI provider: gemini, openai, or anthropic (default: auto-fallback)
- `--skip-glossary` - Skip glossary building phase
- `--glossary-only` - Only build glossary, skip translation
- `--no-proofing` - Skip proofing phase

**Examples:**
```bash
# Basic translation
python main.py translate

# Translate with OpenAI
python main.py translate --provider openai --source-lang Japanese

# Build glossary only
python main.py translate --glossary-only

# Translate Korean novel with custom glossary
python main.py translate --source-lang Korean --glossary my_glossary.txt

# Skip glossary building (use existing)
python main.py translate --skip-glossary
```

### 4. Proofing
Run proofing on already translated files:

```bash
python main.py proof [OPTIONS]
```

**Options:**
- `--glossary PATH` - Path to glossary file
- `--subphase TYPE` - Run specific proofing subphase: gender, glossary, style, or non-english

**Examples:**
```bash
# Run all proofing phases
python main.py proof

# Run only gender proofing
python main.py proof --subphase gender

# Proof with specific glossary
python main.py proof --glossary my_glossary.txt
```

### 5. Launch GUI
Explicitly launch the GUI (same as running without arguments):

```bash
python main.py gui
```

## Typical Workflows

### Workflow 1: Translate an EPUB Novel

```bash
# Step 1: Extract EPUB to text files
python main.py epub-separate novel.epub ./input

# Step 2: Run translation
python main.py translate --source-lang Japanese --provider openai

# Step 3: Combine back to EPUB
python main.py epub-combine ./output translated_novel.epub --reference-epub novel.epub
```

### Workflow 2: Translate Text Files

```bash
# Place your .txt files in the input folder, then:

# Step 1: Build glossary and translate
python main.py translate --source-lang Japanese

# Step 2: Review and re-proof if needed
python main.py proof
```

### Workflow 3: Multi-Provider Translation

```bash
# Try OpenAI first, with automatic fallback to other providers
python main.py translate --provider openai

# Or use Anthropic Claude for literary translation
python main.py translate --provider anthropic
```

## AI Provider Configuration

The CLI supports multiple AI providers. Make sure you have the necessary API keys configured:

- **Gemini**: Configure Google Cloud service account (see `src/config/README.md`)
- **OpenAI**: Set `OPENAI_API_KEY` environment variable
- **Anthropic**: Set `ANTHROPIC_API_KEY` environment variable

See `MULTI_PROVIDER_README.md` for detailed provider setup instructions.

## Tips

1. **Interrupting Operations**: Press `Ctrl+C` to gracefully interrupt translation or proofing
2. **Logging**: All CLI operations log to stdout - redirect to a file if needed:
   ```bash
   python main.py translate > translation.log 2>&1
   ```
3. **Batch Processing**: Use shell scripts to process multiple files:
   ```bash
   for epub in *.epub; do
       python main.py epub-separate "$epub" "./input/${epub%.epub}"
   done
   ```

## Getting Help

For detailed help on any command:
```bash
python main.py --help
python main.py translate --help
python main.py proof --help
```

For GUI-based workflows, simply run:
```bash
python main.py
```

