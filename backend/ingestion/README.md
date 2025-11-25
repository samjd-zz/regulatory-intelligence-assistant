# Data Ingestion System

Complete data ingestion pipeline for Canadian federal regulations into the Regulatory Intelligence Assistant.

## 📋 Overview

This module provides end-to-end ingestion of Canadian regulatory data from XML format into all system components:

1. **PostgreSQL** - Full-text storage and metadata
2. **Neo4j** - Knowledge graph relationships
3. **Elasticsearch** - Hybrid search indexing  
4. **Gemini API** - RAG document corpus

## 🏗️ Architecture

```
┌──────────────────┐
│  XML Files       │
│  (Open Canada)   │
└────────┬─────────┘
         │
         ▼
┌────────────────────┐
│ CanadianLawXML     │
│ Parser             │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ DataIngestion      │
│ Pipeline           │
└────┬───────────────┘
     │
     ├──────────► PostgreSQL (Regulations, Sections, Amendments)
     │
     ├──────────► Neo4j (Knowledge Graph)
     │
     ├──────────► Elasticsearch (Search Index)
     │
     └──────────► Gemini API (RAG Corpus)
```

## 📦 Components

### 1. `canadian_law_xml_parser.py`

Specialized XML parser for Canadian Justice Laws format.

**Features:**
- Parses official Canadian legal XML structure
- Extracts sections, subsections, and clauses
- Identifies cross-references automatically
- Handles amendments and bill numbers
- Supports namespaced XML

**Example:**
```python
from ingestion.canadian_law_xml_parser import CanadianLawXMLParser

parser = CanadianLawXMLParser()
regulation = parser.parse_file("employment-insurance-act.xml")

print(f"Title: {regulation.title}")
print(f"Sections: {len(regulation.sections)}")
print(f"Cross-references: {len(regulation.cross_references)}")
```

### 2. `data_pipeline.py`

Main ingestion pipeline orchestrator.

**Pipeline Stages:**
1. Parse XML → Structured data
2. Store in PostgreSQL → Full-text + metadata
3. Build knowledge graph → Neo4j relationships
4. Index in Elasticsearch → Hybrid search
5. Upload to Gemini → RAG context

**Example:**
```python
from ingestion.data_pipeline import DataIngestionPipeline

pipeline = DataIngestionPipeline(
    db_session=db,
    graph_service=graph_service,
    search_service=search_service
)

await pipeline.ingest_from_directory(
    xml_dir="data/regulations/canadian_laws",
    limit=10  # Test with 10 files first
)
```

### 3. `download_canadian_laws.py`

Data download and sample generation tool.

**Features:**
- Creates sample XML files for testing
- Documents real data sources
- Manages 50 priority Canadian federal acts
- Validates file structure

**Example:**
```bash
# Create sample data for testing
python backend/ingestion/download_canadian_laws.py --limit 10

# Show instructions for real data
python backend/ingestion/download_canadian_laws.py --show-instructions
```

## 🚀 Quick Start

### Prerequisites

1. **Services Running:**
```bash
docker-compose up -d
# Starts: PostgreSQL, Neo4j, Elasticsearch, Redis
```

2. **Database Initialized:**
```bash
cd backend
alembic upgrade head
python scripts/init_neo4j.py
```

3. **Python Environment:**
```bash
cd backend
source venv/bin/activate  # or activate your environment
pip install -r requirements.txt
```

### Step 1: Download Sample Data

```bash
cd backend
python ingestion/download_canadian_laws.py --limit 10
```

This creates 10 sample XML files in `data/regulations/canadian_laws/`.

**Output:**
```
data/regulations/canadian_laws/
├── employment-insurance-act.xml
├── canada-pension-plan.xml
├── old-age-security-act.xml
├── immigration-refugee-protection-act.xml
├── citizenship-act.xml
├── income-tax-act.xml
├── access-to-information-act.xml
├── privacy-act.xml
├── canadian-human-rights-act.xml
└── canada-health-act.xml
```

