# Development Guide

Guide for developers working on the Regulatory Intelligence Assistant.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git
- VS Code (recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd regulatory-intelligence-assistant

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Start services
docker compose up -d

# Install backend dependencies (local development)
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install
```

### Development Workflow

#### Backend Development

```bash
# Backend runs in Docker with hot reload enabled
# View logs
docker compose logs -f backend

# Restart after changes (if needed)
docker compose restart backend

# Run backend locally (outside Docker - optional)
cd backend
python -m venv venv
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Run specific test file
pytest tests/test_search_service.py -v

# Run with coverage
pytest --cov=services --cov-report=html

# Format code
black .
isort .

# Lint
pylint services/ routes/
mypy services/
```

#### Frontend Development

```bash
# Run frontend dev server
cd frontend
npm run dev

# Run tests
npm test

# Run E2E tests
npm run test:e2e

# Build for production
npm run build

# Lint and format
npm run lint
npm run format
```

## Project Structure

### Backend (`backend/`)

```
backend/
├── main.py                     # FastAPI app entry
├── database.py                 # SQLAlchemy setup
│
├── scripts/                    # Utility scripts
│   ├── init_data.py           # Intelligent data loader (NEW)
│   ├── data_summary.sh        # Database statistics
│   ├── deprecated/            # Old scripts (archived)
│
├── services/                   # Business logic
│   ├── compliance_checker.py  # Compliance validation
│   ├── document_parser.py     # Document parsing
│   ├── gemini_client.py       # AI integration
│   ├── graph_builder.py       # Graph construction
│   ├── graph_service.py       # Neo4j operations
│   ├── legal_nlp.py           # NLP processing
│   ├── postgres_search_service.py  # PostgreSQL FTS
│   ├── query_parser.py        # Intent classification
│   ├── rag_service.py         # Q&A system
│   └── search_service.py      # Multi-tier search
│
├── routes/                    # API endpoints
│   ├── search.py             # Search API
│   ├── rag.py                # Q&A API
│   ├── compliance.py         # Compliance API
│   ├── graph.py              # Graph API
│   └── nlp.py                # NLP API
│
├── models/                    # Data models
│   ├── models.py             # SQLAlchemy ORM
│   └── document_models.py    # Pydantic schemas
│
├── tests/                     # Test suite
│   ├── conftest.py           # Pytest configuration
│   ├── test_search_service.py
│   ├── test_rag_service.py
│   └── ...
│
├── ingestion/                # Data ingestion
│   ├── data_pipeline.py      # Main pipeline
│   ├── canadian_law_xml_parser.py
│   └── download_canadian_laws.py
│
└── alembic/                  # Database migrations
    └── versions/
```

### Frontend (`frontend/`)

```
frontend/
├── src/
│   ├── main.tsx              # App entry
│   ├── App.tsx               # Root component
│   │
│   ├── pages/                # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Search.tsx
│   │   ├── Chat.tsx
│   │   └── Compliance.tsx
│   │
│   ├── components/           # Reusable components
│   │   ├── SearchBar.tsx
│   │   ├── ResultCard.tsx
│   │   ├── ConfidenceBadge.tsx
│   │   └── ...
│   │
│   ├── store/                # Zustand stores
│   │   ├── searchStore.ts
│   │   ├── chatStore.ts
│   │   └── complianceStore.ts
│   │
│   ├── services/             # API clients
│   │   ├── api.ts            # Axios setup
│   │   ├── searchService.ts
│   │   ├── ragService.ts
│   │   └── complianceService.ts
│   │
│   └── types/                # TypeScript definitions
│       ├── search.ts
│       ├── rag.ts
│       └── compliance.ts
│
└── e2e/                      # Playwright E2E tests
    ├── search.spec.ts
    ├── chat.spec.ts
    └── compliance.spec.ts
```

## Adding New Features

### 1. Backend Service

```python
# backend/services/my_service.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MyService:
    """Service for doing something awesome."""
    
    def __init__(self):
        self.cache = {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data and return results."""
        logger.info(f"Processing data: {data}")
        
        # Your logic here
        result = {"status": "success"}
        
        return result
```

### 2. API Route

```python
# backend/routes/my_route.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.my_service import MyService

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])
service = MyService()

class MyRequest(BaseModel):
    data: str

class MyResponse(BaseModel):
    result: str
    status: str

@router.post("/process", response_model=MyResponse)
async def process(request: MyRequest):
    """Process request and return response."""
    try:
        result = service.process({"data": request.data})
        return MyResponse(result=result["data"], status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Register Route

```python
# backend/main.py
from routes import my_route

app.include_router(my_route.router)
```

### 4. Add Tests

```python
# backend/tests/test_my_service.py
import pytest
from services.my_service import MyService

def test_my_service_process():
    service = MyService()
    result = service.process({"data": "test"})
    
    assert result["status"] == "success"
    assert "data" in result
```

### 5. Frontend Integration

```typescript
// frontend/src/services/myService.ts
import api from './api';

export interface MyRequest {
  data: string;
}

export interface MyResponse {
  result: string;
  status: string;
}

export const processData = async (
  data: string
): Promise<MyResponse> => {
  const response = await api.post<MyResponse>('/my-feature/process', {
    data
  });
  return response.data;
};
```

## Database Migrations

### Create Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "add_my_table"

# Create empty migration
alembic revision -m "add_custom_logic"
```

### Edit Migration

```python
# backend/alembic/versions/xxxxx_add_my_table.py
def upgrade():
    op.create_table(
        'my_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )
    
    op.create_index('idx_my_table_name', 'my_table', ['name'])

def downgrade():
    op.drop_table('my_table')
```

### Apply Migration

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Apply specific migration
docker compose exec backend alembic upgrade +1

# Rollback last migration
docker compose exec backend alembic downgrade -1

# View migration history
docker compose exec backend alembic history
```

## Testing

### Backend Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test
pytest tests/test_search_service.py::test_keyword_search -v

# Run with markers
pytest -m "not slow"

# Run failed tests only
pytest --lf
```

### Frontend Testing

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e

# E2E in UI mode
npm run test:e2e:ui

# Coverage
npm run test:coverage
```

### Test Data

```bash
# Load test data (10 documents for quick testing)
docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive

# Check data status
bash backend/scripts/data_summary.sh

# Generate test fixtures
docker compose exec backend python tests/generate_fixtures.py
```

## Debugging

### Backend Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb (better)
import ipdb; ipdb.set_trace()

# View logs
docker compose logs -f backend

# Interactive shell
docker compose exec backend python
>>> from services.search_service import SearchService
>>> service = SearchService()
>>> service.search("test")
```

### Frontend Debugging

```typescript
// Browser console
console.log('Debug:', data);
console.table(results);
debugger;  // Browser breakpoint

// React DevTools
// Install: https://react.dev/learn/react-developer-tools

// Network tab
// View API calls and responses
```

## Code Quality

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Linting

```bash
# Backend
black backend/
isort backend/
pylint backend/services/
mypy backend/services/

# Frontend
npm run lint
npm run format
```

### Type Checking

```bash
# Backend (mypy)
cd backend
mypy services/ routes/

# Frontend (TypeScript)
cd frontend
npm run type-check
```

## Performance Profiling

### Backend Profiling

```python
# Add profiling decorator
from functools import wraps
import time

def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__}: {duration:.3f}s")
        return result
    return wrapper

@profile
def my_slow_function():
    # Your code
    pass
```

### Database Query Profiling

```python
# Enable SQL logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# View query execution time
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, params, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    print(f"Query: {total:.3f}s - {statement[:100]}")
```

## Common Tasks

### Add New Validation Rule

```python
# backend/services/compliance_checker.py
VALIDATION_RULES = {
    "my_program": {
        "field_name": {
            "type": "pattern",
            "pattern": r"^\d{3}-\d{3}-\d{3}$",
            "message": "Must be XXX-XXX-XXX format"
        }
    }
}
```

### Add New Query Intent

```python
# backend/services/query_parser.py
class QueryIntent(Enum):
    MY_NEW_INTENT = "my_new_intent"

# Add to intent patterns
INTENT_PATTERNS = {
    QueryIntent.MY_NEW_INTENT: [
        r"pattern1",
        r"pattern2"
    ]
}
```

### Add New Search Tier

```python
# backend/services/search_service.py
async def tier_6_custom_search(self, query: str) -> List[Dict]:
    """Custom search tier."""
    # Your implementation
    return results

# Add to fallback chain
results = await self.tier_1_elasticsearch(query)
if not results:
    results = await self.tier_6_custom_search(query)
```

## Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
ELASTICSEARCH_URL=http://localhost:9200
REDIS_URL=redis://localhost:6379

# AI Services
GEMINI_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434

# App Config
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:5173
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
```

## See Also

- [Quick Start](./QUICKSTART.md)
- [Architecture](./ARCHITECTURE.md)
- [API Reference](./API_REFERENCE.md)
- [Testing Guide](../docs/testing/README.md)
