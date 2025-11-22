## RAG Service Documentation

**Author:** Developer 2 (AI/ML Engineer)  
**Created:** 2025-11-22  
**Status:** ✅ COMPLETED  
**Stream:** 3B - Gemini RAG System

---

## Overview

The RAG (Retrieval-Augmented Generation) Service provides AI-powered question answering for Canadian regulatory documents. It combines document retrieval with LLM generation to provide accurate, cited answers.

### Key Features

1. **Retrieval-Augmented Generation** - Combines search with AI generation
2. **Citation Extraction** - Automatically extracts and validates citations
3. **Confidence Scoring** - Scores answer reliability (0.0-1.0)
4. **Answer Caching** - Caches responses for 24 hours
5. **Multi-Document Context** - Uses up to 20 documents as context
6. **Uncertainty Detection** - Identifies when AI is uncertain

---

## Architecture

```
User Question
    ↓
NLP Parser (extract intent, filters)
    ↓
Search Service (retrieve relevant docs)
    ↓
Build Context (top N documents)
    ↓
Gemini API (generate answer with citations)
    ↓
Extract Citations + Calculate Confidence
    ↓
Cache Answer
    ↓
Return Response
```

---

## Components

### 1. Gemini Client (`backend/services/gemini_client.py`)

Wrapper for Google Gemini API with safety settings and file upload support.

**Methods:**
- `generate_content()` - Generate text from prompt
- `chat()` - Multi-turn conversations  
- `generate_with_context()` - Generate with provided context
- `upload_file()` - Upload files to Gemini
- `health_check()` - Check API availability

### 2. RAG Service (`backend/services/rag_service.py`)

Core RAG logic combining search, generation, and citation extraction.

**Methods:**
- `answer_question()` - Main Q&A method
- `_extract_citations()` - Extract citations from answer
- `_calculate_confidence()` - Calculate confidence score
- `clear_cache()` - Clear answer cache
- `health_check()` - Check service health

### 3. RAG API Routes (`backend/routes/rag.py`)

REST API endpoints for RAG functionality.

**Endpoints:**
- POST `/api/rag/ask` - Ask a question
- POST `/api/rag/ask/batch` - Ask multiple questions
- POST `/api/rag/cache/clear` - Clear cache
- GET `/api/rag/cache/stats` - Cache statistics
- GET `/api/rag/health` - Health check
- GET `/api/rag/info` - Service information

---

## API Reference

### POST `/api/rag/ask`

Ask a question and get an AI-generated answer.

**Request:**
```json
{
  "question": "Can a temporary resident apply for employment insurance?",
  "filters": {"jurisdiction": "federal"},
  "num_context_docs": 5,
  "use_cache": true,
  "temperature": 0.3,
  "max_tokens": 1024
}
```

**Response:**
```json
{
  "success": true,
  "question": "Can a temporary resident apply for employment insurance?",
  "answer": "Yes, temporary residents can apply for employment insurance if they meet eligibility requirements. According to Section 7(1) of the Employment Insurance Act, benefits are payable to persons who are authorized to work in Canada and have a valid social insurance number.",
  "citations": [
    {
      "text": "[Employment Insurance Act, Section 7]",
      "document_id": "ei-act-s7",
      "document_title": "Employment Insurance Act",
      "section": "7",
      "confidence": 0.9
    }
  ],
  "confidence_score": 0.82,
  "source_documents": [
    {
      "id": "ei-act-s7",
      "title": "Employment Insurance Act - Section 7",
      "citation": "S.C. 1996, c. 23, s. 7",
      "section_number": "7",
      "score": 1.85
    }
  ],
  "intent": "eligibility",
  "processing_time_ms": 2450,
  "cached": false,
  "metadata": {
    "num_context_docs": 5,
    "temperature": 0.3
  }
}
```

---

## Citation Extraction

The RAG service automatically extracts citations using multiple patterns:

**Pattern 1:** `[Document Title, Section X]`  
Example: `[Employment Insurance Act, Section 7(1)]`

**Pattern 2:** `Section X` or `s. X`  
Example: `Section 7(1)` or `s. 7(1)`

