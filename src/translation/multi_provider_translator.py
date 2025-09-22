"""
Multi-provider translator that uses the new AI provider system.

This module provides a translator that can work with multiple AI providers
while maintaining compatibility with the existing translation workflow.
"""

import re
import time
from typing import Optional, List, Callable
from ai_providers.provider_manager import provider_manager
from ai_providers.base_provider import TranslationResult
from glossary.glossary import Glossary
from translation.prompt_templates import get_translation_prompt
from translation.fallback_templates import get_fallback_prompt
from translation.provider_prompt_templates import ProviderPromptTemplates


class MultiProviderTranslator:
    """
    Translator that uses multiple AI providers with fallback support.
    
    This class maintains compatibility with the existing Translator interface
    while using the new provider system underneath.
    """
    
    def __init__(self, glossary_file: Optional[str] = None, source_lang: str = 'Japanese', 
                 preferred_provider: Optional[str] = None):
        """
        Initialize the multi-provider translator.
        
        Args:
            glossary_file: Optional path to the glossary file
            source_lang: Source language for translation
            preferred_provider: Preferred AI provider to use
        """
        self.source_lang = source_lang
        self.preferred_provider = preferred_provider
        self.glossary = Glossary(glossary_file)
        
        # Ensure providers are initialized
        if not provider_manager.get_available_providers():
            provider_manager.reinitialize_all_providers()
    
    def get_name_glossary(self) -> str:
        """Get the name glossary content."""
        try:
            current_glossary = self.glossary.get_current_glossary_file()
            if not current_glossary:
                return ""
                
            import os
            glossary_name = os.path.splitext(os.path.basename(current_glossary))[0]
            glossary_dir = os.path.dirname(current_glossary)
            name_glossary_path = os.path.join(glossary_dir, glossary_name, "name_glossary.txt")
            
            if not os.path.exists(name_glossary_path):
                return ""
                
            with open(name_glossary_path, "r", encoding="utf-8") as f:
                return f.read().strip()
                
        except Exception as e:
            print(f"[WARNING] Error reading name glossary: {e}")
            return ""
    
    def get_context_glossary(self) -> str:
        """Get the context glossary content."""
        try:
            current_glossary = self.glossary.get_current_glossary_file()
            if not current_glossary:
                return ""
                
            import os
            glossary_name = os.path.splitext(os.path.basename(current_glossary))[0]
            glossary_dir = os.path.dirname(current_glossary)
            context_glossary_path = os.path.join(glossary_dir, glossary_name, "context_glossary.txt")
            
            if not os.path.exists(context_glossary_path):
                return ""
                
            with open(context_glossary_path, "r", encoding="utf-8") as f:
                return f.read().strip()
                
        except Exception as e:
            print(f"[WARNING] Error reading context glossary: {e}")
            return ""
    
    def translate(self, text: str, log_message: Optional[Callable] = None, 
                 cancel_flag: Optional[Callable] = None) -> Optional[str]:
        """
        Translate the given text using available AI providers.
        
        Args:
            text: The text to translate
            log_message: Function to log messages
            cancel_flag: Function that returns True if translation should be cancelled
            
        Returns:
            The translated text, or None if translation fails
        """
        if log_message is None:
            log_message = print
        
        # Check for cancellation
        if cancel_flag and cancel_flag():
            log_message("[CONTROL] Translation cancelled before starting.")
            return None
        
        # Extract and store image tags before translation
        image_tag_pattern = re.compile(r'(<img[^>]*>)')
        image_tags = []
        
        def store_image_tag(match):
            image_tags.append(match.group(1))
            return f"__IMAGE_TAG_{len(image_tags)-1}__"
        
        text_with_placeholders = image_tag_pattern.sub(store_image_tag, text)
        
        # Check for cancellation after preprocessing
        if cancel_flag and cancel_flag():
            log_message("[CONTROL] Translation cancelled after preprocessing.")
            return None
        
        # Get glossary text
        name_glossary = self.get_name_glossary()
        context_glossary = self.get_context_glossary()
        
        glossary_parts = []
        if name_glossary:
            glossary_parts.append(f"Character Names:\n{name_glossary}")
        if context_glossary:
            glossary_parts.append(f"Context Terms:\n{context_glossary}")
        
        glossary_text = "\n\n".join(glossary_parts) if glossary_parts else None
        
        # Determine which provider will be used for prompt optimization
        provider_name = self.preferred_provider
        if not provider_name or provider_name == "Auto (Fallback)":
            # Get the default provider for prompt optimization
            available_providers = provider_manager.get_available_providers()
            provider_name = available_providers[0] if available_providers else "gemini"

        # Build instruction sets with provider-specific optimization
        try:
            primary_prompt = ProviderPromptTemplates.get_translation_prompt(self.source_lang, provider_name)
            secondary_prompt = ProviderPromptTemplates.get_fallback_prompt(self.source_lang, provider_name)
        except Exception:
            # Fall back to generic prompts if provider-specific ones fail
            primary_prompt = get_translation_prompt(self.source_lang)
            secondary_prompt = get_fallback_prompt(self.source_lang)
        
        # Try primary instructions first
        log_message("[TRANSLATION] Attempting translation with primary instructions...")
        result = self._attempt_translation(
            text_with_placeholders,
            [primary_prompt],
            glossary_text,
            "PRIMARY",
            log_message,
            cancel_flag
        )
        
        if result and result.success:
            translated_text = result.text
        else:
            # Try fallback instructions
            log_message("[TRANSLATION] Primary failed, trying fallback instructions...")
            if cancel_flag and cancel_flag():
                log_message("[CONTROL] Translation cancelled before fallback.")
                return None
                
            result = self._attempt_translation(
                text_with_placeholders,
                [secondary_prompt],
                glossary_text,
                "FALLBACK",
                log_message,
                cancel_flag
            )
            
            if result and result.success:
                translated_text = result.text
            else:
                log_message("[ERROR] All translation attempts failed.")
                return None
        
        # Restore image tags
        if image_tags:
            for i, tag in enumerate(image_tags):
                placeholder = f"__IMAGE_TAG_{i}__"
                translated_text = translated_text.replace(placeholder, tag)
        
        log_message(f"[SUCCESS] Translation completed using {result.provider}")
        return translated_text
    
    def _attempt_translation(self, text: str, instructions: List[str], 
                           glossary_text: Optional[str], instructions_label: str,
                           log_message: Callable, cancel_flag: Optional[Callable]) -> Optional[TranslationResult]:
        """
        Attempt translation with given instructions.
        
        Args:
            text: Text to translate
            instructions: List of instruction prompts
            glossary_text: Glossary text to include
            instructions_label: Label for logging
            log_message: Logging function
            cancel_flag: Cancellation check function
            
        Returns:
            TranslationResult or None if cancelled
        """
        if cancel_flag and cancel_flag():
            return None
        
        log_message(f"[TRANSLATION] Using {instructions_label} instructions")
        
        # Determine provider to use
        provider_name = None
        if self.preferred_provider and self.preferred_provider != "Auto (Fallback)":
            provider_name = self.preferred_provider.lower()
        
        # Perform translation
        result = provider_manager.translate(
            text=text,
            source_lang=self.source_lang,
            instructions=instructions,
            glossary_text=glossary_text,
            provider_name=provider_name
        )
        
        if result.success:
            log_message(f"[SUCCESS] Translation successful with {result.provider} ({result.model})")
            if result.tokens_used:
                log_message(f"[INFO] Tokens used: {result.tokens_used}")
            if result.cost:
                log_message(f"[INFO] Estimated cost: ${result.cost:.4f}")
        else:
            log_message(f"[ERROR] Translation failed: {result.error}")
        
        return result
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return provider_manager.get_available_providers()
    
    def get_provider_status(self) -> dict:
        """Get status of all providers."""
        return provider_manager.get_provider_status()
    
    def set_preferred_provider(self, provider_name: Optional[str]):
        """Set the preferred provider."""
        self.preferred_provider = provider_name
    
    def reinitialize_providers(self):
        """Reinitialize all providers."""
        provider_manager.reinitialize_all_providers()
