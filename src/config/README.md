# Configuration Setup

This directory contains configuration files for the GeminiTL translation tool.

## Service Account Setup

### Google Cloud Service Account

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Required APIs:**
   - Vertex AI API
   - Cloud Vision API (for OCR functionality)

3. **Create a Service Account:**
   - Go to IAM & Admin > Service Accounts
   - Click "Create Service Account"
   - Give it a name like "translation-service"
   - Grant the following roles:
     - Vertex AI User
     - Cloud Vision API User

4. **Generate Service Account Key:**
   - Click on your service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Choose JSON format
   - Download the file

5. **Setup the Configuration:**
   - Copy the downloaded JSON file to `src/config/service_account.json`
   - Or use the template: copy `service_account.json.template` to `service_account.json` and fill in your values

### Configuration Files

- `service_account.json.template` - Template for Google Cloud service account credentials
- `service_account.json` - Your actual service account credentials (not tracked by git)
- `providers_config.json` - API keys and settings for AI providers (not tracked by git)
- `config.txt` - General application configuration (not tracked by git)

### Security Notes

- Never commit actual API keys or service account files to version control
- The `.gitignore` file is configured to exclude sensitive configuration files
- Only template files should be committed to the repository

### Provider Configuration

Create a `providers_config.json` file with your API keys:

```json
{
  "gemini": {
    "project_id": "your-google-cloud-project-id",
    "location": "us-central1"
  },
  "openai": {
    "api_key": "your-openai-api-key"
  },
  "anthropic": {
    "api_key": "your-anthropic-api-key"
  }
}
```
