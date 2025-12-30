# Quick Start Guide

Get the Regulatory Intelligence Assistant running in under 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Git
- 8GB RAM minimum
- Gemini API key (optional for RAG features)

## Installation

### 1. Clone & Setup

```bash
git clone <repository-url>
cd regulatory-intelligence-assistant
cp backend/.env.example backend/.env
```

### 2. Configure API Keys

Edit `backend/.env`:

```bash
# Required for RAG/Q&A features
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Use Ollama instead
# OLLAMA_HOST=http://ollama:11434
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Neo4j, Elasticsearch, Redis, Backend, Frontend)
docker compose up -d

# Wait for services to be ready (~30 seconds)
docker compose ps
```

**What happens automatically on startup:**
1. ✅ **Database migrations** - Alembic runs migrations to latest schema
2. ✅ **Neo4j setup** - Creates constraints, indexes, and fulltext search indexes  
3. ✅ **Health checks** - Waits for Neo4j and Elasticsearch to be ready
4. ✅ **Data check** - Detects if database is empty (<100 regulations)

**Optional: Automatic data loading**

To auto-load sample data on first start, set in `docker-compose.yml`:
```yaml
environment:
  - AUTO_INIT_DATA=true  # Loads 50 documents automatically
```

### 4. Initialize Database & Load Data (Manual)

The intelligent data loader makes it easy to get started:

```bash
# Interactive mode - recommended for first time
docker compose exec backend python scripts/init_data.py
```

The wizard will ask you to choose:
1. **Canadian Laws** (Acts/Lois) - ~800 documents
2. **Regulations** - ~4,240 documents  
3. **Both** (Full Dataset) - ~5,040 documents
4. **Custom limit** - Specify number for testing (e.g., 10, 50, 100)

**Quick Test (Non-Interactive):**
```bash
# Load 10 laws for quick testing
docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive

# Load 50 regulations
docker compose exec backend python scripts/init_data.py --type regulations --limit 50 --non-interactive

# Load all Canadian laws
docker compose exec backend python scripts/init_data.py --type laws --non-interactive

# Load everything (production)
docker compose exec backend python scripts/init_data.py --type both --non-interactive
```

**What it does:**
- ✅ Checks if data files exist (auto-downloads from Justice Canada if missing)
- ✅ Smart filtering by type (Acts/Lois vs Regulations based on filename)
- ✅ Applies your limit after filtering
- ✅ Loads into all three databases simultaneously (PostgreSQL → Neo4j → Elasticsearch)
- ✅ Shows real-time progress and final statistics
- ✅ Skips duplicates (use `--force` to re-ingest)

### 5. Access the Application

Once data is loaded, you can access:

- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:8000/docs (interactive Swagger UI)
- **Neo4j Browser**: http://localhost:7474 (username: neo4j, password: password123)
- **Health Check**: http://localhost:8000/api/health

**Tip**: The frontend will show "No results" until you load data in step 4.

## Understanding the Data Pipeline

Behind the scenes, `init_data.py` uses the **Data Ingestion Pipeline** (`backend/ingestion/data_pipeline.py`) which orchestrates a 6-stage process:

**Pipeline Stages:**
1. 📥 **Download**: Fetches XML files from Justice Canada's Open Data portal
2. 🔍 **Parse**: Extracts structured data using CanadianLawXMLParser
3. 💾 **PostgreSQL**: Stores regulations, sections, amendments, and citations
4. 🕸️ **Neo4j Graph**: Builds knowledge graph with relationships
5. 🔎 **Elasticsearch**: Indexes full-text for semantic search
6. 🤖 **Gemini RAG**: (Optional) Uploads to Gemini API for AI Q&A

**Advanced Usage:**
```bash
# Direct pipeline usage (for advanced scenarios)
docker compose exec backend python -m ingestion.data_pipeline data/regulations/canadian_laws --limit 100

# Clear PostgreSQL and rebuild from scratch
docker compose exec backend python -m ingestion.data_pipeline data/regulations/canadian_laws --clear-postgres

# Force re-ingestion (skip duplicate checking)
docker compose exec backend python -m ingestion.data_pipeline data/regulations/canadian_laws --force

# Ingest only to PostgreSQL (skip Neo4j and Elasticsearch)
docker compose exec backend python -m ingestion.data_pipeline data/regulations/canadian_laws --postgres-only
```

## Specialized Rebuild Tools

If you need to rebuild just **Neo4j** or **Elasticsearch** without re-ingesting from XML files, use these specialized scripts:

### Rebuild Neo4j Knowledge Graph

**`backend/tasks/populate_graph.py`** - Rebuilds Neo4j graph from PostgreSQL data:

