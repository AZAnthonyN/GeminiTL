"""
Factory for creating AI provider instances.

This module provides a centralized way to create and manage AI provider instances
based on configuration settings.
"""

from typing import Dict, Any, Optional, List
from .base_provider import BaseAIProvider, ProviderType


class ProviderFactory:
    """Factory class for creating AI provider instances."""
    
    _providers = {}  # Registry of available providers
    
    @classmethod
    def register_provider(cls, provider_type: ProviderType, provider_class):
        """
        Register a provider class with the factory.
        
        Args:
            provider_type: Type of provider to register
            provider_class: Class that implements BaseAIProvider
        """
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def create_provider(cls, provider_type: ProviderType, config: Dict[str, Any]) -> Optional[BaseAIProvider]:
        """
        Create a provider instance of the specified type.
        
        Args:
            provider_type: Type of provider to create
            config: Configuration for the provider
            
        Returns:
            BaseAIProvider: Provider instance, or None if type not supported
        """
        if provider_type not in cls._providers:
            return None
            
        provider_class = cls._providers[provider_type]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[ProviderType]:
        """
        Get list of available provider types.
        
        Returns:
            List[ProviderType]: List of registered provider types
        """
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_names(cls) -> List[str]:
        """
        Get list of available provider names.
        
        Returns:
            List[str]: List of provider names
        """
        return [provider_type.value for provider_type in cls._providers.keys()]
    
    @classmethod
    def is_provider_available(cls, provider_type: ProviderType) -> bool:
        """
        Check if a provider type is available.
        
        Args:
            provider_type: Provider type to check
            
        Returns:
            bool: True if provider is available, False otherwise
        """
        return provider_type in cls._providers


# Auto-register providers when they're imported
def _auto_register_providers():
    """Automatically register available providers."""
    try:
        from .gemini_provider import GeminiProvider
        ProviderFactory.register_provider(ProviderType.GEMINI, GeminiProvider)
    except ImportError:
        pass
    
    try:
        from .openai_provider import OpenAIProvider
        ProviderFactory.register_provider(ProviderType.OPENAI, OpenAIProvider)
    except ImportError:
        pass
    
    try:
        from .anthropic_provider import AnthropicProvider
        ProviderFactory.register_provider(ProviderType.ANTHROPIC, AnthropicProvider)
    except ImportError:
        pass


# Register providers on module import
_auto_register_providers()