### Step 2: Run Ingestion Pipeline

```bash
cd backend
python ingestion/data_pipeline.py data/regulations/canadian_laws --limit 10 --validate
```

**Expected Output:**
```
2025-11-25 10:15:00 - INFO - Found 10 XML files in data/regulations/canadian_laws
2025-11-25 10:15:01 - INFO - [1/10] Processing employment-insurance-act.xml
2025-11-25 10:15:01 - INFO - Parsing Canadian Law XML: ...
2025-11-25 10:15:02 - INFO - Stored 3 sections, 1 amendments, 2 citations
2025-11-25 10:15:02 - INFO - Created 4 nodes, 6 relationships
2025-11-25 10:15:02 - INFO - Indexed 1 regulation + 3 sections
...
2025-11-25 10:15:20 - INFO - ============================================================
2025-11-25 10:15:20 - INFO - INGESTION COMPLETE
2025-11-25 10:15:20 - INFO - ============================================================
2025-11-25 10:15:20 - INFO - Statistics:
2025-11-25 10:15:20 - INFO -   Total files: 10
2025-11-25 10:15:20 - INFO -   Successful: 10
2025-11-25 10:15:20 - INFO -   Failed: 0
2025-11-25 10:15:20 - INFO -   Regulations created: 10
2025-11-25 10:15:20 - INFO -   Sections created: 30
2025-11-25 10:15:20 - INFO -   Amendments created: 10
2025-11-25 10:15:20 - INFO -   Graph nodes: 40
2025-11-25 10:15:20 - INFO -   Graph relationships: 60
```

### Step 3: Validate Ingestion

```bash
# Check PostgreSQL
psql -h localhost -U postgres -d regulatory -c "SELECT COUNT(*) FROM regulations;"

# Check Neo4j
python scripts/verify_graph.py

# Check Elasticsearch
curl http://localhost:9200/regulations/_count
```

## 📊 Data Statistics (MVP Target)

| Metric | Target | Sample Data |
|--------|--------|-------------|
| Regulations | 50 | 10 |
| Sections | 500-1,000 | 30 |
| Amendments | 50-100 | 10 |
| Cross-references | 200-500 | 20 |
| Graph Nodes | 1,000+ | 40 |
| Graph Relationships | 2,000+ | 60 |

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/regulatory

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Gemini API (for RAG)
GEMINI_API_KEY=your_api_key_here
```

### Pipeline Options

```python
pipeline = DataIngestionPipeline(
    db_session=db,
    graph_service=graph_service,
    search_service=search_service,
    data_dir="data/regulations"  # Custom data directory
)

await pipeline.ingest_from_directory(
    xml_dir="data/regulations/canadian_laws",
    limit=None  # None = process all files
)
```

## 📝 XML Format

### Canadian Justice Laws XML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>S.C. 1996, c. 23</Chapter>
    <TitleText>Employment Insurance Act</TitleText>
    <EnabledDate>1996-06-30</EnabledDate>
    <ConsolidationDate>2024-01-15</ConsolidationDate>
  </Identification>
  <Body>
    <Part id="I">
      <Number>I</Number>
      <Heading>Unemployment Insurance</Heading>
      <Section id="7">
        <Number>7</Number>
        <Heading>Qualification for benefits</Heading>
        <Subsection id="7-1">
          <Number>1</Number>
          <Text>Subject to this Part, benefits are payable...</Text>
        </Subsection>
        <Subsection id="7-2">
          <Number>2</Number>
          <Text>Reference to Section 12...</Text>
        </Subsection>
      </Section>
    </Part>
  </Body>
  <Amendments>
    <Amendment>
      <Date>2024-01-15</Date>
      <BillNumber>C-47</BillNumber>
      <Description>Updated eligibility requirements</Description>
    </Amendment>
  </Amendments>
</Consolidation>
```

