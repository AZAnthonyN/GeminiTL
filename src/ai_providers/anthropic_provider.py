"""
Anthropic provider implementation.

This module provides integration with Anthropic's Claude models for translation services.
"""

import time
import json
from typing import Dict, Any, Optional, List

from .base_provider import BaseAIProvider, ProviderType, TranslationResult

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class AnthropicProvider(BaseAIProvider):
    """Anthropic provider for translation services."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.provider_type = ProviderType.ANTHROPIC
        self.client = None
        self.available_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
        
    def initialize(self) -> bool:
        """Initialize the Anthropic provider."""
        if not ANTHROPIC_AVAILABLE:
            return False
            
        try:
            api_key = self.config.get("api_key")
            if not api_key:
                return False
            
            # Initialize Anthropic client
            self.client = anthropic.Anthropic(api_key=api_key)
            
            # Set model name from config or use default
            self.model_name = self.config.get("model", "claude-3-5-haiku-20241022")
            
            # Test the connection with a simple request
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1,
                    messages=[{"role": "user", "content": "Test"}]
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
        """Translate text using Anthropic Claude models."""
        if not self.is_initialized:
            return self.create_error_result("Provider not initialized")
        
        # Build the system message
        system_parts = []
        if instructions:
            system_parts.extend(instructions)
        if glossary_text:
            system_parts.append(f"Use this glossary for translation:\n{glossary_text}")
        
        system_message = "\n\n".join(system_parts) if system_parts else f"Translate the following {source_lang} text to English."
        
        messages = [{"role": "user", "content": text}]
        
        # Attempt translation with retries
        for attempt in range(max_retries):
            try:
                # Add rate limiting delay
                if attempt > 0:
                    delay = self.handle_rate_limit(attempt - 1)
                    time.sleep(delay)
                
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.config.get("max_tokens", 4000),
                    temperature=self.config.get("temperature", 0.4),
                    top_p=self.config.get("top_p", 0.95),
                    system=system_message,
                    messages=messages
                )
                
                if response.content and len(response.content) > 0:
                    translated_text = response.content[0].text.strip()
                    
                    # Calculate token usage and cost (approximate)
                    tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else None
                    cost = self._calculate_cost(response.usage.input_tokens, response.usage.output_tokens) if response.usage else None
                    
                    return TranslationResult(
                        text=translated_text,
                        success=True,
                        provider=self.get_provider_name(),
                        model=self.get_model_name(),
                        tokens_used=tokens_used,
                        cost=cost
                    )
                else:
                    error_msg = "Empty response from Anthropic"
                    if attempt == max_retries - 1:
                        return self.create_error_result(error_msg)
                    
            except anthropic.RateLimitError as e:
                error_msg = f"Anthropic rate limit exceeded: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                # Wait longer for rate limit errors
                time.sleep(self.handle_rate_limit(attempt) * 2)
                
            except anthropic.APIError as e:
                error_msg = f"Anthropic API error: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                    
            except Exception as e:
                error_msg = f"Anthropic error: {str(e)}"
                if attempt == max_retries - 1:
                    return self.create_error_result(error_msg)
                
        return self.create_error_result("Max retries exceeded")
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate approximate cost based on token usage."""
        # Approximate pricing (as of 2024) - should be updated regularly
        pricing = {
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},  # per 1K tokens
            "claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
        }
        
        if self.model_name in pricing:
            input_cost = (input_tokens / 1000) * pricing[self.model_name]["input"]
            output_cost = (output_tokens / 1000) * pricing[self.model_name]["output"]
            return input_cost + output_cost
        
        return 0.0
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported Anthropic models."""
        return self.available_models.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Anthropic provider configuration."""
        # API key is required
        if "api_key" not in config or not config["api_key"]:
            return False
        
        # Validate model if specified
        if "model" in config:
            if config["model"] not in self.available_models:
                return False
        
        # Validate numeric parameters
        numeric_params = {
            "temperature": (0.0, 1.0),
            "top_p": (0.0, 1.0),
            "max_tokens": (1, 8192)
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
        """Get configuration schema for Anthropic provider."""
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Anthropic API key",
                    "required": True
                },
                "model": {
                    "type": "string",
                    "description": "Anthropic model to use",
                    "enum": self.available_models,
                    "default": "claude-3-5-haiku-20241022"
                },
                "temperature": {
                    "type": "number",
                    "description": "Sampling temperature (0.0-1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0,
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
                    "description": "Maximum tokens in response (1-8192)",
                    "minimum": 1,
                    "maximum": 8192,
                    "default": 4000
                }
            }
        }