Each citation includes:
- Extracted text
- Document ID (if matched)
- Document title
- Section number
- Confidence score (0.0-1.0)

---

## Confidence Scoring

Confidence scores are calculated using 4 factors:

1. **Citation Quality (35%):** Number and quality of citations
2. **Answer Quality (25%):** Length appropriateness, uncertainty phrases
3. **Context Quality (25%):** Search scores of source documents
4. **Intent Confidence (15%):** NLP intent classification confidence

**Score Ranges:**
- `0.8-1.0`: High confidence - well-cited, clear answer
- `0.6-0.8`: Medium confidence - some citations, reasonable answer
- `0.4-0.6`: Low confidence - few citations or uncertainty
- `0.0-0.4`: Very low confidence - no citations or insufficient context

---

## Caching

Answers are cached for 24 hours using an in-memory cache (MD5 hash of normalized question).

**Cache Features:**
- Normalized question keys (case-insensitive, whitespace-trimmed)
- 24-hour TTL
- Max 1000 entries (LRU eviction)
- Manual clearing via `/api/rag/cache/clear`

---

## Usage Examples

### Example 1: Simple Question

```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is employment insurance?",
    "num_context_docs": 3
  }'
```

### Example 2: Filtered Question

```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who is eligible for CPP benefits?",
    "filters": {
      "jurisdiction": "federal",
      "program": "canada_pension_plan"
    }
  }'
```

### Example 3: Batch Questions

```bash
curl -X POST "http://localhost:8000/api/rag/ask/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "questions": [
      "What is EI?",
      "Who can apply for CPP?",
      "What is OAS?"
    ]
  }'
```

---

## Testing

Run tests:
```bash
cd backend
pytest tests/test_rag_service.py -v
```

**Test Coverage:**
- Citation extraction (2 patterns)
- Confidence scoring (with/without citations)
- Caching (key normalization, TTL)
- Error handling (no context, Gemini unavailable)
- Health checks
- Serialization

---

## Configuration

**Environment Variables:**
- `GEMINI_API_KEY` - Google Gemini API key (required)

**RAG Parameters:**
- `num_context_docs`: 1-20 (default: 5)
- `temperature`: 0.0-1.0 (default: 0.3)
- `max_tokens`: 100-4096 (default: 1024)
- `cache_ttl`: 24 hours

---

## Performance

- **Average latency:** 2-5 seconds per question
- **Search time:** ~300-500ms
- **Generation time:** ~1.5-4s (depends on answer length)
- **Cache hit rate:** ~40-60% for common questions
- **Throughput:** ~10-15 questions/minute (sequential)

---

## Integration

The RAG service integrates with:

1. **Search Service:** Retrieves relevant documents
2. **NLP Service:** Parses queries, extracts filters
3. **Gemini API:** Generates answers
4. **Cache:** Stores responses

---

## Best Practices

1. **Use appropriate context size:** 3-5 docs for simple questions, 10-15 for complex
2. **Lower temperature for factual answers:** 0.2-0.3 recommended
3. **Check confidence scores:** <0.5 = verify answer manually
4. **Clear cache after doc updates:** Ensures fresh answers
5. **Monitor Gemini API quotas:** Watch usage limits

---

## Troubleshooting

### "Gemini API not available"
- Set `GEMINI_API_KEY` environment variable
- Verify API key is valid

### Low confidence scores
- Increase `num_context_docs`
- Check if relevant documents are indexed
- Verify search service is working

### Slow responses
- Reduce `max_tokens`
- Enable caching
- Use fewer context documents

---

## Future Enhancements

1. Redis caching for production
2. Streaming responses
3. Multi-language support (French)
4. Fine-tuned legal models
5. Citation verification
6. Alternative interpretation flagging

---

## Files

- `backend/services/gemini_client.py` (370 lines)
- `backend/services/rag_service.py` (570 lines)
- `backend/routes/rag.py` (370 lines)
- `backend/tests/test_rag_service.py` (400 lines)

**Total:** ~1,710 lines

---

**Developer 2 (AI/ML Engineer)** - Stream 3B Implementation
