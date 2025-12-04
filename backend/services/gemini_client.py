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
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                logger.warning(f"No usage_metadata in response for {operation}")
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
        stop_sequences: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate content using Gemini API.

        Args:
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: List of sequences to stop generation

        Returns:
            Generated text or None if error
        """
        if not self.available:
            logger.error("Gemini API not available")
            return None

        try:
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

            return self._extract_text_from_response(response)

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return None

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
            return response.text
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
        max_tokens: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate content with provided context.

        Args:
            query: User query
            context: Context string or list of context strings
            system_prompt: Optional system instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response or None if error
        """
        if not self.available:
            return None

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
            max_tokens=max_tokens
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
