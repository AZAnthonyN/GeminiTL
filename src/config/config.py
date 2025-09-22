
# src/config/config.py
import os
import vertexai
import vertexai.preview.generative_models as generative_models
from google.oauth2 import service_account

# Paths
this_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(this_dir, "config.txt")
service_account_file = os.path.join(this_dir, "service_account.json")

def read_config():
    config = {}
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    config[key.strip()] = value.strip()
    return config

def initialize_vertexai():
    """Initialize or reinitialize VertexAI with current configuration."""
    global PROJECT_ID, LOCATION, LOGIN_KEY

    # Load config values
    config_values = read_config()
    PROJECT_ID = config_values.get("PROJECT_ID", "your-project-id")
    LOCATION   = config_values.get("LOCATION", "us-central1")
    LOGIN_KEY  = config_values.get("LOGIN_KEY", "")

    # Load and apply credentials from JSON
    if not os.path.exists(service_account_file):
        raise RuntimeError(f"[CONFIG] Missing service_account.json in {this_dir}")

    try:
        credentials = service_account.Credentials.from_service_account_file(service_account_file)
        vertexai.init(project=PROJECT_ID, location=LOCATION, credentials=credentials)
        print(f"[CONFIG] VertexAI initialized - Project: {PROJECT_ID}, Location: {LOCATION}")
    except Exception as e:
        raise RuntimeError(f"[CONFIG] Failed to initialize VertexAI with service account: {e}")

# Initialize on first import
try:
    initialize_vertexai()
except Exception as e:
    print(f"[CONFIG] Warning: Initial VertexAI initialization failed: {e}")
    # Set default values if initialization fails
    PROJECT_ID = "your-project-id"
    LOCATION = "us-central1"
    LOGIN_KEY = ""

# Global safety settings
SAFETY_SETTING = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.OFF,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.OFF,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.OFF,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.OFF,
    generative_models.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY: generative_models.HarmBlockThreshold.OFF,
    generative_models.HarmCategory.HARM_CATEGORY_UNSPECIFIED: generative_models.HarmBlockThreshold.OFF,
}
