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
5. 🔎 **Elasticsearch**: Indexes full-text with SentenceTransformer embeddings for semantic search

**Note**: Embeddings are generated using SentenceTransformer during Elasticsearch indexing, NOT uploaded to Gemini. The LLM (Gemini/Ollama) is only used for final answer generation in the RAG Q&A feature.

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

## Understanding the RAG Q&A System

The **RAG Service** (`backend/services/rag_service.py`) powers the AI question-answering feature. Here's how it works:

### RAG Architecture

**Retrieval Phase** (Elasticsearch + SentenceTransformer):
1. 🔍 **Query Parsing**: Extracts intent, entities, and filters from user question
2. 🔎 **Multi-Tier Search**: Progressive 5-tier fallback system for document retrieval
3. 📊 **Semantic Search**: Uses SentenceTransformer embeddings indexed in Elasticsearch
4. 🔗 **Graph Enhancement**: (Optional) Adds related documents via Neo4j relationships

**Generation Phase** (LLM):
5. 🤖 **Answer Generation**: LLM (Gemini or Ollama) generates answer from retrieved context
6. 📝 **Citation Extraction**: Extracts legal citations from generated answer
7. 🎯 **Confidence Scoring**: Calculates confidence based on citations and context quality

### Multi-Tier Search Fallback System

The RAG service uses a **5-tier progressive fallback** to ensure high success rates (target: 85%+ on Tier 1):

| Tier | Method | When Used | Success Rate Target |
|------|--------|-----------|---------------------|
| **Tier 1** | Optimized Elasticsearch (hybrid keyword + semantic) | Default | 85%+ |
| **Tier 2** | Relaxed Elasticsearch (expanded synonyms, fewer filters) | Tier 1 insufficient | 10-12% |
| **Tier 3** | Neo4j Graph Traversal (relationship-based discovery) | Tiers 1-2 fail | 2-3% |
| **Tier 4** | PostgreSQL Full-Text Search (comprehensive text matching) | Tiers 1-3 fail | 1-2% |
| **Tier 5** | Metadata-Only Search (last resort, low confidence) | All others fail | <1% |

**Quality Checks**: Each tier's results are assessed for minimum score, average score, and keyword coverage before accepting.

### Query Routing

The RAG service intelligently routes different query types:

- **Regular Questions** → RAG pipeline (retrieval + LLM generation)
- **Graph Relationship Questions** → Neo4j direct queries (e.g., "What sections does X reference?")
- **Statistics Questions** → Database direct queries (e.g., "How many regulations exist?")

### Key Features

✅ **Language Detection**: Auto-detects English/French and filters results accordingly  
✅ **Citation Validation**: Extracts and validates legal citations from answers  
✅ **Confidence Scoring**: Provides transparency on answer reliability  
✅ **Caching**: In-memory caching for frequently asked questions  
✅ **Fallback Resilience**: 5-tier system ensures <1% zero-result rate  
✅ **Graph Enhancement**: Selectively adds related documents for section-specific queries  

### Testing the RAG Service

```bash
# Test basic Q&A
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is eligible for employment insurance?"}'

# Test with French query
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "Qui est admissible à l'\''assurance-emploi?"}'

# Test graph relationship query
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "What sections does the Employment Insurance Act reference?"}'
```

**Note**: The RAG service requires either a Gemini API key or Ollama to be running. Set `GEMINI_API_KEY` in `backend/.env` or configure Ollama in `docker-compose.yml`.

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

## Download Scripts for Real Canadian Data

If you want to work with real Canadian regulatory data instead of the sample data, three specialized download scripts are available:

### Option 1: Complete End-to-End Download & Ingestion

**`backend/scripts/download_and_ingest_real_data.sh`** - The most comprehensive option that automates the entire process:

```bash
# Run from project root
bash backend/scripts/download_and_ingest_real_data.sh
```

**What it does:**
1. ✅ **Downloads** - Clones official Justice Canada GitHub repo (laws-lois-xml)
2. ✅ **Backs up** - Creates backup of existing sample data
3. ✅ **Validates** - Checks for required dependencies (git, docker, curl)
4. ✅ **Clears** - Drops all existing data from PostgreSQL, Neo4j, and Elasticsearch
5. ✅ **Copies** - Extracts XML files from repo (English + French)
6. ✅ **Ingests** - Runs full data pipeline to load all databases
7. ✅ **Verifies** - Tests search, API health, and graph integrity

**Source**: Official Government of Canada open data repository  
**License**: Open Government License - Canada  
**URL**: https://github.com/justicecanada/laws-lois-xml

