"""
Test suite for the multi-provider system.

This module provides tests to validate the provider system functionality.
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from ai_providers.base_provider import BaseAIProvider, ProviderType, TranslationResult
    from ai_providers.provider_factory import ProviderFactory
    from ai_providers.provider_manager import ProviderManager
    from config.multi_provider_config import MultiProviderConfig
    from translation.provider_prompt_templates import ProviderPromptTemplates
    PROVIDERS_AVAILABLE = True
except ImportError as e:
    print(f"Provider system not available: {e}")
    PROVIDERS_AVAILABLE = False


class MockProvider(BaseAIProvider):
    """Mock provider for testing."""
    
    def __init__(self, config, should_fail=False):
        super().__init__(config)
        self.provider_type = ProviderType.GEMINI
        self.model_name = "mock-model"
        self.should_fail = should_fail
    
    def initialize(self) -> bool:
        self.is_initialized = not self.should_fail
        return self.is_initialized
    
    def translate(self, text, source_lang="Japanese", instructions=None, 
                 glossary_text=None, max_retries=3) -> TranslationResult:
        if self.should_fail:
            return self.create_error_result("Mock failure")
        
        return TranslationResult(
            text=f"Translated: {text}",
            success=True,
            provider="mock",
            model="mock-model"
        )
    
    def get_supported_models(self):
        return ["mock-model"]
    
    def validate_config(self, config):
        return True
    
    def get_config_schema(self):
        return {"type": "object", "properties": {}}


@unittest.skipUnless(PROVIDERS_AVAILABLE, "Provider system not available")
class TestProviderSystem(unittest.TestCase):
    """Test cases for the provider system."""
    
    def test_translation_result(self):
        """Test TranslationResult creation."""
        result = TranslationResult(
            text="Hello world",
            success=True,
            provider="test",
            model="test-model"
        )
        
        self.assertEqual(result.text, "Hello world")
        self.assertTrue(result.success)
        self.assertEqual(result.provider, "test")
        self.assertEqual(result.model, "test-model")
        self.assertIsNotNone(result.timestamp)
    
    def test_mock_provider(self):
        """Test mock provider functionality."""
        provider = MockProvider({})
        self.assertTrue(provider.initialize())
        
        result = provider.translate("Hello")
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Translated: Hello")
    
    def test_mock_provider_failure(self):
        """Test mock provider failure handling."""
        provider = MockProvider({}, should_fail=True)
        self.assertFalse(provider.initialize())
        
        result = provider.translate("Hello")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "Mock failure")
    
    def test_provider_factory_registration(self):
        """Test provider factory registration."""
        # Register mock provider
        ProviderFactory.register_provider(ProviderType.GEMINI, MockProvider)
        
        # Check if registered
        self.assertIn(ProviderType.GEMINI, ProviderFactory.get_available_providers())
        
        # Create provider
        provider = ProviderFactory.create_provider(ProviderType.GEMINI, {})
        self.assertIsInstance(provider, MockProvider)
    
    def test_config_manager(self):
        """Test configuration manager."""
        config_manager = MultiProviderConfig()
        
        # Test default provider
        default = config_manager.get_default_provider()
        self.assertIsInstance(default, str)
        
        # Test provider config
        config = config_manager.get_provider_config("gemini")
        self.assertIsInstance(config, dict)
        
        # Test enabled providers
        enabled = config_manager.get_enabled_providers()
        self.assertIsInstance(enabled, list)
    
    def test_prompt_templates(self):
        """Test provider-specific prompt templates."""
        # Test Gemini prompts
        gemini_prompt = ProviderPromptTemplates.get_translation_prompt("Japanese", "gemini")
        self.assertIsInstance(gemini_prompt, str)
        self.assertIn("Japanese", gemini_prompt)
        
        # Test OpenAI prompts
        openai_prompt = ProviderPromptTemplates.get_translation_prompt("Japanese", "openai")
        self.assertIsInstance(openai_prompt, str)
        self.assertIn("Japanese", openai_prompt)
        
        # Test Anthropic prompts
        anthropic_prompt = ProviderPromptTemplates.get_translation_prompt("Japanese", "anthropic")
        self.assertIsInstance(anthropic_prompt, str)
        self.assertIn("Japanese", anthropic_prompt)
        
        # Prompts should be different for different providers
        self.assertNotEqual(gemini_prompt, openai_prompt)
        self.assertNotEqual(openai_prompt, anthropic_prompt)
    
    def test_fallback_prompts(self):
        """Test fallback prompt generation."""
        fallback = ProviderPromptTemplates.get_fallback_prompt("Japanese", "gemini")
        self.assertIsInstance(fallback, str)
        self.assertIn("Japanese", fallback)
    
    @patch('ai_providers.provider_manager.config_manager')
    def test_provider_manager_fallback(self, mock_config):
        """Test provider manager fallback logic."""
        # Mock configuration
        mock_config.get_enabled_providers.return_value = ["mock1", "mock2"]
        mock_config.get_default_provider.return_value = "mock1"
        mock_config.get_fallback_providers.return_value = ["mock1", "mock2"]
        mock_config.get_retry_settings.return_value = {
            "max_retries": 3,
            "base_delay": 1.0,
            "exponential_backoff": True
        }
        
        # Create manager with mock providers
        manager = ProviderManager()
        manager.providers = {
            "mock1": MockProvider({}, should_fail=True),
            "mock2": MockProvider({})
        }
        manager.initialized_providers = {"mock1": True, "mock2": True}
        
        # Test fallback
        result = manager.translate_with_fallback("Hello")
        self.assertTrue(result.success)
        self.assertEqual(result.text, "Translated: Hello")


class TestProviderIntegration(unittest.TestCase):
    """Integration tests for the provider system."""
    
    @unittest.skipUnless(PROVIDERS_AVAILABLE, "Provider system not available")
    def test_multi_provider_translator_import(self):
        """Test that multi-provider translator can be imported."""
        try:
            from translation.multi_provider_translator import MultiProviderTranslator
            translator = MultiProviderTranslator()
            self.assertIsNotNone(translator)
        except ImportError:
            self.skipTest("Multi-provider translator not available")
    
    def test_legacy_compatibility(self):
        """Test that legacy translator still works."""
        try:
            from translation.translator import Translator
            translator = Translator()
            self.assertIsNotNone(translator)
        except ImportError:
            self.fail("Legacy translator should still be available")


def run_provider_tests():
    """Run all provider tests."""
    if not PROVIDERS_AVAILABLE:
        print("Provider system not available. Skipping tests.")
        return False

    # Create test suite
    suite = unittest.TestSuite()

    # Add test cases using TestLoader (compatible with all Python versions)
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestProviderSystem))
    suite.addTests(loader.loadTestsFromTestCase(TestProviderIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_provider_tests()
    sys.exit(0 if success else 1)