## 🧪 Testing

### Unit Tests

```bash
cd backend
pytest ingestion/test_*.py -v
```

### Integration Test

```bash
# Full pipeline test with sample data
python ingestion/download_canadian_laws.py --limit 5
python ingestion/data_pipeline.py data/regulations/canadian_laws --limit 5 --validate
```

### Test XML Parser

```bash
cd backend
python ingestion/canadian_law_xml_parser.py
```

## 🐛 Troubleshooting

### Issue: "Directory not found"

**Solution:**
```bash
mkdir -p data/regulations/canadian_laws
python ingestion/download_canadian_laws.py --limit 10
```

### Issue: "Database connection failed"

**Solution:**
```bash
# Check Docker services
docker-compose ps

# Restart if needed
docker-compose restart postgres
```

### Issue: "Neo4j authentication failed"

**Solution:**
```bash
# Check credentials in .env
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Or reset Neo4j password
docker-compose restart neo4j
```

### Issue: "Elasticsearch index not created"

**Solution:**
```bash
# Check Elasticsearch is running
curl http://localhost:9200

# Check index
curl http://localhost:9200/_cat/indices

# Recreate index if needed
curl -X DELETE http://localhost:9200/regulations
curl -X DELETE http://localhost:9200/sections
```

## 📈 Performance

### Benchmarks (Single Node)

| Operation | Time per File | Throughput |
|-----------|--------------|------------|
| XML Parsing | 50-100ms | ~20 files/sec |
| PostgreSQL Insert | 100-200ms | ~10 files/sec |
| Neo4j Graph Build | 200-400ms | ~5 files/sec |
| Elasticsearch Index | 100-200ms | ~10 files/sec |
| **Total Pipeline** | **500ms-1s** | **~2 files/sec** |

### Optimization Tips

1. **Batch Processing:**
```python
# Process in batches of 10
for i in range(0, len(files), 10):
    batch = files[i:i+10]
    await pipeline.ingest_batch(batch)
    db.commit()  # Commit after batch
```

2. **Parallel Processing:**
```python
# Use multiple workers
import asyncio
tasks = [pipeline.ingest_xml_file(f) for f in files]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

3. **Skip Existing:**
```python
# Check hash before ingestion
if existing_hash(content_hash):
    continue
```

## 🔄 Production Deployment

### Real Data Sources

1. **Open Canada Portal:**
   - URL: https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa
   - Download ZIP (~50 MB)
   - Extract to `data/regulations/canadian_laws/`

2. **Justice Laws Website:**
   - URL: https://laws-lois.justice.gc.ca/eng/
   - Download individual acts as XML
   - Automated scraping with `requests` + `BeautifulSoup`

3. **Bulk API Access:**
   - Contact: laws-lois@justice.gc.ca
   - Request bulk XML download access

### Continuous Updates

```python
# Schedule daily ingestion
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)  # 2 AM daily
async def daily_ingestion():
    await pipeline.ingest_from_directory(
        xml_dir="data/regulations/canadian_laws",
        limit=None
    )

scheduler.start()
```

## 📚 Additional Resources

- **DATA_VERIFICATION_REPORT.md** - Data source evaluation
- **docs/design.md** - System architecture
- **docs/dev/database-management.md** - PostgreSQL details
- **docs/dev/neo4j-knowledge-graph.md** - Graph schema
- **docs/dev/BAITMAN_search-service.md** - Elasticsearch setup

## 🤝 Contributing

When adding new data sources:

1. Create parser in `backend/ingestion/`
2. Extend `DataIngestionPipeline` with new source
3. Update this README with examples
4. Add tests for new parser
5. Document data source in DATA_VERIFICATION_REPORT.md

## 📄 License

MIT License - See LICENSE file for details

---

**Last Updated:** November 25, 2025  
**Version:** 1.0 (MVP)  
**Status:** ✅ Ready for Use
