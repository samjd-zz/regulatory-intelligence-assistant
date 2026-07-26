# Backend Scripts

This directory contains scripts for initializing, managing, and maintaining the Regulatory Intelligence Assistant system.

## 🚀 Quick Start

### First-Time Setup

```bash
# 1. Start all Docker services
docker compose up -d

# 2. Initialize database with data (interactive wizard)
docker compose exec backend python scripts/init_data.py

# The wizard will guide you through:
# - Choosing data type (Laws, Regulations, or Both)
# - Setting limits for testing
# - Automatic download if needed
```

## 📁 Scripts Overview

### Data Initialization

#### `init_data.py` ⭐ **PRIMARY DATA LOADER**
Interactive wizard for initializing the system with Canadian regulatory data.

**Usage:**
```bash
# Interactive mode (recommended)
docker compose exec backend python scripts/init_data.py

# Non-interactive with options
docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive
docker compose exec backend python scripts/init_data.py --type regulations --non-interactive
docker compose exec backend python scripts/init_data.py --type both --non-interactive
```

**Features:**
- ✅ Checks existing data
- ✅ Downloads data if missing
- ✅ Loads into PostgreSQL, Neo4j, and Elasticsearch
- ✅ Shows progress and statistics
- ✅ Supports custom limits for testing

**Options:**
- `--type`: Choose 'laws', 'regulations', or 'both'
- `--limit`: Limit number of documents (e.g., 10, 50, 100)
- `--force`: Re-ingest even if data exists
- `--non-interactive`: Run without prompts

---

### Data Download

#### `download_and_ingest_real_data.sh`
Comprehensive script for downloading all Canadian laws from Justice Canada.

**Usage:**
```bash
bash backend/scripts/download_and_ingest_real_data.sh
```

**What it does:**
- Downloads XML files from laws-lois.justice.gc.ca
- Processes both English and French versions
- Ingests into all databases
- Provides progress tracking

#### `download_bulk_regulations.sh`
Downloads SOR/DORS regulations in bulk with chunked ingestion.

**Usage:**
```bash
bash backend/scripts/download_bulk_regulations.sh
```

**Features:**
- Downloads up to 5,000 regulations
- Processes in chunks of 100
- Auto-ingests as it downloads
- Skips existing files

#### `ingest_regulations.py`
Called by download scripts to process regulation XML files.

---

### Database & Neo4j Management

#### `init_neo4j.py`
Initializes Neo4j schema with indexes and constraints.

**Usage:**
```bash
docker compose exec backend python scripts/init_neo4j.py
```

**Called by:** `entrypoint_backend.sh` (automatic on startup)

**What it does:**
- Executes schema from `init_graph.cypher`
- Creates indexes and constraints
- Sets up full-text search indexes

#### `init_graph.cypher`
Cypher schema definition file.

**Contains:**
- Unique constraints on node IDs
- Performance indexes
- Full-text search indexes
- Node and relationship type definitions

#### `optimize_neo4j_indexes.cypher`
Additional optimization queries for Neo4j indexes.

---

### Maintenance & Operations

#### `reindex_elasticsearch.py`
Rebuilds Elasticsearch index from PostgreSQL data.

**Usage:**
```bash
docker compose exec backend python scripts/reindex_elasticsearch.py
```

**When to use:**
- After bulk data changes
- When search results seem stale
- After index configuration changes

#### `reindex_neo4j_overnight.py`
Batch reindexing for Neo4j graph with progress tracking.

**Usage:**
```bash
docker compose exec backend python scripts/reindex_neo4j_overnight.py --batch-size 50
```

**Features:**
- Batch processing to avoid memory issues
- Progress tracking
- Dry-run mode for testing

#### `rebuild_citation_relationships.py`
Rebuilds citation relationships in Neo4j graph.

**Usage:**
```bash
docker compose exec backend python scripts/rebuild_citation_relationships.py
```

#### `rebuild_section_hierarchy.py`
Rebuilds parent-child relationships between document sections.

**Usage:**
```bash
docker compose exec backend python scripts/rebuild_section_hierarchy.py
```

