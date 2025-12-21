# API Reference

Complete REST API documentation for the Regulatory Intelligence Assistant.

**Base URL**: `http://localhost:8000/api`

**Interactive Docs**: http://localhost:8000/docs

## Authentication

**Current**: No authentication required (MVP/development mode)

**Production**: JWT bearer tokens (planned)

## Search API

### Hybrid Search

Search regulations using keyword + semantic matching.

```http
GET /api/search
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| q | string | Yes | Search query |
| limit | integer | No | Max results (default: 10) |
| offset | integer | No | Pagination offset (default: 0) |
| jurisdiction | string | No | Filter by jurisdiction |
| doc_type | string | No | Filter by type |
| date_from | string | No | Start date (YYYY-MM-DD) |
| date_to | string | No | End date (YYYY-MM-DD) |

**Example:**

```bash
curl "http://localhost:8000/api/search?q=employment+insurance&limit=5"
```

**Response:**

```json
{
  "results": [
    {
      "id": "abc123",
      "title": "Employment Insurance Act",
      "content": "...",
      "score": 0.95,
      "jurisdiction": "CA",
      "type": "legislation",
      "metadata": {...}
    }
  ],
  "total": 42,
  "took_ms": 145
}
```

### Keyword Search

Fast keyword-only search (Tier 4 PostgreSQL).

```http
GET /api/search/keyword
```

Same parameters as hybrid search. Faster but less accurate.

### Vector Search

Semantic similarity search only.

```http
GET /api/search/vector
```

Same parameters as hybrid search. Better for conceptual queries.

## RAG Q&A API

### Ask Question

Get AI-generated answers with citations.

```http
POST /api/rag/answer
```

**Request Body:**

```json
{
  "question": "Who is eligible for employment insurance?",
  "max_context_docs": 5,
  "language": "en"
}
```

**Response:**

```json
{
  "answer": "To be eligible for employment insurance...",
  "citations": [
    {
      "document_id": "abc123",
      "title": "Employment Insurance Act",
      "section": "Section 7",
      "text": "..."
    }
  ],
  "confidence": 0.87,
  "reasoning": {
    "question_analysis": "...",
    "relevant_regulations": "...",
    "requirement_mapping": "...",
    "answer_synthesis": "...",
    "confidence_assessment": "..."
  }
}
```

### Follow-up Question

Ask a follow-up in an existing conversation.

```http
POST /api/rag/follow-up
```

**Request Body:**

```json
{
  "question": "What about temporary residents?",
  "conversation_id": "conv-abc123"
}
```

## Compliance API

### Check Compliance

Validate form data against regulatory requirements.

```http
POST /api/compliance/check
```

**Request Body:**

```json
{
  "program_id": "employment-insurance",
  "workflow_type": "ei_application",
  "form_data": {
    "sin": "123-456-789",
    "hours_worked": 700,
    "residency_status": "citizen"
  }
}
```

**Response:**

```json
{
  "is_compliant": true,
  "confidence": 0.92,
  "issues": [],
  "summary": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }
}
```

### Validate Field

Real-time field validation (<50ms).

```http
POST /api/compliance/validate-field
```

**Request Body:**

```json
{
  "program_id": "employment-insurance",
  "field_name": "hours_worked",
  "field_value": 700
}
```

### Get Compliance Rules

Retrieve validation rules for a program.

```http
GET /api/compliance/rules/{program_id}
```

### Extract Requirements

Extract requirements from regulatory text.

```http
POST /api/compliance/extract-requirements
```

**Request Body:**

```json
{
  "text": "Applicants must have worked 700 hours in the last 52 weeks.",
  "context": "employment-insurance"
}
```

## NLP API

### Extract Entities

Extract structured information from legal text.

```http
POST /api/nlp/extract-entities
```

**Request Body:**

```json
{
  "text": "Permanent residents must have 700 hours of work.",
  "entity_types": ["person_type", "requirement"]
}
```

**Response:**

```json
{
  "entities": [
    {
      "type": "person_type",
      "text": "permanent residents",
      "start": 0,
      "end": 19,
      "confidence": 0.95
    },
    {
      "type": "requirement",
      "text": "700 hours of work",
      "start": 30,
      "end": 47,
      "confidence": 0.89
    }
  ]
}
```

### Classify Query Intent

Determine the intent of a user query.

```http
POST /api/nlp/classify-intent
```

**Request Body:**

```json
{
  "query": "How do I apply for employment insurance?"
}
```

**Response:**

```json
{
  "intent": "PROCEDURE",
  "confidence": 0.92,
  "entities": ["employment insurance"]
}
```

Intent types: SEARCH, QUESTION, ELIGIBILITY, PROCEDURE, DEFINITION, COMPARISON, COMPLIANCE, REFERENCE, STATISTICS

## Graph API

### Get Document

Retrieve a document from the knowledge graph.

```http
GET /api/graph/documents/{document_id}
```

### Find Related

Find documents related by graph relationships.

```http
GET /api/graph/related/{document_id}
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| max_depth | integer | No | Traversal depth (default: 2) |
| relationship_types | string[] | No | Filter by relationship type |

### Search Graph

Full-text search across the knowledge graph.

```http
POST /api/graph/search
```

**Request Body:**

```json
{
  "query": "employment insurance",
  "node_types": ["Legislation", "Section"],
  "limit": 10
}
```

## Health & Status API

### Overall Health

Check system health.

```http
GET /api/health
```

**Response:**

```json
{
  "status": "healthy",
  "services": {
    "postgres": "up",
    "neo4j": "up",
    "elasticsearch": "up",
    "redis": "up"
  },
  "version": "1.4.3"
}
```

### Service-Specific Health

```http
GET /api/health/postgres
GET /api/health/neo4j
GET /api/health/elasticsearch
GET /api/health/redis
```

### Statistics

Get system statistics.

```http
GET /api/stats
```

**Response:**

```json
{
  "documents": {
    "regulations": 1827,
    "sections": 275995,
    "total": 277812
  },
  "graph": {
    "nodes": 278858,
    "relationships": 470353
  },
  "indexes": {
    "elasticsearch": 2,
    "postgresql_fts": 4,
    "neo4j_fulltext": 3,
    "neo4j_range": 16
  }
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Query parameter 'q' is required",
    "details": {...}
  }
}
```

**HTTP Status Codes:**

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (future)
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded (future)
- `500` - Internal Server Error

## Rate Limiting

**Current**: No rate limiting (MVP)

**Production**: 1000 requests/hour for authenticated users

## Pagination

Endpoints supporting pagination use `limit` and `offset` parameters:

```http
GET /api/search?q=test&limit=20&offset=40
```

**Response includes:**

```json
{
  "results": [...],
  "total": 150,
  "limit": 20,
  "offset": 40,
  "has_more": true
}
```

## Performance Targets

| Endpoint Type | Target Latency |
|---------------|----------------|
| Search (keyword) | <100ms |
| Search (vector) | <400ms |
| Search (hybrid) | <500ms |
| RAG Q&A | <3s |
| Field Validation | <50ms |
| Full Compliance | <200ms |
| NLP Extraction | <100ms |
| Graph Query | <200ms |

## OpenAPI Specification

Download machine-readable API spec:

```http
GET /openapi.json
```

Import into:
- Postman
- Insomnia
- Swagger UI
- Code generators
