#!/usr/bin/env python3
"""
Provider system validation script.

This script validates that the multi-provider system is working correctly
and provides diagnostic information.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

def check_imports():
    """Check if all required modules can be imported."""
    print("=== Checking Imports ===")
    
    imports_to_check = [
        ("ai_providers.base_provider", ["BaseAIProvider", "ProviderType", "TranslationResult"]),
        ("ai_providers.provider_factory", ["ProviderFactory"]),
        ("ai_providers.provider_manager", ["ProviderManager", "provider_manager"]),
        ("config.multi_provider_config", ["MultiProviderConfig", "config_manager"]),
        ("translation.provider_prompt_templates", ["ProviderPromptTemplates"]),
        ("translation.multi_provider_translator", ["MultiProviderTranslator"]),
    ]
    
    all_good = True
    for module_name, items in imports_to_check:
        try:
            module = __import__(module_name, fromlist=items)
            for item in items:
                if hasattr(module, item):
                    print(f"✓ {module_name}.{item}")
                else:
                    print(f"✗ {module_name}.{item} - not found")
                    all_good = False
        except ImportError as e:
            print(f"✗ {module_name} - import failed: {e}")
            all_good = False
    
    return all_good

def check_provider_factory():
    """Check provider factory functionality."""
    print("\n=== Checking Provider Factory ===")
    
    try:
        from ai_providers.provider_factory import ProviderFactory
        from ai_providers.base_provider import ProviderType
        
        available = ProviderFactory.get_available_providers()
        print(f"Available provider types: {[p.value for p in available]}")
        
        provider_names = ProviderFactory.get_provider_names()
        print(f"Available provider names: {provider_names}")
        
        # Try to create each provider
        for provider_type in available:
            try:
                provider = ProviderFactory.create_provider(provider_type, {})
                if provider:
                    print(f"✓ {provider_type.value} provider created successfully")
                else:
                    print(f"✗ {provider_type.value} provider creation returned None")
            except Exception as e:
                print(f"✗ {provider_type.value} provider creation failed: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Provider factory check failed: {e}")
        return False

def check_configuration():
    """Check configuration system."""
    print("\n=== Checking Configuration ===")
    
    try:
        from config.multi_provider_config import config_manager
        
        default_provider = config_manager.get_default_provider()
        print(f"Default provider: {default_provider}")
        
        enabled_providers = config_manager.get_enabled_providers()
        print(f"Enabled providers: {enabled_providers}")
        
        fallback_providers = config_manager.get_fallback_providers()
        print(f"Fallback order: {fallback_providers}")
        
        retry_settings = config_manager.get_retry_settings()
        print(f"Retry settings: {retry_settings}")
        
        # Check provider configs
        for provider_name in ["gemini", "openai", "anthropic"]:
            config = config_manager.get_provider_config(provider_name)
            enabled = config.get("enabled", False)
            print(f"{provider_name}: {'enabled' if enabled else 'disabled'}")
        
        return True
    except Exception as e:
        print(f"✗ Configuration check failed: {e}")
        return False

def check_provider_manager():
    """Check provider manager functionality."""
    print("\n=== Checking Provider Manager ===")
    
    try:
        from ai_providers.provider_manager import provider_manager
        
        available = provider_manager.get_available_providers()
        print(f"Available providers: {available}")
        
        status = provider_manager.get_provider_status()
        for provider_name, info in status.items():
            status_str = "✓" if info["available"] else "✗"
            print(f"{status_str} {provider_name}: {info}")
        
        return True
    except Exception as e:
        print(f"✗ Provider manager check failed: {e}")
        return False

def check_prompt_templates():
    """Check prompt template system."""
    print("\n=== Checking Prompt Templates ===")
    
    try:
        from translation.provider_prompt_templates import ProviderPromptTemplates
        
        languages = ["Japanese", "Chinese", "Korean"]
        providers = ["gemini", "openai", "anthropic"]
        
        for lang in languages:
            for provider in providers:
                try:
                    prompt = ProviderPromptTemplates.get_translation_prompt(lang, provider)
                    fallback = ProviderPromptTemplates.get_fallback_prompt(lang, provider)
                    
                    if prompt and fallback:
                        print(f"✓ {lang} prompts for {provider} (lengths: {len(prompt)}, {len(fallback)})")
                    else:
                        print(f"✗ {lang} prompts for {provider} - empty")
                except Exception as e:
                    print(f"✗ {lang} prompts for {provider} failed: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Prompt templates check failed: {e}")
        return False

def check_translator_integration():
    """Check translator integration."""
    print("\n=== Checking Translator Integration ===")
    
    try:
        from translation.multi_provider_translator import MultiProviderTranslator
        
        translator = MultiProviderTranslator(source_lang="Japanese")
        print(f"✓ MultiProviderTranslator created")
        
        available = translator.get_available_providers()
        print(f"Available providers: {available}")
        
        status = translator.get_provider_status()
        print(f"Provider status: {len(status)} providers")
        
        return True
    except Exception as e:
        print(f"✗ Translator integration check failed: {e}")
        return False

def run_validation():
    """Run all validation checks."""
    print("Multi-Provider System Validation")
    print("=" * 40)
    
    checks = [
        ("Import Check", check_imports),
        ("Provider Factory", check_provider_factory),
        ("Configuration", check_configuration),
        ("Provider Manager", check_provider_manager),
        ("Prompt Templates", check_prompt_templates),
        ("Translator Integration", check_translator_integration),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ {name} check crashed: {e}")
            results.append((name, False))
    
    print("\n=== Summary ===")
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! The multi-provider system is ready to use.")
    else:
        print("\n⚠️  Some checks failed. Please review the errors above.")
    
    return all_passed

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