```bash
# Rebuild entire graph from PostgreSQL
docker compose exec backend python tasks/populate_graph.py

# Clear existing graph and rebuild (DESTRUCTIVE)
docker compose exec backend python tasks/populate_graph.py --clear

# Limit to first 100 regulations for testing
docker compose exec backend python tasks/populate_graph.py --limit 100

# Setup indexes only (don't populate)
docker compose exec backend python tasks/populate_graph.py --setup-only

# Custom batch size for performance tuning
docker compose exec backend python tasks/populate_graph.py --batch-size 5000
```

**What it does:**
- **Pass 1**: Creates all nodes (Legislation, Regulation, Section)
- **Pass 2**: Creates all relationships (HAS_SECTION, REFERENCES, CITES, etc.)
- Uses batching for memory efficiency (default: 2,500 nodes/batch)
- Two-pass design prevents errors with cross-regulation references

### Rebuild Elasticsearch Index

**`backend/scripts/reindex_elasticsearch.py`** - Re-indexes documents from PostgreSQL to Elasticsearch:

```bash
# Incremental update (default) - updates existing docs, adds new ones
docker compose exec backend python scripts/reindex_elasticsearch.py

# Full recreation - deletes and rebuilds index (use when mappings change)
docker compose exec backend python scripts/reindex_elasticsearch.py --force-recreate

# Custom batch size for performance tuning
docker compose exec backend python scripts/reindex_elasticsearch.py --batch-size 5000
```

**What it does:**
- Indexes all regulations and sections from PostgreSQL
- Generates embeddings for semantic search
- Uses bulk indexing for efficiency (default: 2,500 docs/batch)
- Incremental mode: zero downtime, updates existing documents
- Force-recreate mode: complete rebuild (causes temporary search downtime)

**When to use:**
- ✅ After modifying Elasticsearch mappings (use `--force-recreate`)
- ✅ After manually adding data to PostgreSQL
- ✅ To fix inconsistencies between PostgreSQL and Elasticsearch
- ✅ After upgrading Elasticsearch version

## Check Data Statistics

Use the **Data Summary Script** to view comprehensive statistics across all databases:

```bash
# Run from project root
bash backend/scripts/data_summary.sh

# Or from within Docker
docker compose exec backend bash scripts/data_summary.sh
```

**Sample Output:**
```
╔═══════════════════════════════════════════════════════════════╗
║   REGULATORY INTELLIGENCE ASSISTANT - DATA SUMMARY REPORT    ║
╚═══════════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  POSTGRESQL DATABASE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Regulations:
    Total:           4,240
    English:         3,800
    French:          440
    Active:          4,240

  Sections:          395,465
  Citations:         12,384

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEO4J KNOWLEDGE GRAPH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Nodes by Type:
    Section:             278,858
    Legislation:         800
    Regulation:          3,440

  Total Nodes:         399,705

  Relationships by Type:
    HAS_SECTION:         395,465
    REFERENCES:          74,888

  Total Relationships: 470,353

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ELASTICSEARCH SEARCH INDEX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Index:             regulatory_documents
  Total Documents:   399,705
  Documents by Type:
    Regulations:     4,240
    Sections:        395,465

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  System Health:
    ✓ All systems operational
    ✓ Data present in all databases
    ✓ PostgreSQL and Elasticsearch are in sync
```

This script shows:
- **PostgreSQL**: Regulation counts, language breakdown, jurisdictions
- **Neo4j**: Node and relationship counts by type
- **Elasticsearch**: Index size and document counts
- **Health Checks**: Data consistency across all systems

## Verify Installation

### Test Search

```bash
curl "http://localhost:8000/api/search?q=employment+insurance&limit=5"
```

### Test RAG Q&A

```bash
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is eligible for employment insurance?"}'
```

### Test Compliance Check

```bash
curl -X POST http://localhost:8000/api/compliance/check \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "employment-insurance",
    "workflow_type": "ei_application",
    "form_data": {
      "sin": "123-456-789",
      "hours_worked": 700
    }
  }'
```

## Common Issues

### No Data Loaded

If you see empty search results:

```bash
# Check database status
bash backend/scripts/data_summary.sh

# Or re-run initialization
docker compose exec backend python scripts/init_data.py --force
```

### Services Not Starting

```bash
# Check logs
docker compose logs backend
docker compose logs postgres

# Restart services
docker compose restart
```

### Port Conflicts

Edit `docker-compose.yml` to change ports:
- Frontend: 5173 → 3000
- Backend: 8000 → 8080
- Neo4j: 7474 → 7475

### Low Memory

Reduce Elasticsearch memory in `docker-compose.yml`:
```yaml
environment:
  - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
```

## Next Steps

- **Load More Data**: See [Data Ingestion Guide](./DATA_INGESTION.md)
- **API Reference**: Browse http://localhost:8000/docs
- **Architecture**: Read [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Development**: See [DEVELOPMENT.md](./DEVELOPMENT.md)

## Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (delete all data)
docker compose down -v
```
