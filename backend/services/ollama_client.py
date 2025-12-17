"""
Ollama Client - Wrapper for Ollama API

This module provides a client for interacting with a local Ollama API instance,
providing a compatible interface with the existing Gemini client for seamless switching.

Author: Assistant
Created: 2025-12-16
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMError:
    """Structured error information from LLM APIs (compatible with GeminiError)"""
    error_type: str  # "rate_limit", "quota_exceeded", "invalid_request", "network", "unknown"
    message: str  # User-friendly message
    retry_after_seconds: Optional[int] = None  # Suggested retry delay
    is_retryable: bool = False  # Whether the error can be retried
    original_error: Optional[str] = None  # Original exception message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "error_type": self.error_type,
            "message": self.message,
            "retry_after_seconds": self.retry_after_seconds,
            "is_retryable": self.is_retryable,
            "original_error": self.original_error
        }


class OllamaClient:
    """Client for Ollama local LLM API with Gemini-compatible interface"""
    
    def __init__(self, host: Optional[str] = None, model_name: Optional[str] = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self._session = requests.Session()
        self._session.timeout = 30
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        """Internal method to check if Ollama is available"""
        return self.is_available()

    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = self._session.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == self.model_name for m in models)
            return False
        except Exception as e:
            logger.debug(f"Ollama availability check failed: {e}")
            return False

    def _make_request(
        self, 
        endpoint: str, 
        data: Dict[str, Any], 
        timeout: int = 30
    ) -> Tuple[Optional[Dict[str, Any]], Optional[LLMError]]:
        """Make HTTP request to Ollama API with error handling"""
        try:
            response = self._session.post(
                f"{self.host}/{endpoint}",
                json=data,
                timeout=timeout,
                stream=True
            )
            
            if response.status_code == 200:
                # Parse streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'response' in chunk:
                                full_response += chunk['response']
                            if chunk.get('done', False):
                                return {'response': full_response}, None
                        except json.JSONDecodeError:
                            continue
                
                return {'response': full_response}, None
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return None, LLMError(
                    error_type="network",
                    message=f"Ollama API request failed: {error_msg}",
                    is_retryable=True,
                    original_error=error_msg
                )
                
        except requests.exceptions.Timeout:
            return None, LLMError(
                error_type="network",
                message="Request to Ollama API timed out",
                is_retryable=True,
                retry_after_seconds=5
            )
        except requests.exceptions.ConnectionError:
            return None, LLMError(
                error_type="network",
                message="Could not connect to Ollama API. Is Ollama running?",
                is_retryable=True,
                retry_after_seconds=10
            )
        except Exception as e:
            return None, LLMError(
                error_type="unknown",
                message=f"Unexpected error: {str(e)}",
                is_retryable=False,
                original_error=str(e)
            )

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        max_retries: int = 3,
        **kwargs
    ) -> Tuple[Optional[str], Optional[LLMError]]:
        """Generate content using Ollama API"""
        
        if not self.is_available():
            return None, LLMError(
                error_type="network",
                message="Ollama service is not available",
                is_retryable=True,
                retry_after_seconds=10
            )

        # Prepare request data
        data = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,  # Always use non-streaming for simplicity
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            data["options"]["num_predict"] = max_tokens

        # Retry logic
        for attempt in range(max_retries):
            try:
                response_data, error = self._make_request("api/generate", data)
                
                if error is None and response_data:
                    return response_data.get('response'), None
                elif error and error.is_retryable and attempt < max_retries - 1:
                    delay = error.retry_after_seconds or (2 ** attempt)
                    logger.warning(f"Ollama request failed (attempt {attempt + 1}/{max_retries}), retrying in {delay}s: {error.message}")
                    time.sleep(delay)
                    continue
                else:
                    return None, error
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    return None, LLMError(
                        error_type="unknown",
                        message=f"Failed after {max_retries} attempts: {str(e)}",
                        is_retryable=False,
                        original_error=str(e)
                    )
                time.sleep(2 ** attempt)
                
        return None, LLMError(
            error_type="unknown",
            message="Max retries exceeded",
            is_retryable=False
        )

    def generate_with_context(
        self,
        query: str,
        context: Union[str, List[str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ) -> Tuple[Optional[str], Optional[LLMError]]:
        """Generate with context (used by RAG service)"""
        
        # Prepare context string
        if isinstance(context, list):
            context_str = "\n\n".join(context)
        else:
            context_str = context

        # Build prompt with context
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nContext:\n{context_str}\n\nQuery: {query}\n\nAnswer:"
        else:
            full_prompt = f"Context:\n{context_str}\n\nQuery: {query}\n\nAnswer:"

        return self.generate_content(
            prompt=full_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries
        )

    def health_check(self) -> Dict[str, Any]:
        """Health check for Ollama service"""
        start_time = time.time()
        
        try:
            # Check if service is running
            response = self._session.get(f"{self.host}/api/tags", timeout=5)
            
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_available = any(m['name'] == self.model_name for m in models)
                
                # Test generation if model is available
                if model_available:
                    test_prompt = "Hello"
                    test_response, test_error = self.generate_content(
                        prompt=test_prompt,
                        temperature=0.1,
                        max_tokens=10,
                        max_retries=1
                    )
                    
                    response_time = time.time() - start_time
                    
                    return {
                        "status": "healthy" if test_error is None else "degraded",
                        "ollama_running": True,
                        "model_available": True,
                        "model_name": self.model_name,
                        "host": self.host,
                        "response_time_seconds": round(response_time, 3),
                        "test_generation_successful": test_error is None,
                        "test_error": test_error.to_dict() if test_error else None,
                        "available_models": [m['name'] for m in models],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "ollama_running": True,
                        "model_available": False,
                        "model_name": self.model_name,
                        "host": self.host,
                        "error": f"Model {self.model_name} not available",
                        "available_models": [m['name'] for m in models],
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                return {
                    "status": "unhealthy",
                    "ollama_running": False,
                    "model_available": False,
                    "model_name": self.model_name,
                    "host": self.host,
                    "error": f"Ollama API returned status {response.status_code}",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "ollama_running": False,
                "model_available": False,
                "model_name": self.model_name,
                "host": self.host,
                "error": f"Health check failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Get cost estimate (returns $0.00 since Ollama is local/free)"""
        return {
            "input_cost": 0.00,
            "output_cost": 0.00,
            "total_cost": 0.00,
            "provider": "ollama",
            "model": self.model_name,
            "note": "Local inference - no API costs"
        }