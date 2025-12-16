# Ollama Integration Plan - LLM Provider Abstraction

## Executive Summary

This plan outlines the implementation of an Ollama client as a drop-in replacement for the Gemini client, enabling local LLM inference without API costs. The solution uses a factory pattern for seamless provider switching.

## Current State Analysis

### Existing Gemini Client Interface

The current `gemini_client.py` provides:

**Core Methods (Must be replicated):**
- `__init__(api_key, model_name)` - Initialize client
- `is_available()` → `bool` - Check availability
- `generate_content(prompt, temperature, max_tokens, ...)` → `Tuple[Optional[str], Optional[GeminiError]]`
- `generate_with_context(query, context, system_prompt, temperature, max_tokens, max_retries)` → `Tuple[Optional[str], Optional[GeminiError]]`
- `health_check()` → `Dict[str, Any]`

**Error Handling:**
- Uses `GeminiError` dataclass for structured errors
- Returns `Tuple[Optional[str], Optional[GeminiError]]` pattern
- Implements exponential backoff retry logic
- Classifies errors: rate_limit, quota_exceeded, invalid_request, network, unknown

**RAG Service Integration Points:**
```python
# rag_service.py uses these methods:
self.gemini_client = gemini_client or get_gemini_client()
if not self.gemini_client.is_available():
    # Handle unavailable
answer_text, gemini_error = self.gemini_client.generate_with_context(...)
health_status = self.gemini_client.health_check()
```

## Solution Design

### 1. Ollama Client Architecture

**File:** `backend/services/ollama_client.py`

**Key Features:**
- HTTP client for local Ollama API (port 11434)
- Compatible interface with Gemini client
- Reuse `GeminiError` dataclass (rename to `LLMError` for generality)
- No API key required (local model)
- Model: `llama3.2:3b` (already pulled in Dockerfile)

**API Endpoints:**
- `POST /api/generate` - Generate completion
- `POST /api/chat` - Chat completion
- `GET /api/tags` - List models
- `POST /api/pull` - Pull model (for health check)

### 2. LLM Provider Factory Pattern

**File:** `backend/services/llm_client_factory.py`

**Purpose:**
- Centralized provider selection based on `LLM_PROVIDER` env var
- Singleton pattern for both clients
- Abstract interface for future providers (OpenAI, Anthropic, etc.)

**Interface:**
```python
def get_llm_client(provider: Optional[str] = None) -> Union[GeminiClient, OllamaClient]:
    """
    Factory function to get appropriate LLM client.
    
    Args:
        provider: 'gemini' or 'ollama' (defaults to env LLM_PROVIDER)
    
    Returns:
        Client instance with compatible interface
    """
```

### 3. Environment Configuration

