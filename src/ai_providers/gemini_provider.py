"""
Gemini AI provider implementation.

This module provides integration with Google's Gemini AI models through VertexAI.
"""

import time
import json
from typing import Dict, Any, Optional, List
from vertexai.generative_models import GenerativeModel, GenerationConfig
import vertexai.preview.generative_models as generative_models

from .base_provider import BaseAIProvider, ProviderType, TranslationResult
from config.config import SAFETY_SETTING, initialize_vertexai


class GeminiProvider(BaseAIProvider):
    """Gemini AI provider for translation services."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = ProviderType.GEMINI
        self.model = None
        self.available_models = [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro"
        ]
        
    def initialize(self) -> bool:
        """Initialize the Gemini provider."""
        try:
            # Initialize VertexAI with current configuration
            initialize_vertexai()
            
            # Set model name from config or use default
            self.model_name = self.config.get("model", "gemini-2.0-flash-exp")
            
            # Create the model instance
            self.model = GenerativeModel(
                model_name=self.model_name,
                safety_settings=SAFETY_SETTING,
                generation_config=GenerationConfig(
                    temperature=self.config.get("temperature", 0.4),
                    top_p=self.config.get("top_p", 0.95),
                    top_k=self.config.get("top_k", 40)
                )
            )
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            self.is_initialized = False
            return False
    
    def translate(self, text: str, source_lang: str = "Japanese", 
                 instructions: Optional[List[str]] = None,
                 glossary_text: Optional[str] = None,
                 max_retries: int = 3) -> TranslationResult:
        """Translate text using Gemini."""
        if not self.is_initialized:
            return self.create_error_result("Provider not initialized")
        
        # Build the prompt
        prompt_parts = []
        if instructions:
            prompt_parts.extend(instructions)
        if glossary_text:
            prompt_parts.append(glossary_text)
        prompt_parts.append(text)
        
        full_prompt = "\n\n".join(prompt_parts)
        
        # Attempt translation with retries
        for attempt in range(max_retries):
            try:
                # Add rate limiting delay
                if attempt > 0:
                    delay = self.handle_rate_limit(attempt - 1)
                    time.sleep(delay)
                
                response = self.model.generate_content(full_prompt)
                
                if response and response.text:
                    return TranslationResult(
                        text=response.text.strip(),
                        success=True,
                        provider=self.get_provider_name(),
                        model=self.get_model_name()
                    )
                else:
                    error_msg = "Empty response from Gemini"
                    if attempt == max_retries - 1:
                        return self.create_error_result(error_msg)
                    
            except Exception as e:
                error_msg = f"Gemini API error: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                
        return self.create_error_result("Max retries exceeded")
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported Gemini models."""
        return self.available_models.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Gemini provider configuration."""
        required_fields = ["project_id", "location"]
        
        for field in required_fields:
            if field not in config or not config[field]:
                return False
        
        # Validate model if specified
        if "model" in config:
            if config["model"] not in self.available_models:
                return False
        
        # Validate numeric parameters
        numeric_params = {
            "temperature": (0.0, 2.0),
            "top_p": (0.0, 1.0),
            "top_k": (1, 100)
        }
        
        for param, (min_val, max_val) in numeric_params.items():
            if param in config:
                try:
                    value = float(config[param])
                    if not (min_val <= value <= max_val):
                        return False
                except (ValueError, TypeError):
                    return False
        
        return True
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for Gemini provider."""
        return {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "Google Cloud Project ID",
                    "required": True
                },
                "location": {
                    "type": "string",
                    "description": "Google Cloud region (e.g., us-central1)",
                    "required": True,
                    "default": "us-central1"
                },
                "service_account_path": {
                    "type": "string",
                    "description": "Path to service account JSON file",
                    "required": False
                },
                "model": {
                    "type": "string",
                    "description": "Gemini model to use",
                    "enum": self.available_models,
                    "default": "gemini-2.0-flash-exp"
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature (0.0-2.0)",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.4
                },
                "top_p": {
                    "type": "number",
                    "description": "Top-p sampling parameter (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.95
                },
                "top_k": {
                    "type": "integer",
                    "description": "Top-k sampling parameter (1-100)",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 40
                }
            }
        }
