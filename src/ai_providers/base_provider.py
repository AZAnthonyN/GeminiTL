"""
Abstract base class for AI translation providers.

This module defines the interface that all AI providers must implement
to work with the translation system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import time


class ProviderType(Enum):
    """Enumeration of supported AI providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"


class TranslationResult:
    """Container for translation results with metadata."""
    
    def __init__(self, text: str, success: bool = True, error: Optional[str] = None, 
                 provider: Optional[str] = None, model: Optional[str] = None,
                 tokens_used: Optional[int] = None, cost: Optional[float] = None):
        self.text = text
        self.success = success
        self.error = error
        self.provider = provider
        self.model = model
        self.tokens_used = tokens_used
        self.cost = cost
        self.timestamp = time.time()


class BaseAIProvider(ABC):
    """
    Abstract base class for AI translation providers.
    
    All AI providers must inherit from this class and implement the required methods.
    This ensures a consistent interface across different AI services.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI provider with configuration.
        
        Args:
            config: Dictionary containing provider-specific configuration
        """
        self.config = config
        self.provider_type = None
        self.model_name = None
        self.is_initialized = False
        self.rate_limit_delay = 1.0  # Default delay between requests
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        Initialize the provider with the given configuration.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    def translate(self, text: str, source_lang: str = "Japanese", 
                 instructions: Optional[List[str]] = None,
                 glossary_text: Optional[str] = None,
                 max_retries: int = 3) -> TranslationResult:
        """
        Translate text using the AI provider.
        
        Args:
            text: Text to translate
            source_lang: Source language (default: Japanese)
            instructions: List of translation instructions/prompts
            glossary_text: Glossary text to use for translation
            max_retries: Maximum number of retry attempts
            
        Returns:
            TranslationResult: Result containing translated text and metadata
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models for this provider.
        
        Returns:
            List[str]: List of model names
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate the provider configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get the configuration schema for this provider.
        
        Returns:
            Dict[str, Any]: Schema describing required and optional config fields
        """
        pass
    
    def get_provider_name(self) -> str:
        """Get the human-readable name of this provider."""
        return self.provider_type.value if self.provider_type else "Unknown"
    
    def get_model_name(self) -> str:
        """Get the current model name."""
        return self.model_name or "Unknown"
    
    def is_ready(self) -> bool:
        """Check if the provider is ready for use."""
        return self.is_initialized
    
    def set_rate_limit_delay(self, delay: float):
        """Set the delay between API requests for rate limiting."""
        self.rate_limit_delay = max(0.1, delay)
    
    def handle_rate_limit(self, retry_count: int = 0) -> float:
        """
        Calculate delay for rate limiting with exponential backoff.
        
        Args:
            retry_count: Current retry attempt number
            
        Returns:
            float: Delay in seconds
        """
        base_delay = self.rate_limit_delay
        exponential_delay = base_delay * (2 ** retry_count)
        return min(exponential_delay, 60.0)  # Cap at 60 seconds
    
    def create_error_result(self, error_message: str) -> TranslationResult:
        """
        Create a TranslationResult for an error condition.
        
        Args:
            error_message: Description of the error
            
        Returns:
            TranslationResult: Result object with error information
        """
        return TranslationResult(
            text="",
            success=False,
            error=error_message,
            provider=self.get_provider_name(),
            model=self.get_model_name()
        )
