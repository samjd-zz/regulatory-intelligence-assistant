"""
Test Suite for LLM Client Factory

Tests the factory pattern for switching between different LLM providers.

Author: Assistant
Created: 2025-12-16
"""

import pytest
import os
from unittest.mock import patch, Mock
from services.llm_client_factory import (
    get_llm_client,
    get_gemini_client,
    reset_clients,
    get_available_providers,
    health_check_all_providers
)


class TestLLMClientFactory:
    """Test suite for LLM client factory"""
    
    def setup_method(self):
        """Reset clients before each test"""
        reset_clients()
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'gemini'})
    @patch('services.gemini_client.GeminiClient')
    def test_get_llm_client_gemini(self, mock_gemini_class):
        """Test getting Gemini client"""
        mock_client = Mock()
        mock_gemini_class.return_value = mock_client
        
        client = get_llm_client()
        assert client is mock_client
        mock_gemini_class.assert_called_once()
    
    @patch.dict(os.environ, {'LLM_PROVIDER': 'ollama'})
    @patch('services.ollama_client.OllamaClient')
    def test_get_llm_client_ollama(self, mock_ollama_class):
        """Test getting Ollama client"""
        mock_client = Mock()
        mock_ollama_class.return_value = mock_client
        
        client = get_llm_client()
        assert client is mock_client
        mock_ollama_class.assert_called_once()
    
    @patch('services.gemini_client.GeminiClient')
    def test_get_llm_client_default_gemini(self, mock_gemini_class):
        """Test default to Gemini when LLM_PROVIDER not set"""
        mock_client = Mock()
        mock_gemini_class.return_value = mock_client
        
        # Ensure LLM_PROVIDER is not set
        with patch.dict(os.environ, {}, clear=True):
            client = get_llm_client()
            assert client is mock_client
    
    def test_get_llm_client_invalid_provider(self):
        """Test error with invalid provider"""
        with pytest.raises(ValueError, match="Unknown LLM provider: invalid"):
            get_llm_client("invalid")
    
    @patch('services.ollama_client.OllamaClient')
    def test_get_llm_client_explicit_provider(self, mock_ollama_class):
        """Test explicit provider parameter"""
        mock_client = Mock()
        mock_ollama_class.return_value = mock_client
        
        client = get_llm_client("ollama")
        assert client is mock_client
    
    @patch('services.gemini_client.GeminiClient')
    def test_singleton_behavior(self, mock_gemini_class):
        """Test that clients are singleton instances"""
        mock_client = Mock()
        mock_gemini_class.return_value = mock_client
        
        client1 = get_llm_client("gemini")
        client2 = get_llm_client("gemini")
        
        assert client1 is client2
        # Should only instantiate once
        mock_gemini_class.assert_called_once()
    
    @patch('services.llm_client_factory.get_llm_client')
    def test_get_gemini_client_backwards_compatibility(self, mock_get_llm_client):
        """Test backward compatibility function"""
        mock_client = Mock()
        mock_get_llm_client.return_value = mock_client
        
        client = get_gemini_client()
        assert client is mock_client
        mock_get_llm_client.assert_called_once()
    
    def test_reset_clients(self):
        """Test resetting singleton clients"""
        # This test mainly ensures the function runs without error
        reset_clients()
    
    @patch('services.gemini_client.GeminiClient')
    @patch('services.ollama_client.OllamaClient')
    def test_get_available_providers(self, mock_ollama_class, mock_gemini_class):
        """Test getting available providers"""
        providers = get_available_providers()
        assert "gemini" in providers
        assert "ollama" in providers
    
    @patch('services.llm_client_factory.get_available_providers')
    @patch('services.llm_client_factory.get_llm_client')
    def test_health_check_all_providers(self, mock_get_llm_client, mock_get_providers):
        """Test health check for all providers"""
        mock_get_providers.return_value = ["gemini", "ollama"]
        
        mock_gemini_client = Mock()
        mock_gemini_client.health_check.return_value = {"status": "healthy"}
        
        mock_ollama_client = Mock()
        mock_ollama_client.health_check.return_value = {"status": "healthy"}
        
        def mock_client_factory(provider):
            if provider == "gemini":
                return mock_gemini_client
            elif provider == "ollama":
                return mock_ollama_client
            
        mock_get_llm_client.side_effect = mock_client_factory
        
        results = health_check_all_providers()
        
        assert "gemini" in results
        assert "ollama" in results
        assert results["gemini"]["status"] == "healthy"
        assert results["ollama"]["status"] == "healthy"
    
    @patch('services.llm_client_factory.get_available_providers')
    @patch('services.llm_client_factory.get_llm_client')
    def test_health_check_with_error(self, mock_get_llm_client, mock_get_providers):
        """Test health check when provider raises error"""
        mock_get_providers.return_value = ["gemini"]
        mock_get_llm_client.side_effect = Exception("Provider error")
        
        results = health_check_all_providers()
        
        assert "gemini" in results
        assert results["gemini"]["status"] == "error"
        assert "Provider error" in results["gemini"]["error"]


if __name__ == "__main__":
    pytest.main([__file__])