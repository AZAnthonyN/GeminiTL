"""
OpenAI provider implementation.

This module provides integration with OpenAI's GPT models for translation services.
"""

import time
import json
from typing import Dict, Any, Optional, List

from .base_provider import BaseAIProvider, ProviderType, TranslationResult

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIProvider(BaseAIProvider):
    """OpenAI provider for translation services."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = ProviderType.OPENAI
        self.client = None
        self.available_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
        
    def initialize(self) -> bool:
        """Initialize the OpenAI provider."""
        if not OPENAI_AVAILABLE:
            return False
            
        try:
            api_key = self.config.get("api_key")
            if not api_key:
                return False
            
            # Initialize OpenAI client
            self.client = openai.OpenAI(api_key=api_key)
            
            # Set model name from config or use default
            self.model_name = self.config.get("model", "gpt-4o-mini")
            
            # Test the connection with a simple request
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=1
                )
                self.is_initialized = True
                return True
            except Exception:
                return False
                
        except Exception:
            self.is_initialized = False
            return False
    
    def translate(self, text: str, source_lang: str = "Japanese", 
                 instructions: Optional[List[str]] = None,
                 glossary_text: Optional[str] = None,
                 max_retries: int = 3) -> TranslationResult:
        """Translate text using OpenAI GPT models."""
        if not self.is_initialized:
            return self.create_error_result("Provider not initialized")
        
        # Build the system message
        system_parts = []
        if instructions:
            system_parts.extend(instructions)
        if glossary_text:
            system_parts.append(f"Use this glossary for translation:\n{glossary_text}")
        
        system_message = "\n\n".join(system_parts) if system_parts else f"Translate the following {source_lang} text to English."
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": text}
        ]
        
        # Attempt translation with retries
        for attempt in range(max_retries):
            try:
                # Add rate limiting delay
                if attempt > 0:
                    delay = self.handle_rate_limit(attempt - 1)
                    time.sleep(delay)
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=self.config.get("temperature", 0.4),
                    max_tokens=self.config.get("max_tokens", 4000),
                    top_p=self.config.get("top_p", 0.95)
                )
                
                if response.choices and response.choices[0].message.content:
                    translated_text = response.choices[0].message.content.strip()
                    
                    # Calculate token usage and cost (approximate)
                    tokens_used = response.usage.total_tokens if response.usage else None
                    cost = self._calculate_cost(tokens_used) if tokens_used else None
                    
                    return TranslationResult(
                        text=translated_text,
                        success=True,
                        provider=self.get_provider_name(),
                        model=self.get_model_name(),
                        tokens_used=tokens_used,
                        cost=cost
                    )
                else:
                    error_msg = "Empty response from OpenAI"
                    if attempt == max_retries - 1:
                        return self.create_error_result(error_msg)
                    
            except openai.RateLimitError as e:
                error_msg = f"OpenAI rate limit exceeded: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                # Wait longer for rate limit errors
                time.sleep(self.handle_rate_limit(attempt) * 2)
                
            except openai.APIError as e:
                error_msg = f"OpenAI API error: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                    
            except Exception as e:
                error_msg = f"OpenAI error: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                
        return self.create_error_result("Max retries exceeded")
    
    def _calculate_cost(self, tokens: int) -> float:
        """Calculate approximate cost based on token usage."""
        # Approximate pricing (as of 2024) - should be updated regularly
        pricing = {
            "gpt-4o": {"input": 0.005, "output": 0.015},  # per 1K tokens
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
        }
        
        if self.model_name in pricing:
            # Rough estimate assuming 70% input, 30% output
            input_tokens = int(tokens * 0.7)
            output_tokens = int(tokens * 0.3)
            
            input_cost = (input_tokens / 1000) * pricing[self.model_name]["input"]
            output_cost = (output_tokens / 1000) * pricing[self.model_name]["output"]
            
            return input_cost + output_cost
        
        return 0.0
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported OpenAI models."""
        return self.available_models.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate OpenAI provider configuration."""
        # API key is required
        if "api_key" not in config or not config["api_key"]:
            return False
        
        # Validate model if specified
        if "model" in config:
            if config["model"] not in self.available_models:
                return False
        
        # Validate numeric parameters
        numeric_params = {
            "temperature": (0.0, 2.0),
            "top_p": (0.0, 1.0),
            "max_tokens": (1, 8000)
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
        """Get configuration schema for OpenAI provider."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "OpenAI API key",
                    "required": True
                },
                "model": {
                    "type": "string",
                    "description": "OpenAI model to use",
                    "enum": self.available_models,
                    "default": "gpt-4o-mini"
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
                "max_tokens": {
                    "type": "integer",
                    "description": "Maximum tokens in response (1-8000)",
                    "minimum": 1,
                    "maximum": 8000,
                    "default": 4000
                }
            }
        }
