#!/usr/bin/env python3
"""
Ollama Integration Test Script

This script tests the Ollama client implementation and factory pattern.
Run this script after starting Ollama to verify the integration works.

Usage:
    python test_ollama_integration.py

Environment Variables:
    LLM_PROVIDER - Set to 'ollama' to test Ollama (default: gemini)
    OLLAMA_HOST - Ollama host URL (default: http://localhost:11434)
    OLLAMA_MODEL - Model name (default: llama3.2:3b)

Author: Assistant
Created: 2025-12-16
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path for imports
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

try:
    from services.ollama_client import OllamaClient, LLMError
    from services.llm_client_factory import get_llm_client, get_gemini_client, health_check_all_providers
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory and dependencies are installed.")
    sys.exit(1)


def test_ollama_client_direct():
    """Test OllamaClient directly"""
    print("🧪 Testing OllamaClient directly...")
    
    client = OllamaClient()
    print(f"   Host: {client.host}")
    print(f"   Model: {client.model_name}")
    
    # Test availability
    print("   Testing availability...")
    is_available = client.is_available()
    print(f"   ✅ Available: {is_available}" if is_available else f"   ❌ Available: {is_available}")
    
    if not is_available:
        print("   ⚠️  Ollama service is not available. Make sure:")
        print("      - Ollama is running: ollama serve")
        print("      - Model is pulled: ollama pull llama3.2:3b")
        return False
    
    # Test health check
    print("   Testing health check...")
    health = client.health_check()
    print(f"   Status: {health.get('status', 'unknown')}")
    
    # Test generation
    print("   Testing content generation...")
    try:
        result, error = client.generate_content(
            "Say hello in one word only.",
            temperature=0.1,
            max_tokens=5
        )
        
        if error:
            print(f"   ❌ Generation failed: {error.message}")
            return False
        else:
            print(f"   ✅ Generated: '{result}'")
    
    except Exception as e:
        print(f"   ❌ Generation error: {e}")
        return False
    
    # Test context generation
    print("   Testing context-based generation...")
    try:
        result, error = client.generate_with_context(
            query="What is the main topic?",
            context="This document discusses renewable energy policies.",
            system_prompt="You are a helpful assistant.",
            temperature=0.1,
            max_tokens=10
        )
        
        if error:
            print(f"   ❌ Context generation failed: {error.message}")
            return False
        else:
            print(f"   ✅ Generated with context: '{result}'")
    
    except Exception as e:
        print(f"   ❌ Context generation error: {e}")
        return False
    
    return True


def test_factory_pattern():
    """Test the factory pattern"""
    print("\n🏭 Testing LLM Factory Pattern...")
    
    # Test with explicit provider
    print("   Testing explicit Ollama provider...")
    try:
        client = get_llm_client("ollama")
        print(f"   ✅ Got client: {type(client).__name__}")
    except Exception as e:
        print(f"   ❌ Factory error: {e}")
        return False
    
    # Test backward compatibility
    print("   Testing backward compatibility (get_gemini_client)...")
    original_provider = os.environ.get("LLM_PROVIDER")
    
    try:
        # Test with LLM_PROVIDER=ollama
        os.environ["LLM_PROVIDER"] = "ollama"
        client = get_gemini_client()  # Should return Ollama client
        print(f"   ✅ Backward compatible client: {type(client).__name__}")
        
        # Test health check all providers
        print("   Testing health check for all providers...")
        health_results = health_check_all_providers()
        for provider, health in health_results.items():
            status = health.get("status", "unknown")
            print(f"   {provider}: {status}")
    
    except Exception as e:
        print(f"   ❌ Factory test error: {e}")
        return False
    
    finally:
        # Restore original environment
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        elif "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]
    
    return True


def test_environment_switching():
    """Test switching between providers"""
    print("\n🔄 Testing Environment Provider Switching...")
    
    original_provider = os.environ.get("LLM_PROVIDER")
    
    try:
        # Test Ollama
        os.environ["LLM_PROVIDER"] = "ollama"
        ollama_client = get_llm_client()
        print(f"   LLM_PROVIDER=ollama -> {type(ollama_client).__name__}")
        
        # Test Gemini (default)
        if "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]
        gemini_client = get_llm_client()
        print(f"   LLM_PROVIDER=default -> {type(gemini_client).__name__}")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Environment switching error: {e}")
        return False
    
    finally:
        # Restore original environment
        if original_provider:
            os.environ["LLM_PROVIDER"] = original_provider
        elif "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]


def main():
    """Main test function"""
    print("🚀 Ollama Integration Test Suite")
    print("=" * 50)
    
    # Show current environment
    print(f"LLM_PROVIDER: {os.environ.get('LLM_PROVIDER', 'not set')}")
    print(f"OLLAMA_HOST: {os.environ.get('OLLAMA_HOST', 'http://localhost:11434')}")
    print(f"OLLAMA_MODEL: {os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')}")
    print()
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Direct Ollama client
    if test_ollama_client_direct():
        tests_passed += 1
    
    # Test 2: Factory pattern
    if test_factory_pattern():
        tests_passed += 1
    
    # Test 3: Environment switching
    if test_environment_switching():
        tests_passed += 1
    
    print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Ollama integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())