"""
Gemini Client - Wrapper for Google Gemini API

This module provides a client for interacting with Google's Gemini API,
including file uploads, chat completions, and content generation.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions as google_exceptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GeminiError:
    """Structured error information from Gemini API"""
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

# Gemini API pricing (per million tokens) - Updated December 2024
# Prices from: https://ai.google.dev/pricing
GEMINI_PRICING = {
    "gemini-1.5-pro": {
        "input_price_per_million": 1.25,  # Prompts up to 128K tokens
        "input_price_per_million_long": 2.50,  # Prompts over 128K tokens
        "output_price_per_million": 5.00,
        "context_caching_storage_per_million": 0.00,  # Free during preview
    },
    "gemini-1.5-flash": {
        "input_price_per_million": 0.075,  # Prompts up to 128K tokens
        "input_price_per_million_long": 0.15,  # Prompts over 128K tokens
        "output_price_per_million": 0.30,
        "context_caching_storage_per_million": 0.00,  # Free during preview
    },
    "gemini-2.0-flash-exp": {
        "input_price_per_million": 0.00,  # Free during preview
        "output_price_per_million": 0.00,
        "context_caching_storage_per_million": 0.00,
    },
    "gemini-2.5-flash": {
        "input_price_per_million": 0.00,  # Free during preview (experimental)
        "input_price_per_million_long": 0.00,
        "output_price_per_million": 0.00,
        "context_caching_storage_per_million": 0.00,
    }
}


class GeminiClient:
    """
    Client for Google Gemini API operations.

    Provides methods for file uploads, chat completions, and content generation
    with safety settings and configuration management.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (defaults to env var GEMINI_API_KEY)
            model_name: Model to use (defaults to env var GEMINI_MODEL or gemini-1.5-pro)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. Gemini features will be unavailable.")
            self.available = False
            return

        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        self.available = True

        # Initialize model
        try:
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini client initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.available = False

    def is_available(self) -> bool:
        """Check if Gemini API is available"""
        return self.available

    def _classify_error(self, error: Exception) -> GeminiError:
        """
        Classify an exception into a structured GeminiError.
        
        Args:
            error: Exception from Gemini API
            
        Returns:
            GeminiError with categorized information
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Rate limit errors (429)
        if isinstance(error, google_exceptions.ResourceExhausted) or "429" in error_str or "rate limit" in error_str:
            # Try to extract retry-after from error message
            retry_after = 60  # Default to 60 seconds
            if "retry after" in error_str:
                import re
                match = re.search(r'retry after (\d+)', error_str)
                if match:
                    retry_after = int(match.group(1))
            
            return GeminiError(
                error_type="rate_limit",
                message=f"The AI service is experiencing high demand. Please wait {retry_after} seconds and try again.",
                retry_after_seconds=retry_after,
                is_retryable=True,
                original_error=str(error)
            )
        
        # Quota exceeded (daily/monthly limits)
        elif isinstance(error, google_exceptions.PermissionDenied) or "quota" in error_str or "quota exceeded" in error_str:
            return GeminiError(
                error_type="quota_exceeded",
                message="Your API quota has been exceeded. Please check your Gemini API usage limits and try again later.",
                retry_after_seconds=3600,  # Suggest trying again in 1 hour
                is_retryable=False,  # Don't auto-retry quota issues
                original_error=str(error)
            )
        
        # Invalid request (bad parameters, malformed input)
        elif isinstance(error, google_exceptions.InvalidArgument) or "invalid" in error_str or "400" in error_str:
            return GeminiError(
                error_type="invalid_request",
                message="The request to the AI service was invalid. Please try rephrasing your question.",
                retry_after_seconds=None,
                is_retryable=False,
                original_error=str(error)
            )
        
        # Network/connection errors
        elif isinstance(error, (google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded)) or \
             "timeout" in error_str or "connection" in error_str or "network" in error_str:
            return GeminiError(
                error_type="network",
                message="Unable to connect to the AI service. Please check your internet connection and try again.",
                retry_after_seconds=5,
                is_retryable=True,
                original_error=str(error)
            )
        
        # Authentication errors
        elif isinstance(error, google_exceptions.Unauthenticated) or "authentication" in error_str or "401" in error_str:
            return GeminiError(
                error_type="authentication",
                message="AI service authentication failed. Please contact support.",
                retry_after_seconds=None,
                is_retryable=False,
                original_error=str(error)
            )
        
        # Unknown errors
        else:
            return GeminiError(
                error_type="unknown",
                message="An unexpected error occurred with the AI service. Please try again later.",
                retry_after_seconds=30,
                is_retryable=True,
                original_error=str(error)
            )

    def _exponential_backoff_retry(
        self,
        operation_func,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0
    ) -> Tuple[Optional[Any], Optional[GeminiError]]:
        """
        Execute an operation with exponential backoff retry logic.
        
        Args:
            operation_func: Function to execute (should raise exceptions on failure)
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds before first retry
            max_delay: Maximum delay between retries
            backoff_multiplier: Multiplier for exponential backoff
            
        Returns:
            Tuple of (result, error). If successful, error is None. If failed after all retries, result is None.
        """
        last_error = None
        delay = initial_delay
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Attempt the operation
                result = operation_func()
                
                # Success!
                if attempt > 0:
                    logger.info(f"✅ Operation succeeded after {attempt} retry attempt(s)")
                
                return result, None
                
            except Exception as e:
                # Classify the error
                gemini_error = self._classify_error(e)
                last_error = gemini_error
                
                # Log the error
                logger.warning(
                    f"⚠️  Gemini API error (attempt {attempt + 1}/{max_retries + 1}): "
                    f"{gemini_error.error_type} - {gemini_error.message}"
                )
                
                # Check if we should retry
                if not gemini_error.is_retryable:
                    logger.error(f"❌ Error is not retryable: {gemini_error.error_type}")
                    return None, gemini_error
                
                # Check if we've exhausted retries
                if attempt >= max_retries:
                    logger.error(f"❌ Max retries ({max_retries}) exhausted")
                    return None, gemini_error
                
                # Calculate delay (use error's suggested delay if available)
                if gemini_error.retry_after_seconds:
                    actual_delay = min(gemini_error.retry_after_seconds, max_delay)
                else:
                    actual_delay = min(delay, max_delay)
                
                logger.info(f"🔄 Retrying in {actual_delay:.1f} seconds...")
                time.sleep(actual_delay)
                
                # Exponential backoff for next iteration
                delay *= backoff_multiplier
        
        # Should not reach here, but just in case
        return None, last_error

    def _calculate_cost(self, input_tokens: int, output_tokens: int, cached_tokens: int = 0) -> Dict[str, float]:
        """
        Calculate the cost of API usage based on token counts.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cached_tokens: Number of cached tokens (for context caching)
            
        Returns:
            Dict with cost breakdown
        """
        pricing = GEMINI_PRICING.get(self.model_name, GEMINI_PRICING["gemini-1.5-pro"])
        
        # Determine if long context pricing applies (over 128K tokens)
        threshold = 128_000
        use_long_pricing = input_tokens > threshold
        
        input_price = pricing["input_price_per_million_long"] if use_long_pricing else pricing["input_price_per_million"]
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * input_price
        output_cost = (output_tokens / 1_000_000) * pricing["output_price_per_million"]
        cached_cost = (cached_tokens / 1_000_000) * pricing["context_caching_storage_per_million"]
        
        total_cost = input_cost + output_cost + cached_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": input_tokens + output_tokens,
            "input_cost_usd": round(input_cost, 6),
            "output_cost_usd": round(output_cost, 6),
            "cached_cost_usd": round(cached_cost, 6),
            "total_cost_usd": round(total_cost, 6),
            "model": self.model_name,
            "pricing_tier": "long_context" if use_long_pricing else "standard"
        }
    
    def _log_usage_metrics(self, response, operation: str = "generate") -> Optional[Dict[str, Any]]:
        """
        Extract and log token usage metrics from a Gemini API response.
        
        Args:
            response: Gemini API response object
            operation: Type of operation (generate, chat, etc.)
            
        Returns:
            Dict with usage metrics or None if unavailable
        """
        try:
            # Extract usage metadata from response
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                
                input_tokens = getattr(usage, 'prompt_token_count', 0)
                output_tokens = getattr(usage, 'candidates_token_count', 0)
                total_tokens = getattr(usage, 'total_token_count', 0)
                cached_tokens = getattr(usage, 'cached_content_token_count', 0)
                
                # Calculate costs
                cost_metrics = self._calculate_cost(input_tokens, output_tokens, cached_tokens)
                
                # Log the metrics transparently
                logger.info(
                    f"🤖 GEMINI API USAGE - {operation.upper()} | "
                    f"Model: {self.model_name} | "
                    f"Tokens: {input_tokens:,} in + {output_tokens:,} out = {total_tokens:,} total"
                    f"{f' ({cached_tokens:,} cached)' if cached_tokens > 0 else ''} | "
                    f"Cost: ${cost_metrics['total_cost_usd']:.6f} USD "
                    f"(in: ${cost_metrics['input_cost_usd']:.6f}, out: ${cost_metrics['output_cost_usd']:.6f})"
                )
                
                # Add timestamp and operation type
                metrics = {
                    **cost_metrics,
                    "operation": operation,
                    "timestamp": datetime.now().isoformat()
                }
                
                return metrics
            else:
                # usage_metadata is not always available in Gemini API responses
                # This is normal for some models/API versions and doesn't affect functionality
                logger.debug(f"ℹ️  Usage metadata not available for {operation} (this is normal for {self.model_name})")
                return None
                
        except Exception as e:
            logger.error(f"Failed to extract usage metrics: {e}", exc_info=True)
            return None

    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> Tuple[Optional[str], Optional[GeminiError]]:
        """
        Generate content using Gemini API with automatic retry on rate limits.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: List of sequences to stop generation
            max_retries: Maximum number of retry attempts on retryable errors

        Returns:
            Tuple of (generated_text, error). If successful, error is None.
            If failed, generated_text is None and error contains details.
        """
        if not self.available:
            logger.error("Gemini API not available")
            error = GeminiError(
                error_type="unavailable",
                message="The AI service is not configured. Please contact support.",
                is_retryable=False
            )
            return None, error

        # Define the operation to retry
        def _generate_operation():
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
            }

            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens

            if stop_sequences:
                generation_config["stop_sequences"] = stop_sequences

            # Safety settings - allow most content for legal/regulatory text
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            # Log usage metrics for transparency
            self._log_usage_metrics(response, operation="generate_content")

            # Extract text with detailed logging
            extracted_text = self._extract_text_from_response(response)
            
            if extracted_text:
                logger.info(f"✅ Successfully extracted {len(extracted_text)} characters from Gemini response")
                return extracted_text
            else:
                logger.error(f"❌ Failed to extract text from Gemini response - response may be blocked or empty")
                raise ValueError("Failed to extract text from response")
        
        # Execute with retry logic
        result, error = self._exponential_backoff_retry(
            operation_func=_generate_operation,
            max_retries=max_retries
        )
        
        return result, error

    def _extract_text_from_response(self, response) -> Optional[str]:
        """
        Safely extract text from a Gemini API response.
        Handles both simple (single-part) and complex (multi-part) responses.

        Args:
            response: Gemini API response object

        Returns:
            Extracted text or None if extraction fails
        """
        try:
            # Try the simple accessor first
            result_text = response.text
            if result_text and result_text.strip():
                return result_text
            logger.warning("response.text is empty or whitespace only")
        except (ValueError, AttributeError) as e:
            # Handle multi-part responses
            logger.debug(f"Simple text accessor failed, trying multi-part extraction: {e}")
            
            try:
                texts = []
                
                # Detailed debugging: Log full response structure
                logger.info(f"=== DEBUGGING GEMINI RESPONSE ===")
                logger.info(f"Response type: {type(response)}")
                
                if hasattr(response, '__dict__'):
                    logger.info(f"Response attributes: {list(response.__dict__.keys())}")
                    # Log the actual values (safely)
                    for key in response.__dict__.keys():
                        try:
                            value = getattr(response, key)
                            logger.info(f"  {key}: {type(value)} = {str(value)[:200]}")
                        except Exception as attr_error:
                            logger.info(f"  {key}: <error accessing: {attr_error}>")
                
                # Check prompt_feedback for safety blocks or issues
                if hasattr(response, 'prompt_feedback'):
                    logger.info(f"Prompt feedback: {response.prompt_feedback}")
                    if hasattr(response.prompt_feedback, 'block_reason'):
                        logger.warning(f"BLOCKED! Reason: {response.prompt_feedback.block_reason}")
                    if hasattr(response.prompt_feedback, 'safety_ratings'):
                        logger.info(f"Safety ratings: {response.prompt_feedback.safety_ratings}")
                
                # Check candidates
                if hasattr(response, 'candidates'):
                    logger.info(f"Number of candidates: {len(response.candidates) if response.candidates else 0}")
                    
                    if response.candidates:
                        for idx, candidate in enumerate(response.candidates):
                            logger.info(f"  Candidate {idx}:")
                            
                            # Check finish_reason
                            if hasattr(candidate, 'finish_reason'):
                                logger.info(f"    Finish reason: {candidate.finish_reason}")
                            
                            # Check safety ratings
                            if hasattr(candidate, 'safety_ratings'):
                                logger.info(f"    Safety ratings: {candidate.safety_ratings}")
                            
                            # Try to extract content
                            if hasattr(candidate, 'content'):
                                logger.info(f"    Content type: {type(candidate.content)}")
                                
                                # Check if content has parts
                                if hasattr(candidate.content, 'parts'):
                                    logger.info(f"    Number of parts: {len(candidate.content.parts) if candidate.content.parts else 0}")
                                    if candidate.content.parts:
                                        for part_idx, part in enumerate(candidate.content.parts):
                                            logger.info(f"      Part {part_idx}: {type(part)}")
                                            if hasattr(part, 'text'):
                                                logger.info(f"        Has text: {bool(part.text)}")
                                                if part.text:
                                                    texts.append(part.text)
                                                    logger.info(f"        Extracted text (first 100 chars): {part.text[:100]}")
                                            else:
                                                logger.info(f"        No text attribute")
                                                
                                # Sometimes content.text works directly
                                elif hasattr(candidate.content, 'text'):
                                    logger.info(f"    Content has text attribute: {bool(candidate.content.text)}")
                                    if candidate.content.text:
                                        texts.append(candidate.content.text)
                                        logger.info(f"    Extracted text (first 100 chars): {candidate.content.text[:100]}")
                            else:
                                logger.warning(f"    Candidate {idx} has no content attribute")
                    else:
                        logger.warning("Response has candidates attribute but it's empty/None")
                else:
                    logger.warning("Response has no candidates attribute")
                
                logger.info(f"=== END GEMINI RESPONSE DEBUG ===")
                
                if texts:
                    logger.info(f"Successfully extracted {len(texts)} text part(s)")
                    return ' '.join(texts)
                
                # Method 2: Try response.parts directly
                if hasattr(response, 'parts') and response.parts:
                    logger.info("Trying response.parts directly")
                    for part in response.parts:
                        if hasattr(part, 'text') and part.text:
                            texts.append(part.text)
                
                if texts:
                    logger.info(f"Successfully extracted {len(texts)} text part(s) from response.parts")
                    return ' '.join(texts)
                
                logger.error(f"Could not extract any text from response")
                return None
                
            except Exception as extract_error:
                logger.error(f"Failed to extract text from multi-part response: {extract_error}", exc_info=True)
                return None

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate response in a chat conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Assistant's response or None if error
        """
        if not self.available:
            logger.error("Gemini API not available")
            return None

        try:
            # Convert messages to Gemini format
            chat = self.model.start_chat(history=[])

            # Add all messages except the last one to history
            for msg in messages[:-1]:
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
                elif msg['role'] == 'assistant':
                    # Gemini doesn't directly support adding assistant messages to history
                    # We'll include them in the context
                    pass

            # Send the last user message
            last_message = messages[-1]['content']

            response = chat.send_message(
                last_message,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens if max_tokens else 2048,
                }
            )

            # Log usage metrics for transparency
            self._log_usage_metrics(response, operation="chat")

            return self._extract_text_from_response(response)

        except Exception as e:
            logger.error(f"Chat generation failed: {e}")
            return None

    def upload_file(self, file_path: str, display_name: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to Gemini for use in prompts.

        Args:
            file_path: Path to file to upload
            display_name: Optional display name for the file

        Returns:
            File URI or None if error
        """
        if not self.available:
            logger.error("Gemini API not available")
            return None

        try:
            file_path_obj = Path(file_path)

            if not file_path_obj.exists():
                logger.error(f"File not found: {file_path}")
                return None

            display_name = display_name or file_path_obj.name

            # Upload file
            uploaded_file = genai.upload_file(
                path=file_path,
                display_name=display_name
            )

            logger.info(f"Uploaded file: {uploaded_file.uri} ({uploaded_file.name})")

            return uploaded_file.uri

        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return None

    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all uploaded files.

        Returns:
            List of file metadata dicts
        """
        if not self.available:
            return []

        try:
            files = []
            for file in genai.list_files():
                files.append({
                    "name": file.name,
                    "display_name": file.display_name,
                    "uri": file.uri,
                    "mime_type": file.mime_type,
                    "size_bytes": file.size_bytes,
                    "create_time": file.create_time.isoformat() if file.create_time else None,
                })

            return files

        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []

    def delete_file(self, file_name: str) -> bool:
        """
        Delete an uploaded file.

        Args:
            file_name: Name of file to delete

        Returns:
            True if successful
        """
        if not self.available:
            return False

        try:
            genai.delete_file(file_name)
            logger.info(f"Deleted file: {file_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False

    def generate_with_context(
        self,
        query: str,
        context: Union[str, List[str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ) -> Tuple[Optional[str], Optional[GeminiError]]:
        """
        Generate content with provided context and automatic retry on rate limits.

        Args:
            query: User query
            context: Context string or list of context strings
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_retries: Maximum number of retry attempts on retryable errors

        Returns:
            Tuple of (generated_text, error). If successful, error is None.
            If failed, generated_text is None and error contains details.
        """
        if not self.available:
            error = GeminiError(
                error_type="unavailable",
                message="The AI service is not configured. Please contact support.",
                is_retryable=False
            )
            return None, error

        # Build prompt with context
        if isinstance(context, list):
            context_str = "\n\n".join(context)
        else:
            context_str = context

        prompt_parts = []

        if system_prompt:
            prompt_parts.append(f"System Instructions:\n{system_prompt}\n")

        prompt_parts.append(f"Context:\n{context_str}\n")
        prompt_parts.append(f"Question: {query}\n")
        prompt_parts.append("Answer based on the provided context:")

        prompt = "\n".join(prompt_parts)

        return self.generate_content(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries
        )

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of Gemini API connection.

        Returns:
            Health status dict
        """
        if not self.available:
            return {
                "status": "unavailable",
                "message": "Gemini API key not configured"
            }

        try:
            # Try a simple generation
            response = self.generate_content("Test", temperature=0.0, max_tokens=10)

            if response:
                return {
                    "status": "healthy",
                    "model": self.model_name,
                    "api_key_set": bool(self.api_key)
                }
            else:
                return {
                    "status": "degraded",
                    "message": "API call failed but credentials valid"
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create singleton Gemini client"""
    global _gemini_client

    if _gemini_client is None:
        _gemini_client = GeminiClient()

    return _gemini_client


if __name__ == "__main__":
    # Test the Gemini client
    print("=" * 80)
    print("Gemini Client - Test")
    print("=" * 80)

    client = GeminiClient()

    if not client.is_available():
        print("\n❌ Gemini API not available (API key not set)")
        print("Set GEMINI_API_KEY environment variable to test")
    else:
        print("\n✅ Gemini API available")

        # Test health check
        print("\n1. Health Check:")
        health = client.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Model: {health.get('model')}")

        # Test simple generation
        print("\n2. Simple Generation:")
        response = client.generate_content(
            "What is the purpose of employment insurance in Canada? Answer in one sentence.",
            temperature=0.3,
            max_tokens=100
        )
        if response:
            print(f"   Response: {response}")
        else:
            print("   ❌ Generation failed")

        # Test with context
        print("\n3. Generation with Context:")
        context = """
        Employment Insurance (EI) provides temporary income support to unemployed Canadians
        while they look for work or upgrade their skills. Applicants must have lost their
        employment through no fault of their own and have a valid social insurance number.
        """

        response = client.generate_with_context(
            query="Who is eligible for EI?",
            context=context,
            system_prompt="You are a helpful assistant answering questions about Canadian regulations. Be concise and cite the context.",
            temperature=0.3
        )

        if response:
            print(f"   Response: {response}")
        else:
            print("   ❌ Generation failed")

    print("\n" + "=" * 80)
    print("Test complete!")
