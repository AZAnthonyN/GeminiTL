"""
Provider manager for handling multiple AI providers.

This module manages the lifecycle and usage of multiple AI providers,
including fallback logic and provider switching.
"""

import time
from typing import Dict, Any, Optional, List
from .base_provider import BaseAIProvider, ProviderType, TranslationResult
from .provider_factory import ProviderFactory
from config.multi_provider_config import config_manager


class ProviderManager:
    """Manages multiple AI providers with fallback support."""
    
    def __init__(self):
        self.providers: Dict[str, BaseAIProvider] = {}
        self.initialized_providers: Dict[str, bool] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all enabled providers."""
        enabled_providers = config_manager.get_enabled_providers()
        
        for provider_name in enabled_providers:
            try:
                provider_type = ProviderType(provider_name)
                provider_config = config_manager.get_provider_config(provider_name)
                
                provider = ProviderFactory.create_provider(provider_type, provider_config)
                if provider:
                    self.providers[provider_name] = provider
                    self.initialized_providers[provider_name] = provider.initialize()
                    
                    if self.initialized_providers[provider_name]:
                        print(f"[PROVIDER] {provider_name} initialized successfully")
                    else:
                        print(f"[PROVIDER] {provider_name} failed to initialize")
                        
            except (ValueError, Exception) as e:
                print(f"[PROVIDER] Error initializing {provider_name}: {e}")
                self.initialized_providers[provider_name] = False
    
    def get_available_providers(self) -> List[str]:
        """Get list of available and initialized providers."""
        return [name for name, initialized in self.initialized_providers.items() if initialized]
    
    def get_provider(self, provider_name: str) -> Optional[BaseAIProvider]:
        """Get a specific provider instance."""
        if provider_name in self.providers and self.initialized_providers.get(provider_name, False):
            return self.providers[provider_name]
        return None
    
    def translate_with_fallback(self, text: str, source_lang: str = "Japanese",
                              instructions: Optional[List[str]] = None,
                              glossary_text: Optional[str] = None,
                              preferred_provider: Optional[str] = None) -> TranslationResult:
        """
        Translate text with automatic fallback to other providers if the primary fails.
        
        Args:
            text: Text to translate
            source_lang: Source language
            instructions: Translation instructions
            glossary_text: Glossary text
            preferred_provider: Preferred provider name (overrides default)
            
        Returns:
            TranslationResult: Translation result with provider information
        """
        # Determine provider order
        if preferred_provider and preferred_provider in self.get_available_providers():
            provider_order = [preferred_provider]
            # Add fallback providers, excluding the preferred one
            fallbacks = [p for p in config_manager.get_fallback_providers() if p != preferred_provider]
            provider_order.extend(fallbacks)
        else:
            # Use default provider order
            default_provider = config_manager.get_default_provider()
            if default_provider in self.get_available_providers():
                provider_order = [default_provider]
                fallbacks = [p for p in config_manager.get_fallback_providers() if p != default_provider]
                provider_order.extend(fallbacks)
            else:
                provider_order = config_manager.get_fallback_providers()
        
        # Filter to only available providers
        provider_order = [p for p in provider_order if p in self.get_available_providers()]
        
        if not provider_order:
            return TranslationResult(
                text="",
                success=False,
                error="No available providers",
                provider="None"
            )
        
        retry_settings = config_manager.get_retry_settings()
        last_error = "Unknown error"
        
        # Try each provider in order
        for i, provider_name in enumerate(provider_order):
            provider = self.get_provider(provider_name)
            if not provider:
                continue

            print(f"[PROVIDER] Attempting translation with {provider_name} (attempt {i+1}/{len(provider_order)})")

            result = provider.translate(
                text=text,
                source_lang=source_lang,
                instructions=instructions,
                glossary_text=glossary_text,
                max_retries=retry_settings.get("max_retries", 3)
            )

            if result.success:
                print(f"[PROVIDER] Translation successful with {provider_name}")
                return result
            else:
                print(f"[PROVIDER] Translation failed with {provider_name}: {result.error}")
                last_error = result.error

                # Intelligent delay based on error type and provider position
                if i < len(provider_order) - 1:  # Not the last provider
                    delay = self._calculate_fallback_delay(result.error, i, retry_settings)
                    if delay > 0:
                        print(f"[PROVIDER] Waiting {delay:.1f}s before trying next provider...")
                        time.sleep(delay)
        
        # All providers failed
        return TranslationResult(
            text="",
            success=False,
            error=f"All providers failed. Last error: {last_error}",
            provider="Multiple"
        )
    
    def translate(self, text: str, source_lang: str = "Japanese",
                 instructions: Optional[List[str]] = None,
                 glossary_text: Optional[str] = None,
                 provider_name: Optional[str] = None) -> TranslationResult:
        """
        Translate text using a specific provider or the default.
        
        Args:
            text: Text to translate
            source_lang: Source language
            instructions: Translation instructions
            glossary_text: Glossary text
            provider_name: Specific provider to use (optional)
            
        Returns:
            TranslationResult: Translation result
        """
        if provider_name:
            # Use specific provider without fallback
            provider = self.get_provider(provider_name)
            if provider:
                retry_settings = config_manager.get_retry_settings()
                return provider.translate(
                    text=text,
                    source_lang=source_lang,
                    instructions=instructions,
                    glossary_text=glossary_text,
                    max_retries=retry_settings.get("max_retries", 3)
                )
            else:
                return TranslationResult(
                    text="",
                    success=False,
                    error=f"Provider {provider_name} not available",
                    provider=provider_name
                )
        else:
            # Use fallback logic
            return self.translate_with_fallback(
                text=text,
                source_lang=source_lang,
                instructions=instructions,
                glossary_text=glossary_text
            )
    
    def reinitialize_provider(self, provider_name: str) -> bool:
        """Reinitialize a specific provider."""
        if provider_name in self.providers:
            provider_config = config_manager.get_provider_config(provider_name)
            self.providers[provider_name].config = provider_config
            self.initialized_providers[provider_name] = self.providers[provider_name].initialize()
            return self.initialized_providers[provider_name]
        return False
    
    def reinitialize_all_providers(self):
        """Reinitialize all providers."""
        self.providers.clear()
        self.initialized_providers.clear()
        self._initialize_providers()
    
    def _calculate_fallback_delay(self, error_message: str, attempt_number: int,
                                retry_settings: Dict[str, Any]) -> float:
        """
        Calculate intelligent delay before trying next provider.

        Args:
            error_message: Error message from failed provider (can be None)
            attempt_number: Which attempt this is (0-based)
            retry_settings: Retry configuration

        Returns:
            Delay in seconds
        """
        base_delay = retry_settings.get("base_delay", 1.0)

        # Handle None error message
        if not error_message:
            error_message = ""

        error_lower = error_message.lower()

        # Longer delays for rate limiting errors
        if any(term in error_lower for term in ["rate limit", "quota", "throttle"]):
            return base_delay * 3.0 * (attempt_number + 1)

        # Shorter delays for authentication/config errors (likely won't resolve)
        if any(term in error_lower for term in ["auth", "key", "credential", "permission"]):
            return base_delay * 0.5

        # Medium delays for API errors
        if any(term in error_lower for term in ["api", "server", "network", "timeout"]):
            return base_delay * 2.0

        # Default exponential backoff
        if retry_settings.get("exponential_backoff", True):
            return base_delay * (2 ** attempt_number)

        return base_delay

    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all providers."""
        status = {}
        for provider_name in config_manager.get_enabled_providers():
            provider = self.providers.get(provider_name)
            status[provider_name] = {
                "enabled": config_manager.is_provider_enabled(provider_name),
                "initialized": self.initialized_providers.get(provider_name, False),
                "available": provider is not None and provider.is_ready(),
                "model": provider.get_model_name() if provider else "Unknown"
            }
        return status


# Global provider manager instance
provider_manager = ProviderManager()
