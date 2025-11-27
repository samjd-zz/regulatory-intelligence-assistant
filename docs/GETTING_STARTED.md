# Getting Started - Regulatory Intelligence Assistant

## Quick Start Guide

This guide will help you set up and run the Regulatory Intelligence Assistant system, which includes:

- ✅ Document Parser & Ingestion (PostgreSQL)
- ✅ Neo4j Knowledge Graph
- ✅ REST API
- ✅ Database migrations

## Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Neo4j 5.15 (Community Edition, provided via Docker)
- Docker & Docker Compose (recommended)

## Step 1: Start Services

### Using Docker Compose (Recommended)

```bash
# Start PostgreSQL, Neo4j, Redis, and Elasticsearch
docker compose up -d

# Verify services are running
docker compose ps
```

Expected output:

```
NAME                     STATUS       PORTS
postgres                 Up           5432->5432
neo4j                    Up           7474->7474, 7687->7687
redis                    Up           6379->6379
elasticsearch            Up           9200->9200
```

### Access Neo4j Browser

Open http://localhost:7474 in your browser.

Default credentials:

- Username: `neo4j`
- Password: `password123`

## Step 2: Set Up Python Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/regulatory_db

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Redis
REDIS_URL=redis://localhost:6379

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# API
API_PORT=8000
DEBUG=True
```

## Step 4: Initialize Databases

### PostgreSQL Setup

```bash
cd backend

# Run database migrations
alembic upgrade head
```

You should see:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 001_initial_schema
INFO  [alembic.runtime.migration] Running upgrade 001_initial_schema -> 002_document_models
```

This creates:

- ✅ 6 document tables (documents, sections, subsections, clauses, cross_references, metadata)
- ✅ ENUMs for document types and statuses
- ✅ Indexes for performance
- ✅ Foreign key constraints

### Neo4j Setup

```bash
cd backend

# Initialize Neo4j schema
python scripts/init_neo4j.py
```

This creates:

- ✅ 6 node types (Legislation, Section, Regulation, Policy, Program, Situation)
- ✅ 9 relationship types (HAS_SECTION, REFERENCES, IMPLEMENTS, etc.)
- ✅ Constraints and indexes
- ✅ Full-text search indexes

### Seed Neo4j with Sample Data

```bash
cd backend

# Load 15+ Canadian federal regulations
python scripts/seed_graph_data.py
```

This adds:

- ✅ 15 legislation documents (EI Act, CPP, OAS, IRPA, etc.)
- ✅ 2 regulations
- ✅ 5 programs
- ✅ 5 situations
- ✅ Multiple relationships

### Verify Neo4j Graph

```bash
cd backend

# Verify the graph structure
python scripts/verify_graph.py
```

Expected output:

```
✅ Graph structure verified!
📊 Node counts:
  - Legislation: 15
  - Section: XX
  - Regulation: 2
  - Policy: X
  - Program: 5
  - Situation: 5
📊 Relationship counts: XX
```

## Step 5: Start the API Server

```bash
cd backend

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Step 6: Test the System

### Option A: Interactive API Documentation

Open http://localhost:8000/docs in your browser.

This provides:

- ✅ Interactive API testing
- ✅ Request/response schemas
- ✅ Authentication testing
- ✅ Try-it-out functionality

### Option B: Automated Test Script

```bash
cd backend

# Run the test suite
python scripts/test_document_api.py
```

This will:

- ✅ Upload a sample Employment Insurance Act document
- ✅ Extract sections, subsections, and clauses
- ✅ Detect cross-references
- ✅ Test all API endpoints
- ✅ Display statistics

### Option C: Manual Testing with cURL

```bash
# Upload a document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@sample_regulation.txt" \
  -F "document_type=legislation" \
  -F "jurisdiction=federal" \
  -F "authority=Parliament of Canada" \
  -F "document_number=S.C. 1996, c. 23" \
  -F "effective_date=1996-06-30"

# List all documents
curl http://localhost:8000/documents

# Get statistics
curl http://localhost:8000/documents/statistics/summary

# Search documents
curl -X POST http://localhost:8000/documents/search \
  -H "Content-Type: application/json" \
  -d '{"query": "employment insurance", "document_type": "legislation"}'
```

## Step 7: Explore Neo4j Graph

### Neo4j Browser Queries

Open http://localhost:7474 and run:

```cypher
// View all legislation
MATCH (l:Legislation)
RETURN l.title, l.jurisdiction, l.effective_date
LIMIT 10;

// Find sections of a specific act
MATCH (l:Legislation {title: "Employment Insurance Act"})-[:HAS_SECTION]->(s:Section)
RETURN s.section_number, s.title
ORDER BY s.section_number;

// Find cross-references
MATCH (s1:Section)-[r:REFERENCES]->(s2:Section)
RETURN s1.section_number, type(r), s2.section_number
LIMIT 20;

// Find programs related to legislation
MATCH (l:Legislation)-[:IMPLEMENTS]->(p:Program)
RETURN l.title, p.name;

// Complex query: Find all regulations implementing a specific act
MATCH (leg:Legislation {title: "Employment Insurance Act"})
      -[:IMPLEMENTS]->(reg:Regulation)
      -[:APPLIES_TO]->(sit:Situation)
