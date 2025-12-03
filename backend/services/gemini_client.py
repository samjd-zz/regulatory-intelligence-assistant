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
                # Extract text from all parts
                if hasattr(response, 'candidates') and response.candidates:
                    texts = []
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    texts.append(part.text)
                    
                    if texts:
                        return ' '.join(texts)
                
                # If that doesn't work, try response.parts directly
                if hasattr(response, 'parts'):
                    texts = [part.text for part in response.parts if hasattr(part, 'text')]
                    if texts:
                        return ' '.join(texts)
                
                logger.error("Could not extract text from multi-part response")
                return None
                
            except Exception as extract_error:
                logger.error(f"Failed to extract text from multi-part response: {extract_error}")
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