**Expected Results:**
- ~800 Canadian federal acts (English + French)
- ~1-2 hour processing time for full dataset
- Complete database population across all systems

**Use when:**
- 🎯 Setting up production environment
- 🎯 You want the most comprehensive, official dataset
- 🎯 You need a fully automated workflow
- ⚠️ **Warning**: This script is **DESTRUCTIVE** - it clears all existing data!

### Option 2: Bulk Regulation Download

**`backend/scripts/download_bulk_regulations.sh`** - Downloads thousands of SOR/DORS regulations incrementally:

```bash
# Run from project root
bash backend/scripts/download_bulk_regulations.sh
```

**What it does:**
1. ✅ Downloads regulations from Justice Canada website (laws-lois.justice.gc.ca)
2. ✅ Works backwards from recent years (2025 → 2000)
3. ✅ Downloads both English (SOR) and French (DORS) versions
4. ✅ Auto-ingests in chunks of 100 regulations (background processing)
5. ✅ Targets 5,000 most recent regulations
6. ✅ Skips existing files (resumable downloads)
7. ✅ Handles 404 errors gracefully (not all SOR numbers exist)

**Expected Results:**
- Up to 5,000 regulations (English + French)
- ~2-3 hours for full download + ingestion
- Incremental chunk ingestion (no waiting until end)

**Directory Structure:**
```
backend/data/regulations/canadian_laws/
  ├── en-regs/     # English regulations (SOR-YYYY-NNN.xml)
  └── fr-regs/     # French regulations (DORS-YYYY-NNN.xml)
```

**Use when:**
- 🎯 You need a large volume of regulations (not just acts)
- 🎯 You want incremental downloading with auto-ingestion
- 🎯 You're building a production regulatory database
- 🎯 You want to resume interrupted downloads

### Option 3: Priority Acts (Sample Generator)

**`backend/ingestion/download_canadian_laws.py`** - Creates sample XML files for 100 priority Canadian acts:

```bash
# Generate sample files for testing
docker compose exec backend python -m ingestion.download_canadian_laws

# Limit to 10 acts for quick testing
docker compose exec backend python -m ingestion.download_canadian_laws --limit 10

# Show instructions for getting real data
docker compose exec backend python -m ingestion.download_canadian_laws --show-instructions
```

**What it does:**
1. ✅ Creates **sample XML files** for 100 priority acts (10 categories)
2. ✅ Provides instructions for downloading real XML from Open Canada portal
3. ✅ Generates realistic test data with proper XML structure
4. ⚠️ **Important**: These are SAMPLE files, not real legal data!

**Priority Categories (100 total):**
- Social Services & Employment (10 acts)
- Immigration & Citizenship (10 acts)
- Tax & Finance (15 acts)
- Transparency & Privacy (10 acts)
- Justice & Rights (15 acts)
- Health & Safety (10 acts)
- Environment (10 acts)
- Business & Commerce (10 acts)
- Defense & Security (10 acts)
- Government Operations (10 acts)

**Use when:**
- 🎯 Testing the ingestion pipeline
- 🎯 Validating system architecture
- 🎯 Demo purposes
- 🎯 You need a specific subset of high-priority acts
- ⚠️ **Not for production** - use Option 1 or 2 for real data

### Comparison: Which Script to Use?

| Feature | End-to-End | Bulk Regulations | Priority Acts |
|---------|-----------|------------------|---------------|
| **Data Source** | GitHub repo | Justice Canada web | Sample generator |
| **Data Type** | Acts + Regulations | Regulations only | Acts only (samples) |
| **Volume** | ~800 acts | ~5,000 regulations | 100 sample acts |
| **Real Data?** | ✅ Yes | ✅ Yes | ❌ No (samples) |
| **Auto-Ingest?** | ✅ Yes | ✅ Yes (chunks) | ❌ No |
| **Destructive?** | ⚠️ Yes (clears all) | ❌ No | ❌ No |
| **Time Required** | 1-2 hours | 2-3 hours | <1 minute |
| **Best For** | Production setup | Large regulatory DB | Testing/demos |

**Recommendation:**
- 🎯 **First time users**: Use built-in `init_data.py` (loads sample data automatically)
- 🎯 **Production**: Use `download_and_ingest_real_data.sh` (complete official dataset)
- 🎯 **Regulations only**: Use `download_bulk_regulations.sh` (SOR/DORS regulations)
- 🎯 **Testing**: Use `download_canadian_laws.py` (quick sample generation)

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
