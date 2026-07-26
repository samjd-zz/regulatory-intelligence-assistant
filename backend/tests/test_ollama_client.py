"""
Test Suite for Ollama Client

Tests the Ollama client implementation including health checks,
content generation, and error handling.

Author: Assistant
Created: 2025-12-16
"""

import pytest
import os
from unittest.mock import patch, Mock
from services.ollama_client import OllamaClient, LLMError


class TestOllamaClient:
    """Test suite for OllamaClient"""
    
    def test_init_default_values(self):
        """Test initialization with default values"""
        with patch.object(OllamaClient, '_check_availability', return_value=True):
            client = OllamaClient()
            assert client.host == "http://ollama:11434"
            assert client.model_name == "llama3.2:3b"
            assert client.available is True
    
    def test_init_custom_values(self):
        """Test initialization with custom values"""
        with patch.object(OllamaClient, '_check_availability', return_value=False):
            client = OllamaClient(host="http://custom:8080", model_name="custom-model")
            assert client.host == "http://custom:8080"
            assert client.model_name == "custom-model"
            assert client.available is False
    
    def test_init_env_variables(self):
        """Test initialization with environment variables"""
        with patch.dict(os.environ, {
            'OLLAMA_HOST': 'http://env-host:9999',
            'OLLAMA_MODEL': 'env-model'
        }):
            with patch.object(OllamaClient, '_check_availability', return_value=True):
                client = OllamaClient()
                assert client.host == "http://env-host:9999"
                assert client.model_name == "env-model"
    
    @patch('services.ollama_client.requests.Session')
    def test_is_available_success(self, mock_session_class):
        """Test is_available when service is running and model exists"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'llama3.2:3b'},
                {'name': 'other-model'}
            ]
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        assert client.is_available() is True
    
    @patch('services.ollama_client.requests.Session')
    def test_is_available_model_not_found(self, mock_session_class):
        """Test is_available when model is not available"""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'other-model'}
            ]
        }
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        assert client.is_available() is False
    
    @patch('services.ollama_client.requests.Session')
    def test_is_available_connection_error(self, mock_session_class):
        """Test is_available when connection fails"""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Connection failed")
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        assert client.is_available() is False
    
    @patch('services.ollama_client.requests.Session')
    def test_generate_content_success(self, mock_session_class):
        """Test successful content generation"""
        mock_session = Mock()
        
        # Mock availability check
        mock_availability_response = Mock()
        mock_availability_response.status_code = 200
        mock_availability_response.json.return_value = {'models': [{'name': 'llama3.2:3b'}]}
        
        # Mock generation response
        mock_generation_response = Mock()
        mock_generation_response.status_code = 200
        mock_generation_response.iter_lines.return_value = [
            b'{"response": "Hello", "done": false}',
            b'{"response": " world", "done": false}',
            b'{"response": "!", "done": true}'
        ]
        
        mock_session.get.return_value = mock_availability_response
        mock_session.post.return_value = mock_generation_response
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        result, error = client.generate_content("Test prompt")
        
        assert error is None
        assert result == "Hello world!"
    
    @patch('services.ollama_client.requests.Session')
    def test_generate_content_service_unavailable(self, mock_session_class):
        """Test content generation when service is unavailable"""
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Connection failed")
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        result, error = client.generate_content("Test prompt")
        
        assert result is None
        assert error is not None
        assert error.error_type == "network"
        assert "not available" in error.message
    
    @patch('services.ollama_client.requests.Session')
    def test_generate_with_context(self, mock_session_class):
        """Test generate_with_context method"""
        mock_session = Mock()
        
        # Mock availability check
        mock_availability_response = Mock()
        mock_availability_response.status_code = 200
        mock_availability_response.json.return_value = {'models': [{'name': 'llama3.2:3b'}]}
        
        # Mock generation response
        mock_generation_response = Mock()
        mock_generation_response.status_code = 200
        mock_generation_response.iter_lines.return_value = [
            b'{"response": "Based on context", "done": false}',
            b'{"response": ", the answer is yes", "done": true}'
        ]
        
        mock_session.get.return_value = mock_availability_response
        mock_session.post.return_value = mock_generation_response
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        result, error = client.generate_with_context(
            query="Is this legal?",
            context=["Some legal document text", "More context"],
            system_prompt="You are a legal assistant"
        )
        
        assert error is None
        assert result == "Based on context, the answer is yes"
    
    @patch('services.ollama_client.requests.Session')
    def test_health_check_healthy(self, mock_session_class):
        """Test health check when service is healthy"""
        mock_session = Mock()
        
        # Mock tags endpoint
        mock_tags_response = Mock()
        mock_tags_response.status_code = 200
        mock_tags_response.json.return_value = {'models': [{'name': 'llama3.2:3b'}]}
        
        # Mock generation endpoint
        mock_generation_response = Mock()
        mock_generation_response.status_code = 200
        mock_generation_response.iter_lines.return_value = [
            b'{"response": "Hello", "done": true}'
        ]
        
        mock_session.get.return_value = mock_tags_response
        mock_session.post.return_value = mock_generation_response
        mock_session_class.return_value = mock_session
        
        client = OllamaClient()
        health = client.health_check()
        
        assert health["status"] == "healthy"
        assert health["ollama_running"] is True
        assert health["model_available"] is True
        assert health["test_generation_successful"] is True
    
    def test_get_cost_estimate(self):
        """Test cost estimation (should be free for local Ollama)"""
        with patch.object(OllamaClient, '_check_availability', return_value=True):
            client = OllamaClient()
            cost = client.get_cost_estimate(1000, 500)
            
            assert cost["input_cost"] == 0.00
            assert cost["output_cost"] == 0.00
            assert cost["total_cost"] == 0.00
            assert cost["provider"] == "ollama"


class TestLLMError:
    """Test suite for LLMError dataclass"""
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        error = LLMError(
            error_type="network",
            message="Test error",
            retry_after_seconds=5,
            is_retryable=True,
            original_error="Original error message"
        )
        
        expected = {
            "error_type": "network",
            "message": "Test error",
            "retry_after_seconds": 5,
            "is_retryable": True,
            "original_error": "Original error message"
        }
        
        assert error.to_dict() == expected


if __name__ == "__main__":
    pytest.main([__file__])