RETURN leg.title, reg.regulation_number, sit.name;
```

### Visualize the Graph

```cypher
// Visualize Employment Insurance ecosystem
MATCH path = (l:Legislation {title: "Employment Insurance Act"})
             -[*1..2]-(n)
RETURN path
LIMIT 50;
```

## API Endpoints Overview

### Document Management

| Method | Endpoint            | Description                 |
| ------ | ------------------- | --------------------------- |
| POST   | `/documents/upload` | Upload and parse a document |
| GET    | `/documents/{id}`   | Get document details        |
| GET    | `/documents`        | List all documents          |
| DELETE | `/documents/{id}`   | Delete a document           |

### Document Structure

| Method | Endpoint                           | Description          |
| ------ | ---------------------------------- | -------------------- |
| GET    | `/documents/{id}/sections`         | Get all sections     |
| GET    | `/documents/{id}/cross-references` | Get cross-references |

### Search & Analytics

| Method | Endpoint                        | Description      |
| ------ | ------------------------------- | ---------------- |
| POST   | `/documents/search`             | Search documents |
| GET    | `/documents/statistics/summary` | Get statistics   |

### Compliance (Neo4j)

| Method | Endpoint            | Description            |
| ------ | ------------------- | ---------------------- |
| POST   | `/compliance/check` | Check compliance rules |
| GET    | `/compliance/rules` | List all rules         |

## Common Tasks

### Upload a PDF Document

```python
import requests

url = "http://localhost:8000/documents/upload"

with open("regulation.pdf", "rb") as f:
    files = {"file": f}
    data = {
        "document_type": "regulation",
        "jurisdiction": "federal",
        "authority": "Government of Canada"
    }
    response = requests.post(url, files=files, data=data)
    print(response.json())
```

### Query Neo4j from Python

```python
from backend.utils.neo4j_client import Neo4jClient

client = Neo4jClient()

# Find all legislation
result = client.run_query(
    "MATCH (l:Legislation) RETURN l.title AS title, l.jurisdiction AS jurisdiction"
)

for record in result:
    print(f"{record['title']} - {record['jurisdiction']}")

client.close()
```

### Search Documents

```python
import requests

response = requests.post(
    "http://localhost:8000/documents/search",
    json={
        "query": "employment insurance",
        "document_type": "legislation",
        "jurisdiction": "federal"
    }
)

documents = response.json()
for doc in documents:
    print(f"{doc['title']} ({doc['document_number']})")
```

## Troubleshooting

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# View logs
docker compose logs postgres

# Restart the service
docker compose restart postgres
```

### Neo4j Connection Errors

```bash
# Check if Neo4j is running
docker compose ps neo4j

# View logs
docker compose logs neo4j

# Restart Neo4j (safe - container handles restarts gracefully)
docker compose restart neo4j

# Rebuild Neo4j image (if Dockerfile changes)
docker compose build neo4j --no-cache
docker compose up -d neo4j

# Clear Neo4j data (WARNING: deletes all data)
docker compose down
docker volume rm regulatory-intelligence-assistant_neo4j_data
docker compose up -d
```

> **Note**: The Neo4j container uses a custom Docker image (`backend/neo4j/Dockerfile`) with pre-installed APOC and Graph Data Science plugins. The container is designed to handle restarts gracefully without losing data or requiring reconfiguration.

### Migration Errors

```bash
# Check migration status
alembic current

# Rollback last migration
alembic downgrade -1

# Reset database (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

### PDF Parsing Errors

```bash
# Ensure PDF dependencies are installed
pip install PyPDF2==3.0.1

# Try alternative PDF library
pip install pdfplumber
```

### Port Conflicts

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

## Running Tests

```bash
cd backend

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_compliance_checker.py -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Development Workflow

### Making Database Changes

1. Edit models in `backend/models/document_models.py`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Review migration in `backend/alembic/versions/`
4. Apply migration: `alembic upgrade head`

### Adding New API Endpoints

1. Create route in `backend/routes/`
2. Import in `backend/main.py`
3. Register router: `app.include_router(your_router)`
4. Test in browser at http://localhost:8000/docs

### Modifying Neo4j Schema

1. Edit `backend/scripts/init_graph.cypher`
2. Re-run: `python scripts/init_neo4j.py`
3. Update seed data: `python scripts/seed_graph_data.py`

## Next Steps

- 📖 Read the [Document Parser Documentation](./docs/dev/document-parser.md)
- 📖 Read the [Neo4j Implementation Guide](./docs/dev/neo4j-implementation-summary.md)
- 🔍 Explore the [Neo4j Schema](./docs/dev/neo4j-schema.md)
- 🧪 Run the test suite: `pytest`
- 🚀 Deploy to production

## Documentation

- [Product Requirements](./docs/prd.md)
- [System Design](./docs/design.md)
- [Development Plan](./docs/plan.md)
- [Neo4j Schema](./docs/dev/neo4j-schema.md)
- [Document Parser](./docs/dev/document-parser.md)
- [Compliance Engine](./docs/dev/compliance-engine.md)

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the documentation in `docs/dev/`
3. Check the test files for usage examples
4. Review the API documentation at http://localhost:8000/docs
