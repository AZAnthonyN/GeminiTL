# GeminiTL - AI-Powered Novel Translation Tool

GeminiTL is a comprehensive translation tool designed for translating novels and light novels from Japanese, Korean, and Chinese into English. It features both a graphical user interface (GUI) and command-line interface (CLI), with support for multiple AI providers and advanced translation workflows.

## 🌟 Key Features

### Multi-Interface Support
- **GUI Mode**: User-friendly graphical interface for interactive workflows
- **CLI Mode**: Command-line interface for automation and scripting
- **Docker Support**: Containerized deployment for Raspberry Pi 5 and other platforms
- Seamless switching between modes

### Multi-Provider AI Translation
- **Google Gemini** (via VertexAI) - Free tier available, excellent reasoning
- **OpenAI GPT** - Industry-leading models (GPT-4, GPT-4o)
- **Anthropic Claude** - Advanced literary translation capabilities
- Automatic fallback between providers
- Provider-specific optimizations

### Complete Translation Workflow
1. **EPUB Processing**: Extract chapters from EPUB files
2. **Glossary Building**: AI-powered glossary creation for consistent terminology
3. **Translation**: Multi-phase translation with context awareness
4. **Proofing**: Automated quality checks including:
   - Gender consistency checking
   - Glossary term verification
   - Style consistency
   - Non-English text detection
5. **EPUB Creation**: Combine translated chapters back into EPUB format

### Advanced Features
- **Image OCR**: Extract and translate text from images in novels
- **Context-Aware Translation**: Maintains character names, terms, and style
- **Glossary Management**: Build and maintain translation glossaries
- **Batch Processing**: Process multiple chapters efficiently
- **Cost Tracking**: Monitor API usage and costs for paid providers

## 🚀 Quick Start

### Installation Options

