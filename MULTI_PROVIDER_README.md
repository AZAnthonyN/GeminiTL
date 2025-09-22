# Multi-Provider AI Translation System

This document describes the new multi-provider AI system that has been added to the GeminiAPITranslator program. The system allows you to use multiple AI providers (Gemini, OpenAI, Anthropic) for translation with automatic fallback and provider-specific optimizations.

## Features

### 🤖 Multiple AI Providers
- **Google Gemini** (via VertexAI) - Original provider with advanced reasoning
- **OpenAI GPT** - Industry-leading language models (GPT-4, GPT-4o, etc.)
- **Anthropic Claude** - Advanced AI with strong translation capabilities

### 🔄 Intelligent Fallback
- Automatic fallback to other providers if the primary fails
- Configurable fallback order
- Smart retry logic with exponential backoff
- Provider-specific error handling

### ⚙️ Provider-Specific Optimizations
- Customized prompts for each provider's strengths
- Provider-specific parameter tuning
- Optimized for translation quality and consistency

### 💰 Cost Tracking
- Approximate cost calculation for OpenAI and Anthropic
- Token usage tracking
- Provider comparison metrics

## Installation

### Required Dependencies

The system will work with just Gemini (existing setup), but to use all providers, install:

```bash
# For OpenAI support
pip install openai

# For Anthropic support  
pip install anthropic
```

### Configuration

1. **Open the Configuration Dialog**: Click the "Config" button in the main GUI
2. **Configure Providers**: Each provider has its own tab with specific settings
3. **Set API Keys**: Enter your API keys for OpenAI and/or Anthropic
4. **Choose Default Provider**: Select which provider to use by default
5. **Set Fallback Order**: Arrange providers in your preferred fallback sequence

## Usage

### GUI Usage

1. **Provider Selection**: Use the "AI Provider" dropdown to choose:
   - "Auto (Fallback)" - Uses default provider with automatic fallback
   - "Gemini" - Forces use of Gemini only
   - "OpenAI" - Forces use of OpenAI only  
   - "Anthropic" - Forces use of Anthropic only

2. **Translation**: Run translation as normal - the system handles provider selection automatically

### Configuration Options

#### Gemini Provider
- **Project ID**: Google Cloud project ID
- **Location**: Google Cloud region (e.g., us-central1)
- **Service Account**: JSON credentials file
- **Model**: Choose from available Gemini models
- **Temperature**: Creativity level (0.0-2.0)

#### OpenAI Provider
- **API Key**: Your OpenAI API key
- **Model**: Choose from GPT models (gpt-4o, gpt-4o-mini, etc.)
- **Temperature**: Creativity level (0.0-2.0)
- **Max Tokens**: Maximum response length

#### Anthropic Provider
- **API Key**: Your Anthropic API key
- **Model**: Choose from Claude models (claude-3-5-sonnet, etc.)
- **Temperature**: Creativity level (0.0-1.0)
- **Max Tokens**: Maximum response length

## Provider Comparison

| Provider | Strengths | Best For | Cost |
|----------|-----------|----------|------|
| **Gemini** | Free tier, good reasoning | General translation, cost-conscious users | Free/Low |
| **OpenAI** | Consistent quality, fast | Professional translation, high volume | Medium |
| **Anthropic** | Nuanced understanding | Literary translation, complex text | Medium-High |

## Advanced Features

### Fallback Logic
The system intelligently handles failures:
- **Rate Limits**: Longer delays, automatic retry
- **API Errors**: Quick fallback to next provider
- **Authentication Issues**: Immediate fallback
- **Network Issues**: Moderate delay, then fallback

### Provider-Specific Prompts
Each provider gets optimized prompts:
- **Gemini**: Detailed examples and explicit instructions
- **OpenAI**: Structured task format with clear requirements
- **Anthropic**: Conversational style with context awareness

### Cost Management
- Real-time cost estimation for paid providers
- Token usage tracking
- Provider cost comparison
- Budget-friendly fallback ordering

## Troubleshooting

### Common Issues

1. **"No available providers"**
   - Check that at least one provider is enabled and configured
   - Verify API keys are correct
   - Run the validation script: `python src/validate_providers.py`

2. **Provider initialization failed**
   - Check API keys and credentials
   - Verify network connectivity
   - Check provider service status

3. **Translation quality issues**
   - Try different providers for comparison
   - Adjust temperature settings
   - Check provider-specific prompts

### Validation Script

Run the validation script to check system health:

```bash
cd src
python validate_providers.py
```

This will check:
- All imports are working
- Providers can be created
- Configuration is valid
- Provider manager is functional
- Prompt templates are available

### Testing

Run the test suite:

```bash
cd src
python tests/test_providers.py
```

## Migration from Single Provider

The system is fully backward compatible:
- Existing Gemini configurations continue to work
- Legacy translator remains available as fallback
- No changes needed to existing workflows
- Gradual migration supported

## Configuration Files

### New Configuration
- `src/config/providers_config.json` - Multi-provider settings
- Automatic migration from legacy `config.txt`

### Legacy Configuration  
- `src/config/config.txt` - Still supported for Gemini
- `src/config/service_account.json` - Still used for Gemini

## API Key Security

- API keys are stored locally in configuration files
- Never transmitted except to respective AI services
- Consider using environment variables for production
- Regularly rotate API keys for security

## Future Enhancements

Planned features:
- Additional providers (Cohere, local models)
- Advanced cost optimization
- Provider performance analytics
- Custom prompt templates
- Batch processing optimizations

## Support

For issues with the multi-provider system:
1. Run the validation script first
2. Check the troubleshooting section
3. Review provider-specific documentation
4. Check API service status pages

## License

This enhancement maintains the same license as the original project.
