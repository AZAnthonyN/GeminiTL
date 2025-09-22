"""
Multi-provider configuration system.

This module handles configuration for multiple AI providers,
extending the existing configuration system.
"""

import os
import json
from typing import Dict, Any, Optional, List


class MultiProviderConfig:
    """Configuration manager for multiple AI providers."""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__))
        self.config_file = os.path.join(self.config_dir, "providers_config.json")
        self.legacy_config_file = os.path.join(self.config_dir, "config.txt")
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        # Try to load from new JSON config first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                return
            except Exception as e:
                print(f"[CONFIG] Error loading providers config: {e}")
        
        # Fall back to legacy config and migrate
        self._migrate_legacy_config()
    
    def _migrate_legacy_config(self):
        """Migrate from legacy config.txt format."""
        legacy_config = {}
        if os.path.exists(self.legacy_config_file):
            try:
                with open(self.legacy_config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            legacy_config[key.strip()] = value.strip()
            except Exception as e:
                print(f"[CONFIG] Error reading legacy config: {e}")
        
        # Create new config structure with legacy Gemini settings
        self._config = {
            "default_provider": "gemini",
            "providers": {
                "gemini": {
                    "enabled": True,
                    "project_id": legacy_config.get("PROJECT_ID", ""),
                    "location": legacy_config.get("LOCATION", "us-central1"),
                    "login_key": legacy_config.get("LOGIN_KEY", ""),
                    "model": "gemini-2.0-flash-exp",
                    "temperature": 0.4,
                    "top_p": 0.95,
                    "top_k": 40
                },
                "openai": {
                    "enabled": False,
                    "api_key": "",
                    "model": "gpt-4o-mini",
                    "temperature": 0.4,
                    "top_p": 0.95,
                    "max_tokens": 4000
                },
                "anthropic": {
                    "enabled": False,
                    "api_key": "",
                    "model": "claude-3-5-haiku-20241022",
                    "temperature": 0.4,
                    "top_p": 0.95,
                    "max_tokens": 4000
                }
            },
            "fallback_providers": ["gemini", "openai", "anthropic"],
            "retry_settings": {
                "max_retries": 3,
                "base_delay": 1.0,
                "exponential_backoff": True
            }
        }
        
        # Save the migrated config
        self.save_config()
    
    def save_config(self):
        """Save configuration to file."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            print(f"[CONFIG] Error saving config: {e}")
    
    def get_default_provider(self) -> str:
        """Get the default provider name."""
        return self._config.get("default_provider", "gemini")
    
    def set_default_provider(self, provider_name: str):
        """Set the default provider."""
        if provider_name in self._config.get("providers", {}):
            self._config["default_provider"] = provider_name
            self.save_config()
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider."""
        providers = self._config.get("providers", {})
        return providers.get(provider_name, {})
    
    def set_provider_config(self, provider_name: str, config: Dict[str, Any]):
        """Set configuration for a specific provider."""
        if "providers" not in self._config:
            self._config["providers"] = {}
        self._config["providers"][provider_name] = config
        self.save_config()
    
    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled."""
        provider_config = self.get_provider_config(provider_name)
        return provider_config.get("enabled", False)
    
    def enable_provider(self, provider_name: str, enabled: bool = True):
        """Enable or disable a provider."""
        if "providers" not in self._config:
            self._config["providers"] = {}
        if provider_name not in self._config["providers"]:
            self._config["providers"][provider_name] = {}
        
        self._config["providers"][provider_name]["enabled"] = enabled
        self.save_config()
    
    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names."""
        enabled = []
        providers = self._config.get("providers", {})
        for name, config in providers.items():
            if config.get("enabled", False):
                enabled.append(name)
        return enabled
    
    def get_fallback_providers(self) -> List[str]:
        """Get list of fallback providers in order."""
        fallbacks = self._config.get("fallback_providers", [])
        # Filter to only include enabled providers
        enabled = self.get_enabled_providers()
        return [p for p in fallbacks if p in enabled]
    
    def set_fallback_providers(self, providers: List[str]):
        """Set the fallback provider order."""
        self._config["fallback_providers"] = providers
        self.save_config()
    
    def get_retry_settings(self) -> Dict[str, Any]:
        """Get retry settings."""
        return self._config.get("retry_settings", {
            "max_retries": 3,
            "base_delay": 1.0,
            "exponential_backoff": True
        })
    
    def set_retry_settings(self, settings: Dict[str, Any]):
        """Set retry settings."""
        self._config["retry_settings"] = settings
        self.save_config()
    
    def validate_provider_config(self, provider_name: str) -> bool:
        """Validate configuration for a specific provider."""
        try:
            # Import here to avoid circular imports
            from ai_providers.base_provider import ProviderType
            from ai_providers.provider_factory import ProviderFactory

            provider_type = ProviderType(provider_name)
            provider = ProviderFactory.create_provider(provider_type, {})
            if provider:
                config = self.get_provider_config(provider_name)
                return provider.validate_config(config)
        except (ValueError, AttributeError):
            pass
        return False
    
    def get_all_provider_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration schemas for all available providers."""
        schemas = {}
        for provider_type in ProviderFactory.get_available_providers():
            provider = ProviderFactory.create_provider(provider_type, {})
            if provider:
                schemas[provider_type.value] = provider.get_config_schema()
        return schemas


# Global configuration instance
config_manager = MultiProviderConfig()