#### `migrate_neo4j_supersedes.py`
Migration script for adding "supersedes" relationships between regulations.

**Usage:**
```bash
docker compose exec backend python scripts/migrate_neo4j_supersedes.py
```

---

### Verification & Diagnostics

#### `verify_all_systems.py`
Comprehensive system health check across all services.

**Usage:**
```bash
docker compose exec backend python scripts/verify_all_systems.py
```

**Checks:**
- ✅ PostgreSQL connectivity and data
- ✅ Neo4j connectivity and graph
- ✅ Elasticsearch index status
- ✅ Redis connectivity
- ✅ API endpoint responses

#### `verify_graph.py`
Neo4j-specific verification and diagnostics.

**Usage:**
```bash
docker compose exec backend python scripts/verify_graph.py
```

**Shows:**
- Connection status
- Node/relationship counts
- Schema information
- Sample data
- Useful Cypher queries

#### `data_summary.sh`
Quick data statistics across all databases.

**Usage:**
```bash
bash backend/scripts/data_summary.sh
```

**Output:**
- PostgreSQL document counts
- Neo4j node/relationship counts
- Elasticsearch index size
- System health status

---

### Docker Entrypoints

#### `entrypoint_backend.sh`
Main Docker entrypoint for backend container.

**Automatically:**
- Waits for services (PostgreSQL, Neo4j, Elasticsearch)
- Initializes Neo4j schema
- Checks database status
- Offers to initialize data if empty
- Starts FastAPI server

#### `entrypoint_ollama.sh`
Docker entrypoint for Ollama LLM service.

---

## 📋 Typical Workflows

### First-Time Setup

```bash
# 1. Start all services
docker compose up -d

# 2. Initialize with data
docker compose exec backend python scripts/init_data.py

# 3. Verify everything works
docker compose exec backend python scripts/verify_all_systems.py
```

### Development Testing

```bash
# Load small dataset for testing
docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive

# Check what's loaded
bash backend/scripts/data_summary.sh
```

### Production Deployment

```bash
# Load full dataset
docker compose exec backend python scripts/init_data.py --type both --non-interactive

# Verify all systems
docker compose exec backend python scripts/verify_all_systems.py
```

### Maintenance Operations

```bash
# Rebuild search index
docker compose exec backend python scripts/reindex_elasticsearch.py

# Rebuild graph relationships
docker compose exec backend python scripts/rebuild_citation_relationships.py

# Check system health
docker compose exec backend python scripts/verify_all_systems.py
```

---

## 🗂️ Deprecated Scripts

Old scripts have been moved to `deprecated/` folder. See `deprecated/README.md` for details.

**Replaced scripts:**
- `seed_graph_data.py` → Use `init_data.py`
- `test_document_api.py` → Use `pytest backend/tests/`
- `test_graph_system.py` → Use `pytest backend/tests/`
- `download_regulations.sh` → Use `download_bulk_regulations.sh`
- `force_reload.sh` → Use `docker compose restart backend`

---

## 🔧 Troubleshooting

### Connection Issues

```bash
# Check if services are running
docker compose ps

# Check service logs
docker compose logs backend
docker compose logs neo4j
docker compose logs elasticsearch

# Restart services
docker compose restart backend
```

### Data Issues

```bash
# Check data status
bash backend/scripts/data_summary.sh

# Verify all systems
docker compose exec backend python scripts/verify_all_systems.py

# Re-initialize if needed
docker compose exec backend python scripts/init_data.py --force
```

### Performance Issues

```bash
# Rebuild indexes
docker compose exec backend python scripts/reindex_elasticsearch.py
docker compose exec backend python scripts/reindex_neo4j_overnight.py
```

---

## 📚 Related Documentation

- [Docker Deployment Guide](../../DOCKER_DEPLOYMENT.md)
- [Data Ingestion Guide](../../docs/DATA_INGESTION.md)
- [Architecture Overview](../../docs/ARCHITECTURE.md)
- [Development Guide](../../docs/DEVELOPMENT.md)