**New Variables:**
```bash
# LLM Provider Selection
LLM_PROVIDER=gemini  # Options: gemini, ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

## Implementation Steps

### Phase 1: Foundation (Refactoring)

**Step 1.1: Generalize Error Handling**
- Create `backend/services/llm_errors.py`
- Rename `GeminiError` → `LLMError` (keep backward compatibility)
- Move error classification logic to shared utilities

**Step 1.2: Create Abstract Base Class (Optional but Recommended)**
- Create `backend/services/base_llm_client.py`
- Define abstract interface for all LLM clients
- Enforce consistent method signatures

### Phase 2: Ollama Client Implementation

**Step 2.1: Create Ollama Client**
- File: `backend/services/ollama_client.py`
- Implement all methods matching Gemini interface
- HTTP client using `requests` library
- Error handling with `LLMError`

**Step 2.2: Implement Core Methods**

```python
class OllamaClient:
    def __init__(self, host: Optional[str] = None, model_name: Optional[str] = None):
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.available = self._check_availability()
    
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return any(m['name'] == self.model_name for m in models)
            return False
        except:
            return False
    
    def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        ...
    ) -> Tuple[Optional[str], Optional[LLMError]]:
        """Generate content using Ollama API"""
        # Implementation with retry logic
    
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
        # Build prompt with context
        # Call generate_content
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for Ollama service"""
        # Check Ollama availability
        # Return status dict
```

### Phase 3: Factory Pattern

**Step 3.1: Create Factory Module**
- File: `backend/services/llm_client_factory.py`

```python
from typing import Union, Optional
import os
from services.gemini_client import GeminiClient
from services.ollama_client import OllamaClient

# Singleton instances
_gemini_client: Optional[GeminiClient] = None
_ollama_client: Optional[OllamaClient] = None

def get_llm_client(provider: Optional[str] = None) -> Union[GeminiClient, OllamaClient]:
    """
    Factory function to get appropriate LLM client based on provider.
    
    Args:
        provider: 'gemini' or 'ollama' (defaults to LLM_PROVIDER env var)
    
    Returns:
        Configured LLM client instance
    
    Raises:
        ValueError: If provider is unknown
    """
    global _gemini_client, _ollama_client
    
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    
    if provider == "gemini":
        if _gemini_client is None:
            _gemini_client = GeminiClient()
        return _gemini_client
    elif provider == "ollama":
        if _ollama_client is None:
            _ollama_client = OllamaClient()
        return _ollama_client
    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Must be 'gemini' or 'ollama'")

def reset_clients():
    """Reset singleton clients (useful for testing)"""
    global _gemini_client, _ollama_client
    _gemini_client = None
    _ollama_client = None
```

### Phase 4: RAG Service Integration

**Step 4.1: Update RAG Service Constructor**

```python
# OLD:
from services.gemini_client import GeminiClient, get_gemini_client

class RAGService:
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        ...
    ):
        self.gemini_client = gemini_client or get_gemini_client()

# NEW:
from services.llm_client_factory import get_llm_client

class RAGService:
    def __init__(
        self,
        llm_client: Optional[Union[GeminiClient, OllamaClient]] = None,
        ...
    ):
        self.llm_client = llm_client or get_llm_client()
```

**Step 4.2: Update Method Calls**

```python
# Replace all instances of:
self.gemini_client.is_available()
self.gemini_client.generate_with_context(...)
self.gemini_client.health_check()

# With:
self.llm_client.is_available()
self.llm_client.generate_with_context(...)
self.llm_client.health_check()
```

### Phase 5: Configuration

**Step 5.1: Update .env.example**

Add after Gemini configuration:

```bash
# LLM Provider Selection
# Options: gemini (cloud API), ollama (local inference)
LLM_PROVIDER=gemini

# Ollama Configuration (only needed if LLM_PROVIDER=ollama)
# Ollama runs locally in the Docker container on port 11434
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# Ollama Model Selection:
# - llama3.2:3b (Default) - 3B parameters, fast, good for testing
# - llama3.2:7b - 7B parameters, better quality, slower
# - mistral:7b - Alternative 7B model
# - codellama:7b - Optimized for code
# Run 'ollama list' in container to see available models
```

**Step 5.2: Update backend/.env**

Add the same configuration to the main .env file.

### Phase 6: Dependencies

**Step 6.1: Update requirements.txt**

Add Ollama Python client:

```txt
# LLM Clients
google-generativeai>=0.3.0  # Gemini API (existing)
ollama>=0.1.0  # Ollama local inference (NEW)
```

**Alternative:** Use `requests` library (already in requirements) for HTTP calls instead of official Ollama client. This gives more control and avoids additional dependency.

### Phase 7: Testing

**Step 7.1: Unit Tests**

Create `backend/tests/test_ollama_client.py`:

```python
import pytest
from services.ollama_client import OllamaClient
from services.llm_errors import LLMError

@pytest.fixture
def ollama_client():
    return OllamaClient()

def test_ollama_availability(ollama_client):
    """Test Ollama service availability"""
    assert isinstance(ollama_client.is_available(), bool)

def test_generate_content(ollama_client):
    """Test basic content generation"""
    result, error = ollama_client.generate_content("What is 2+2?", temperature=0.1)
    
    if ollama_client.is_available():
        assert result is not None
        assert error is None
    else:
        assert result is None
        assert error is not None

def test_generate_with_context(ollama_client):
    """Test RAG-style generation with context"""
    context = "The capital of Canada is Ottawa."
    query = "What is the capital of Canada?"
    
    result, error = ollama_client.generate_with_context(
        query=query,
        context=context,
        system_prompt="Answer based on the context provided.",
        temperature=0.1
    )
    
    if ollama_client.is_available():
        assert result is not None
        assert "Ottawa" in result or "ottawa" in result.lower()
```

**Step 7.2: Integration Tests**

Create `backend/tests/test_llm_factory.py`:

```python
import pytest
import os
from services.llm_client_factory import get_llm_client, reset_clients
from services.gemini_client import GeminiClient
from services.ollama_client import OllamaClient

def test_factory_gemini_provider():
    """Test factory returns Gemini client"""
    reset_clients()
    client = get_llm_client(provider="gemini")
    assert isinstance(client, GeminiClient)

def test_factory_ollama_provider():
    """Test factory returns Ollama client"""
    reset_clients()
    client = get_llm_client(provider="ollama")
    assert isinstance(client, OllamaClient)

def test_factory_env_var(monkeypatch):
    """Test factory respects LLM_PROVIDER env var"""
    reset_clients()
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    client = get_llm_client()
    assert isinstance(client, OllamaClient)

def test_factory_singleton():
    """Test factory returns same instance"""
    reset_clients()
    client1 = get_llm_client(provider="ollama")
    client2 = get_llm_client(provider="ollama")
    assert client1 is client2
```

**Step 7.3: RAG Integration Tests**

Update `backend/tests/test_integration_rag.py`:

```python
@pytest.mark.parametrize("provider", ["gemini", "ollama"])
def test_rag_with_different_providers(provider):
    """Test RAG service works with both providers"""
    os.environ["LLM_PROVIDER"] = provider
    reset_clients()
    
    rag_service = RAGService()
    
    # Test basic question answering
    answer = rag_service.answer_question(
        question="What is employment insurance?",
        filters={"language": "en"}
    )
    
    assert answer is not None
    assert answer.question == "What is employment insurance?"
    # If provider is available, check for answer
```

## Migration Strategy

### For Existing Deployments

**Option A: Backward Compatible (Recommended)**

1. Keep both `gemini_client.py` and `ollama_client.py`
2. Default `LLM_PROVIDER=gemini` in .env
3. Existing deployments continue using Gemini
4. Users can opt-in to Ollama by changing env var

**Option B: Ollama-First**

1. Default `LLM_PROVIDER=ollama` in .env.example
2. Gemini as fallback option
3. Requires Ollama setup for new deployments

**Recommendation:** Use Option A for production stability.

## Documentation Updates

### Files to Update

1. **README.md**
   - Add section on LLM provider selection
   - Document Ollama setup and model selection
   - Performance comparison table

2. **backend/services/README.md**
   - Document factory pattern
   - LLM client interface specification
   - How to add new providers

3. **docker-compose.yml** (Already updated!)
   - Ollama service already configured ✓
   - Port 11434 exposed ✓
   - Model pulled in startup script ✓

## Rollout Checklist

### Pre-Implementation
- [x] Analyze Gemini client interface
- [x] Design Ollama client architecture
- [x] Plan factory pattern
- [x] Identify RAG integration points

### Implementation
- [ ] Create `llm_errors.py` (generalized error handling)
- [ ] Create `ollama_client.py` (core implementation)
- [ ] Create `llm_client_factory.py` (provider factory)
- [ ] Update `rag_service.py` (use factory pattern)
- [ ] Update `.env.example` (add LLM_PROVIDER config)
- [ ] Update `backend/.env` (add configuration)
- [ ] Update `requirements.txt` (add ollama dependency)

### Testing
- [ ] Unit tests for Ollama client
- [ ] Unit tests for factory pattern
- [ ] Integration tests for RAG with Ollama
- [ ] Health check endpoint testing
- [ ] Performance benchmarking (Ollama vs Gemini)

### Documentation
- [ ] Update README.md with provider selection guide
- [ ] Add Ollama setup instructions
- [ ] Document model selection options
- [ ] Add troubleshooting guide

### Deployment
- [ ] Test in development environment
- [ ] Verify Docker container startup
- [ ] Performance testing with real queries
- [ ] Load testing with concurrent requests
- [ ] Production deployment guide

## Performance Considerations

### Ollama (Local Inference)

**Pros:**
- ✅ No API costs
- ✅ No rate limits
- ✅ Data stays local (privacy)
- ✅ Predictable latency

**Cons:**
- ❌ Requires CPU/GPU resources
- ❌ Slower than cloud APIs (3B model)
- ❌ Limited model quality vs Gemini Pro
- ❌ Manual model management

### Expected Performance

**Model:** `llama3.2:3b`
- Response time: 2-5 seconds (CPU), <1s (GPU)
- Context window: 128k tokens
- Quality: Good for general Q&A, moderate for complex legal reasoning

**Recommendations:**
- Use Gemini for production (better quality)
- Use Ollama for:
  - Development/testing (no API costs)
  - Privacy-sensitive deployments
  - High-volume, cost-constrained scenarios

## Future Enhancements

### Phase 2: Additional Providers

Support for:
- OpenAI GPT-4
- Anthropic Claude
- Cohere Command
- Azure OpenAI

### Phase 3: Model Router

Intelligent routing based on:
- Query complexity
- Cost constraints
- Latency requirements
- Privacy requirements

### Phase 4: Hybrid Mode

Combine multiple providers:
- Fast model for simple queries (Ollama)
- Advanced model for complex queries (Gemini)
- Consensus mode (multiple models vote)

## Risk Mitigation

### Risk 1: Ollama Service Unavailable
**Mitigation:** Graceful fallback with clear error messages, health check monitoring

### Risk 2: Performance Degradation
**Mitigation:** Benchmarking before rollout, configurable provider per deployment

### Risk 3: Interface Incompatibility
**Mitigation:** Comprehensive test suite, abstract base class enforcement

### Risk 4: Breaking Changes
**Mitigation:** Backward compatibility, feature flags, staged rollout

## Success Metrics

- [ ] Both providers pass all RAG integration tests
- [ ] Factory pattern enables switching in <5 lines of code
- [ ] Ollama response time <5s for 95% of queries
- [ ] Zero breaking changes to existing deployments
- [ ] Documentation complete and reviewed

## Conclusion

This plan provides a comprehensive, production-ready approach to adding Ollama support while maintaining backward compatibility with Gemini. The factory pattern enables future expansion to additional LLM providers with minimal refactoring.

**Estimated Effort:** 8-12 hours
- Implementation: 4-6 hours
- Testing: 2-3 hours
- Documentation: 2-3 hours

**Priority:** Medium
**Risk:** Low (backward compatible, well-tested pattern)