#### Option 1: Native Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/GeminiTL.git
   cd GeminiTL
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure AI providers** (see [Configuration](#configuration) section below)

#### Option 2: Docker Installation (Recommended for Raspberry Pi 5)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/GeminiTL.git
   cd GeminiTL
   ```

2. **Build Docker image**:
   ```bash
   docker build -t geminitl:latest .
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker setup and usage.

### Basic Usage

#### GUI Mode (Default)
Simply run the program to launch the graphical interface:
```bash
python main.py
```

#### CLI Mode
Use command-line arguments for automation:
```bash
# Get help
python main.py --help

# Translate an EPUB novel
python main.py epub-separate novel.epub ./input
python main.py translate --source-lang Japanese
python main.py epub-combine ./output translated_novel.epub

# Translate with specific AI provider
python main.py translate --provider openai --source-lang Japanese
```

## 📖 Usage Modes

### GUI Workflow
1. Launch the application: `python main.py`
2. Use the "Splitter Tools" to extract EPUB or prepare text files
3. Select input folder and configure translation settings
4. Choose AI provider and source language
5. Run translation workflow (glossary → translation → proofing)
6. Use "Output Combiner" to create final EPUB

### CLI Workflow
```bash
# Complete EPUB translation workflow
python main.py epub-separate novel.epub ./input
python main.py translate --provider openai --source-lang Japanese
python main.py proof
python main.py epub-combine ./output translated_novel.epub --reference-epub novel.epub
```

See [CLI_README.md](CLI_README.md) for detailed CLI documentation.

## ⚙️ Configuration

### Google Gemini (VertexAI)
1. Create a Google Cloud project
2. Enable Vertex AI and Cloud Vision APIs
3. Create a service account with appropriate roles
4. Download service account JSON and place in `src/config/service_account.json`
5. Update `src/config/config.txt` with your project details

See [src/config/README.md](src/config/README.md) for detailed setup instructions.

### OpenAI
Set your API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or add to `src/config/providers_config.json`:
```json
{
  "openai": {
    "api_key": "your-api-key-here"
  }
}
```

### Anthropic Claude
Set your API key as an environment variable:
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or add to `src/config/providers_config.json`:
```json
{
  "anthropic": {
    "api_key": "your-api-key-here"
  }
}
```

See [MULTI_PROVIDER_README.md](MULTI_PROVIDER_README.md) for detailed provider configuration.

## 📁 Project Structure

```
GeminiTL/
├── main.py                 # Main entry point (GUI/CLI router)
├── cli.py                  # Command-line interface
├── Dockerfile              # Docker image for Raspberry Pi 5
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore           # Docker build exclusions
├── .env.template           # Environment variables template
├── docker-quickstart.sh    # Docker helper script
├── requirements.txt        # Python dependencies
├── src/
│   ├── ai_providers/      # AI provider implementations
│   ├── chapter_splitting_tools/  # EPUB and text processing
│   ├── config/            # Configuration files
│   ├── glossary/          # Glossary management
│   ├── gui/               # GUI application
│   ├── proofing/          # Quality checking tools
│   ├── translation/       # Translation engine
│   └── utils/             # Utility functions
├── input/                 # Input text files (created automatically)
├── output/                # Translated output (created automatically)
└── compiled_epubs/        # Final EPUB files (created automatically)
```

## 🎯 Supported Languages

- **Source Languages**: Japanese, Korean, Chinese
- **Target Language**: English

## 📚 Documentation

- [CLI_README.md](CLI_README.md) - Command-line interface guide
- [DOCKER_README.md](DOCKER_README.md) - Docker deployment for Raspberry Pi 5
- [MULTI_PROVIDER_README.md](MULTI_PROVIDER_README.md) - Multi-provider AI setup
- [GUI_LAYOUT_UPDATE.md](GUI_LAYOUT_UPDATE.md) - GUI interface documentation
- [src/config/README.md](src/config/README.md) - Configuration setup guide

## 🔧 Requirements

- Python 3.8+
- wxPython (for GUI)
- Google Cloud credentials (for Gemini)
- OpenAI API key (optional, for OpenAI)
- Anthropic API key (optional, for Claude)

See [requirements.txt](requirements.txt) for complete dependency list.

## 💡 Translation Workflow Details

### Phase 1: Glossary Building
The tool analyzes your source text to identify:
- Character names and titles
- Recurring terms and phrases
- Location names
- Special terminology

The AI builds a glossary to ensure consistent translation throughout the work.

### Phase 2: Translation
- Translates text chapter by chapter
- Uses glossary for consistent terminology
- Maintains context across chapters
- Preserves formatting and structure
- Handles image placeholders

### Phase 3: Proofing
Automated quality checks include:
- **Gender Proofing**: Ensures consistent pronoun usage for characters
- **Glossary Proofing**: Verifies glossary terms are used correctly
- **Style Proofing**: Checks for consistency in writing style
- **Non-English Detection**: Identifies untranslated text

## 🎨 GUI Features

The graphical interface provides:
- **Visual Workflow**: Step-by-step translation process
- **Real-time Logging**: Monitor translation progress
- **Provider Selection**: Choose AI provider from dropdown
- **Language Selection**: Select source language
- **Pause/Resume**: Control translation execution
- **Splitter Tools**: Built-in EPUB and text processing
- **Output Combiner**: Create EPUB from translated files

## 🖥️ CLI Features

The command-line interface offers:
- **Automation**: Script entire translation workflows
- **Batch Processing**: Process multiple files
- **Flexible Options**: Fine-grained control over each phase
- **Logging**: Redirect output to files for analysis
- **Integration**: Easy integration with other tools

## 🌐 Use Cases

### Light Novel Translation
Perfect for translating Japanese light novels with:
- Character dialogue and narration
- Consistent character names and terms
- Proper formatting preservation

### Web Novel Translation
Ideal for web novels with:
- Chapter-by-chapter processing
- Glossary management across volumes
- Batch processing capabilities

### EPUB Processing
Handles EPUB files with:
- Image extraction and OCR
- Chapter separation
- Metadata preservation
- Final EPUB compilation

## 🔍 Advanced Features

### Image OCR
- Extracts text from images in novels
- Supports Japanese, Korean, and Chinese text
- Integrates with Google Cloud Vision API
- Preserves image placement in output

### Context-Aware Translation
- Maintains character relationships
- Preserves honorifics and titles
- Adapts to genre and style
- Handles cultural references

### Glossary Management
- AI-powered term extraction
- Manual glossary editing
- Context-aware term matching
- Glossary splitting for large files

## 🛠️ Troubleshooting

### Common Issues

**GUI won't launch**:
- Ensure wxPython is installed: `pip install wxPython`
- Check Python version (3.8+ required)

**Translation fails**:
- Verify API credentials are configured
- Check internet connection
- Review error logs in the GUI or terminal

**EPUB processing errors**:
- Ensure input EPUB is valid
- Check file permissions
- Verify output directory exists

**Provider authentication errors**:
- Verify API keys are correct
- Check service account permissions (for Gemini)
- Ensure environment variables are set

### Validation

Test your provider setup:
```bash
cd src
python validate_providers.py
```

## 📊 Performance Tips

1. **Use appropriate providers**:
   - Gemini: Best for free tier, good quality
   - OpenAI: Fast and consistent
   - Anthropic: Best for literary quality

2. **Optimize batch size**:
   - Smaller chapters process faster
   - Larger chapters may hit token limits

3. **Manage costs**:
   - Use Gemini free tier for testing
   - Monitor token usage with paid providers
   - Use `--glossary-only` to build glossary separately

4. **Improve quality**:
   - Review and edit glossary before translation
   - Run proofing phases separately
   - Use reference EPUBs for better formatting

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional AI provider support
- Translation quality enhancements
- GUI improvements
- Documentation updates
- Bug fixes

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- Google Cloud Platform for Vertex AI
- OpenAI for GPT models
- Anthropic for Claude
- wxPython for GUI framework
- All contributors and users

## 📞 Support

For issues and questions:
- Check existing documentation
- Review troubleshooting section
- Open an issue on GitHub
- See provider-specific documentation

## 🔄 Version History

### Version 1.0.0
- Initial release with GUI and CLI support
- Multi-provider AI translation
- Complete translation workflow
- EPUB processing capabilities
- Advanced proofing features

---

**Note**: This tool is designed for personal use and learning purposes. Please respect copyright laws and only translate works you have permission to translate.

