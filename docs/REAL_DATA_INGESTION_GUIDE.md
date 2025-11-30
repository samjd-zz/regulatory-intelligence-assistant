# Real Canadian Data Ingestion Guide

**Last Updated**: November 30, 2025  
**Status**: Ready for Execution

---

## Overview

This guide walks through the process of downloading and ingesting **real Canadian federal regulations** from Justice Canada's official GitHub repository into the Regulatory Intelligence Assistant.

**What This Does:**
- Downloads 500+ real Canadian federal acts from Justice Canada
- Replaces sample/test data with production-ready legal content
- Populates PostgreSQL, Neo4j, and Elasticsearch with real data
- Provides rollback capability if needed

**Timeline:** 1-2 hours total
- Download: 5-10 minutes
- Ingestion: 1-2 hours
- Verification: 5-10 minutes

---

## Prerequisites ✅

Before running the ingestion script, ensure:

- ✅ Docker services are running (`docker compose ps`)
- ✅ All services are healthy (postgres, neo4j, elasticsearch, redis, backend)
- ✅ At least 2GB free disk space
- ✅ Stable internet connection for GitHub download
- ✅ Backend API is accessible at `http://localhost:8000`

---

## Quick Start

### Option 1: Automated Script (Recommended)

The automated script handles everything:

```bash
# Navigate to project root
cd /home/shawn/projs/regulatory-intelligence-assistant

# Run the automated script
./backend/scripts/download_and_ingest_real_data.sh
```

**What it does:**
1. ✅ Downloads all Canadian federal acts from GitHub
2. ✅ Backs up current sample data
3. ✅ Clears all databases (with confirmation prompt)
4. ✅ Runs data ingestion pipeline
5. ✅ Verifies data integrity
6. ✅ Tests search functionality

**Interactive Prompts:**
- You'll be asked to confirm database clearing (type `yes`)
- If fewer than 100 XML files are found, you can choose to continue anyway

---

### Option 2: Manual Step-by-Step

If you prefer manual control:

#### Step 1: Download Data

```bash
# Create staging directory
mkdir -p backend/data/staging/canadian_laws

# Clone Justice Canada repository
git clone --depth 1 https://github.com/justicecanada/laws-lois-xml.git \
  backend/data/staging/canadian_laws

# Count files
find backend/data/staging/canadian_laws -name "*.xml" -type f | wc -l
# Expected: 500+ files
```

#### Step 2: Backup Current Data

```bash
# Backup sample data
mv backend/data/regulations/canadian_laws \
   backend/data/regulations/canadian_laws.sample.backup

# Create fresh directory
mkdir -p backend/data/regulations/canadian_laws

# Copy XML files
find backend/data/staging/canadian_laws -name "*.xml" -type f \
  ! -name "Legis.xml" ! -name "index.xml" \
  -exec cp {} backend/data/regulations/canadian_laws/ \;
```

#### Step 3: Clear Databases

```bash
# Clear PostgreSQL
docker compose exec backend python -c "
from database import SessionLocal
from models.models import Regulation, Section, Amendment, Citation
db = SessionLocal()
db.query(Citation).delete()
db.query(Amendment).delete()
db.query(Section).delete()
db.query(Regulation).delete()
db.commit()
print('PostgreSQL cleared')
"

# Clear Neo4j
docker compose exec backend python -c "
from utils.neo4j_client import Neo4jClient
client = Neo4jClient()
client.driver.execute_query('MATCH (n) DETACH DELETE n')
print('Neo4j cleared')
"

# Clear Elasticsearch
curl -X DELETE "localhost:9200/regulatory_documents"
curl -X PUT "localhost:9200/regulatory_documents" \
  -H 'Content-Type: application/json' \
  -d @backend/config/elasticsearch_mappings.json
```

#### Step 4: Run Ingestion

```bash
# Full ingestion (500 files)
docker compose exec backend python -m ingestion.data_pipeline \
  data/regulations/canadian_laws \
  --limit 500 \
  --validate \
  --log-level INFO
```

#### Step 5: Verify

```bash
# Check health
curl http://localhost:8000/health/all | jq

# Verify graph
docker compose exec backend python scripts/verify_graph.py

# Test search
curl -X POST "http://localhost:8000/api/search/keyword" \
  -H "Content-Type: application/json" \
  -d '{"query": "employment insurance", "size": 5}' | jq
```

---

## Expected Results

### Download Phase

```
[INFO] Downloading real Canadian regulatory data from Justice Canada...
[INFO] Cloning repository (this may take a few minutes)...
[SUCCESS] Downloaded 500+ XML files
```

### Ingestion Phase

```
[INFO] Starting data ingestion pipeline...
[INFO] This may take 1-2 hours for 500+ regulations...
[INFO] [1/500] Processing employment-insurance-act.xml
[INFO] [2/500] Processing canada-pension-plan.xml
...
[SUCCESS] Data ingestion completed
```

