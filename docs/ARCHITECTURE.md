# Architecture Overview

## System Design

### Tech Stack

- **Frontend**: React 19 + TypeScript 5.9 + Vite 7 + Tailwind CSS v4
- **State Management**: Zustand 5.0 + TanStack Query v5
- **Backend**: FastAPI (Python 3.11+)
- **Graph Database**: Neo4j 5.15 (with APOC + GDS plugins)
- **Search**: Elasticsearch (keyword + vector)
- **Relational DB**: PostgreSQL 16 with full-text search
- **Cache**: Redis
- **AI Services**: Gemini API (RAG + embeddings)
- **Database Migrations**: Alembic

## System Architecture

```
┌─────────────────┐
│  React Frontend │
│  (Port 5173)    │
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│   FastAPI API   │
│  (Port 8000)    │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Search │ │  RAG   │ │ Graph  │ │Compliance│
│Service │ │Service │ │Query   │ │ Checker │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │
     └──────────┴──────────┴──────────┘
                │
         ┌──────┴───────┬────────────┐
         ▼              ▼            ▼
    ┌────────┐   ┌──────────┐  ┌────────┐
    │Postgres│   │Elasticsearch│ │ Neo4j  │
    │ 5432   │   │   9200    │  │  7474  │
    └────────┘   └──────────┘  └────────┘
```

## Multi-Tier Search Architecture

### Tier 1: Elasticsearch (Primary)
- **Type**: Hybrid search (BM25 + Vector)
- **Target**: <500ms latency
- **Use Case**: Initial semantic search
- **Fallback**: Tier 2 if no results

### Tier 2: Elasticsearch Sections
- **Type**: Section-level full-text search
- **Target**: <400ms latency
- **Use Case**: More granular search
- **Fallback**: Tier 3 if insufficient results

### Tier 3: Neo4j Graph
- **Type**: Graph traversal + full-text
- **Target**: <200ms latency
- **Use Case**: Relationship-aware search
- **Enhancements**:
  - Legal synonyms query expansion
  - Snippet extraction with highlights
  - Fuzzy similarity search
  - Score boosting for matched terms

### Tier 4: PostgreSQL FTS
- **Type**: Full-text search with GIN indexes
- **Target**: <50ms latency
- **Use Case**: Fast keyword fallback
- **Enhancements**:
  - Pre-generated search_vector columns
  - pg_trgm fuzzy matching
  - ts_headline snippet generation
  - JSONB metadata queries

### Tier 5: Metadata-Only
- **Type**: Basic field matching
- **Target**: <20ms latency
- **Use Case**: Last resort fallback

## Core Services

### Search Service
- Multi-tier search orchestration
- Result deduplication and ranking
- Faceted filtering (jurisdiction, date, type)
- Performance: 397/397 tests passing

### RAG Service
- Chain-of-Thought reasoning (5-step process)
- Citation extraction and linking
- Confidence scoring (4 factors)
- In-memory caching (24h TTL, LRU eviction)

### Compliance Checker
- 3-tier architecture (Extractor → Engine → Checker)
- 8 validation types
- Real-time field validation (<50ms)
- Rule caching (1-hour TTL)

### Graph Service
- Neo4j knowledge graph operations
- CRUD for Legislation, Sections, Regulations
- Relationship traversal
- Full-text search across graph nodes

### NLP Service
- Legal entity extraction
- Query intent classification (9 intents)
- Named entity recognition
- Legal synonym expansion

## Data Flow

### 1. Search Query Flow
```
User Query → Query Parser → Search Service
                           ↓
                    Tier 1: Elasticsearch
                           ↓ (fallback)
                    Tier 2: ES Sections
                           ↓ (fallback)
                    Tier 3: Neo4j Graph
                           ↓ (fallback)
                    Tier 4: PostgreSQL
                           ↓ (fallback)
                    Tier 5: Metadata-Only
                           ↓
                    Results → Frontend
```

### 2. RAG Q&A Flow
```
Question → RAG Service
          ↓
    Search for Context (Multi-Tier)
          ↓
    Chain-of-Thought Reasoning
          ↓
    Generate Answer (Gemini API)
          ↓
    Extract Citations
          ↓
    Calculate Confidence
          ↓
    Return to User
```

### 3. Compliance Check Flow
```
Form Data → Compliance Checker
           ↓
    Extract Requirements
           ↓
    Apply Validation Rules
           ↓
    Check Each Field
           ↓
    Generate Report
           ↓
    Return Issues + Confidence
```

## Database Schemas

### PostgreSQL Tables
- `regulations` - Core regulatory documents (1,817 rows)
- `sections` - Document sections (275,995 rows)
- `citations` - Cross-references with CASCADE DELETE
- `amendments` - Change tracking
- `metadata_cache` - Query caching
- `compliance_rules` - Validation rules

### Neo4j Graph Schema
- **Nodes**: Legislation, Section, Regulation, Policy, Program, Situation
- **Relationships**: HAS_SECTION, REFERENCES, IMPLEMENTS, APPLIES_TO, PART_OF
- **Indexes**: 3 fulltext + 16 range indexes
- **Data**: 278,858 nodes, 470,353 relationships

### Elasticsearch Indexes
- `regulations` - Document-level index
- `sections` - Section-level index
- **Total**: 277,812 documents indexed

## Performance Metrics

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Keyword Search | <100ms | ~80ms | ✅ |
| Vector Search | <400ms | ~350ms | ✅ |
| Hybrid Search | <500ms | ~450ms | ✅ |
| Neo4j Graph Query | <200ms | ~150ms | ✅ |
| PostgreSQL FTS | <50ms | ~35ms | ✅ |
| RAG Q&A | <3s | ~2.5s | ✅ |
| Field Validation | <50ms | ~35ms | ✅ |
| Full Compliance | <200ms | ~175ms | ✅ |

## Deployment

### Docker Services
- **backend**: FastAPI application
- **frontend**: Vite dev server (prod: Nginx)
- **postgres**: PostgreSQL 16
- **neo4j**: Neo4j 5.15 Community
- **elasticsearch**: Elasticsearch 8.x
- **redis**: Redis 7.x

### Environment Variables
See `.env.example` for full list:
- `GEMINI_API_KEY` - Required for RAG
- `DATABASE_URL` - PostgreSQL connection
- `NEO4J_URI` - Neo4j connection
- `ELASTICSEARCH_URL` - ES connection
- `REDIS_URL` - Redis connection

## Security Considerations

### Current Status (MVP)
- ✅ No authentication (development mode)
- ✅ CORS enabled for localhost
- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (SQLAlchemy ORM)

### Production TODO
- [ ] JWT authentication
- [ ] Role-based access control (RBAC)
- [ ] Rate limiting (1000 req/hour)
- [ ] API key management
- [ ] Audit logging
- [ ] HTTPS enforcement
- [ ] Secrets management (Vault)

## Monitoring & Observability

### Health Checks
- `GET /api/health` - Overall system health
- `GET /api/health/postgres` - Database connectivity
- `GET /api/health/neo4j` - Graph database status
- `GET /api/health/elasticsearch` - Search service status

### Metrics (Future)
- Prometheus metrics endpoint
- Grafana dashboards
- Request latency tracking
- Error rate monitoring
- Resource utilization

## See Also

- [Data Ingestion](./DATA_INGESTION.md)
- [API Reference](./API_REFERENCE.md)
- [Development Guide](./DEVELOPMENT.md)
- [Testing Strategy](./TESTING.md)
