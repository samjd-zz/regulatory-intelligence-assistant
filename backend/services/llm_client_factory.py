"""
LLM Client Factory - Provider abstraction for switching between Gemini and Ollama

This module provides a factory pattern for creating LLM clients, allowing
seamless switching between different providers based on environment configuration.

Author: Assistant
Created: 2025-12-16
"""

import os
import logging
from typing import Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.gemini_client import GeminiClient
    from services.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

# Singleton instances
_gemini_client: Optional['GeminiClient'] = None
_ollama_client: Optional['OllamaClient'] = None


def get_llm_client(provider: Optional[str] = None) -> Union['GeminiClient', 'OllamaClient']:
    """
    Factory function to get appropriate LLM client based on provider.
    
    Args:
        provider: 'gemini' or 'ollama' (defaults to LLM_PROVIDER env var)
    
    Returns:
        Configured LLM client instance with compatible interface
    
    Raises:
        ValueError: If provider is unknown
        ImportError: If required dependencies are not available
    """
    global _gemini_client, _ollama_client
    
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    logger.info(f"Getting LLM client for provider: {provider}")
    
    if provider == "gemini":
        if _gemini_client is None:
            try:
                from services.gemini_client import GeminiClient
                _gemini_client = GeminiClient()
                logger.info("Initialized Gemini client")
            except ImportError as e:
                logger.error(f"Failed to import GeminiClient: {e}")
                raise
        return _gemini_client
        
    elif provider == "ollama":
        if _ollama_client is None:
            try:
                from services.ollama_client import OllamaClient
                _ollama_client = OllamaClient()
                logger.info("Initialized Ollama client")
            except ImportError as e:
                logger.error(f"Failed to import OllamaClient: {e}")
                raise
        return _ollama_client
        
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Must be 'gemini' or 'ollama'")


def get_gemini_client():
    """
    Backward compatibility function for existing code that imports get_gemini_client.
    
    This function will return either Gemini or Ollama client based on LLM_PROVIDER env var.
    If LLM_PROVIDER is not set, it defaults to Gemini for backward compatibility.
    """
    return get_llm_client()


def reset_clients():
    """Reset singleton clients (useful for testing)"""
    global _gemini_client, _ollama_client
    _gemini_client = None
    _ollama_client = None
    logger.info("Reset LLM client singletons")


def get_available_providers() -> list:
    """Get list of available LLM providers"""
    providers = []
    
    try:
        from services.gemini_client import GeminiClient
        providers.append("gemini")
    except ImportError:
        pass
    
    try:
        from services.ollama_client import OllamaClient
        providers.append("ollama")
    except ImportError:
        pass
    
    return providers


def health_check_all_providers() -> dict:
    """Check health of all available providers"""
    results = {}
    
    for provider in get_available_providers():
        try:
            client = get_llm_client(provider)
            results[provider] = client.health_check()
        except Exception as e:
            results[provider] = {
                "status": "error",
                "error": str(e),
                "timestamp": "unknown"
            }
    
    return results