### Final Statistics

Expected after ingestion:

- **PostgreSQL**: 500+ regulations, 3,500+ sections, 1,000+ amendments
- **Neo4j**: 5,000+ nodes, 8,000+ relationships
- **Elasticsearch**: 4,500+ documents indexed
- **Total Size**: ~200-300 MB

---

## Troubleshooting

### Issue: Git clone fails

**Error**: `fatal: unable to access 'https://github.com/...'`

**Solution**:
```bash
# Check internet connection
ping github.com

# Try with SSH instead
git clone git@github.com:justicecanada/laws-lois-xml.git \
  backend/data/staging/canadian_laws
```

### Issue: Docker services not running

**Error**: `Cannot connect to Docker daemon`

**Solution**:
```bash
# Start Docker services
docker compose up -d

# Wait for services to be healthy
docker compose ps

# Check logs if needed
docker compose logs backend
```

### Issue: Ingestion fails partway through

**Error**: `XMLSyntaxError` or `Database error`

**Solution**:
```bash
# The ingestion pipeline is resumable
# Re-run the command - it will skip already-processed files
docker compose exec backend python -m ingestion.data_pipeline \
  data/regulations/canadian_laws \
  --limit 500 \
  --validate
```

### Issue: Out of disk space

**Error**: `No space left on device`

**Solution**:
```bash
# Check disk usage
df -h

# Clean Docker images/volumes
docker system prune -a --volumes

# Remove staging directory after ingestion
rm -rf backend/data/staging/canadian_laws
```

---

## Rollback Instructions

If you need to restore the sample data:

```bash
# Stop services
docker compose down

# Restore sample data
rm -rf backend/data/regulations/canadian_laws
mv backend/data/regulations/canadian_laws.sample.backup \
   backend/data/regulations/canadian_laws

# Restart services
docker compose up -d

# Re-ingest sample data
docker compose exec backend python -m ingestion.data_pipeline \
  data/regulations/canadian_laws \
  --limit 100 \
  --validate
```

---

## Verification Checklist

After ingestion completes, verify:

- [ ] API health check returns "healthy": `curl http://localhost:8000/health/all | jq`
- [ ] Search returns results: Test at `http://localhost:5173`
- [ ] Neo4j graph populated: Check at `http://localhost:7474`
- [ ] PostgreSQL has 500+ regulations: Check API docs
- [ ] RAG system works: Ask questions in Chat page
- [ ] Compliance checker works: Test on Compliance page

---

## Performance Tips

### Speed Up Ingestion

1. **Increase limit gradually**:
   ```bash
   # Start with 100 files to test
   --limit 100
   
   # Then increase to 250
   --limit 250
   
   # Finally do all
   --limit 500
   ```

2. **Monitor progress**:
   ```bash
   # Watch logs in real-time
   docker compose logs -f backend
   ```

3. **Check resource usage**:
   ```bash
   # Monitor Docker resources
   docker stats
   ```

### Optimize Database Performance

```bash
# After ingestion, vacuum PostgreSQL
docker compose exec postgres psql -U postgres -d regulatory -c "VACUUM ANALYZE;"

# Optimize Neo4j indexes
# Visit http://localhost:7474 and run:
# CALL db.indexes()
```

---

## Data Source Information

**Official Source**: Justice Canada GitHub Repository  
**URL**: https://github.com/justicecanada/laws-lois-xml  
**License**: Open Government License - Canada  
**Update Frequency**: Regular (maintained by Justice Canada)  
**Coverage**: All Canadian federal acts and regulations  
**Format**: XML (Justice Laws Canada schema)  
**Quality**: ⭐⭐⭐⭐⭐ (Legally authoritative)

### What's Included

- Complete regulatory text (all sections, subsections, clauses)
- Amendment history with dates
- Cross-references between regulations
- Metadata (act numbers, effective dates, consolidation dates)
- Bilingual content (English and French)

---

## Next Steps After Ingestion

1. **Test the system**:
   - Visit http://localhost:5173
   - Try searching for "employment insurance"
   - Ask questions in the Chat page
   - Test compliance checking

2. **Run tests**:
   ```bash
   docker compose exec backend pytest
   ```

3. **Update documentation**:
   - Note the number of regulations loaded
   - Document any parser issues encountered
   - Update README with new dataset information

4. **Create data report**:
   ```bash
   # Generate ingestion report
   docker compose exec backend python scripts/verify_graph.py > \
     docs/reports/REAL_DATA_INGESTION_REPORT.md
   ```

---

## Support

If you encounter issues:

1. Check the logs: `docker compose logs backend`
2. Verify services are healthy: `docker compose ps`
3. Review the REAL_CANADIAN_DATA_INGESTION_PLAN.md
4. Check existing issues in the GitHub repository

---

**Document Status**: Ready for Use  
**Last Tested**: November 30, 2025  
**Success Rate**: Expected 95%+ (based on parser compatibility)
