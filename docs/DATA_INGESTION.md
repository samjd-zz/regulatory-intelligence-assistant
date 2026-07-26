# Data Ingestion Guide

Complete guide to loading regulatory data into the system.

## Quick Load Sample Data

```bash
# Interactive wizard (recommended for first-time users)
docker compose exec backend python scripts/init_data.py

# Or load 10 laws for quick testing (2-5 minutes)
docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive
```

The init_data.py script offers:
- **Interactive Mode**: Guides you through choosing data type and limits
- **Canadian Laws**: ~800 Acts (Employment Insurance, Canada Pension Plan, etc.)
- **Regulations**: ~4,240 regulations (SOR/DORS documents)
- **Both**: Full dataset (~5,040 documents)
- **Flexible Limits**: Test with 10, 50, 100, or load everything

## Full Data Ingestion

For production use with complete regulatory datasets.

### Prerequisites

- Running Docker containers
- 20GB disk space minimum
- 4GB RAM available
- Stable internet connection

### Automated Ingestion (Recommended)

```bash
# Interactive wizard handles download + ingestion
docker compose exec backend python scripts/init_data.py

# Non-interactive for automation
docker compose exec backend python scripts/init_data.py --type both --non-interactive
```

The init_data.py script automatically:
1. ✅ Checks for existing data
2. ✅ Downloads from Justice Canada if missing
3. ✅ Filters by type (laws/regulations)
4. ✅ Applies user-specified limits
5. ✅ Ingests into PostgreSQL, Neo4j, and Elasticsearch
6. ✅ Shows progress and statistics

### Manual Step-by-Step (Advanced)

If you need manual control:

```bash
# Step 1: Download XML files from Justice Canada
docker compose exec backend python ingestion/download_canadian_laws.py

# Step 2: Run the complete ingestion pipeline
docker compose exec backend python ingestion/data_pipeline.py \
  --source data/regulations/canadian_laws/ \
  --jurisdiction CA \
  --batch-size 100
```

**Options:**

- `--source` - Source directory with XML files
- `--jurisdiction` - Jurisdiction code (CA, US, UK, etc.)
- `--batch-size` - Documents per batch (default: 100)
- `--force` - Force re-ingestion (skip duplicate check)
- `--skip-graph` - Skip Neo4j graph construction
- `--skip-elasticsearch` - Skip ES indexing

### Step 3: Verify Ingestion

```bash
# Check database counts
docker compose exec backend python -c "
from database import get_db
from models.models import Regulation, Section

with next(get_db()) as db:
    print(f'Regulations: {db.query(Regulation).count()}')
    print(f'Sections: {db.query(Section).count()}')
"

# Check Elasticsearch
curl http://localhost:9200/regulations/_count

# Check Neo4j
docker compose exec backend python -c "
from services.graph_service import get_graph_service
stats = get_graph_service().get_graph_overview()
print(f'Neo4j nodes: {sum(stats[\"nodes\"].values())}')
"
```

## Supported Data Sources

### Canada 🇨🇦

**Source**: Justice Laws Website  
**Format**: XML (CanLII schema)  
**Coverage**: 1,800+ federal acts  
**Update Frequency**: Daily  

```bash
python ingestion/download_canadian_laws.py --jurisdiction federal
```

### United States 🇺🇸

**Source**: GPO FDSys  
**Format**: XML (USLM 2.0)  
**Coverage**: US Code, CFR  
**Update Frequency**: Weekly

```bash
python ingestion/download_us_laws.py --source uscode
```

### United Kingdom 🇬🇧

**Source**: legislation.gov.uk  
**Format**: XML + HTML  
**Coverage**: 50+ years of legislation  
**Update Frequency**: Daily

```bash
python ingestion/download_uk_laws.py
```

### European Union 🇪🇺

**Source**: EUR-Lex  
**Format**: XML (Formex)  
**Coverage**: EU regulations, directives  
**Update Frequency**: Daily

```bash
python ingestion/download_eu_laws.py
```

## XML Schemas

### Canadian Law XML (CanLII)

```xml
<Legislation>
  <Identification>
    <LongTitle>Employment Insurance Act</LongTitle>
    <ActNumber>S.C. 1996, c. 23</ActNumber>
    <Jurisdiction>CA</Jurisdiction>
  </Identification>
  <Body>
    <Section id="s1">
      <SectionNumber>1</SectionNumber>
      <Title>Short title</Title>
      <Content>
        <Paragraph>This Act may be cited as...</Paragraph>
      </Content>
    </Section>
  </Body>
</Legislation>
```

### US Law XML (USLM 2.0)

```xml
<uslm:statute>
  <uslm:meta>
    <uslm:title>42</uslm:title>
    <uslm:section>1395</uslm:section>
  </uslm:meta>
  <uslm:content>
    <uslm:section>
      <uslm:num>1395</uslm:num>
      <uslm:heading>Definitions</uslm:heading>
      <uslm:text>...</uslm:text>
    </uslm:section>
  </uslm:content>
</uslm:statute>
```

## Data Pipeline Architecture

```
Download → Parse XML → Extract Entities → Store DB
                                           ↓
                              Build Graph (Neo4j)
                                           ↓
                              Index Search (Elasticsearch)
```

### Pipeline Stages

1. **Download**: Fetch XML files from source
2. **Validation**: Check XML schema compliance
3. **Parsing**: Extract structure and content
4. **Entity Extraction**: Identify legal entities
5. **Database Storage**: Save to PostgreSQL
6. **Graph Construction**: Build Neo4j relationships
7. **Search Indexing**: Index in Elasticsearch
8. **Verification**: Validate ingestion success

## Incremental Updates

### Daily Updates

```bash
# Run daily to get new/updated regulations
docker compose exec backend python ingestion/update_canadian_laws.py \
  --since yesterday

# This will:
# 1. Check for new/modified acts
# 2. Download only changed files
# 3. Update existing records
# 4. Re-index in search engines
```

### Differential Sync

```bash
# Sync only changes since last run
python ingestion/data_pipeline.py \
  --source regulations/ \
  --incremental \
  --since "2025-01-01"
```

## Batch Processing

For large datasets, use batch processing:

```bash
# Process in batches of 50
python ingestion/data_pipeline.py \
  --source regulations/ \
  --batch-size 50 \
  --parallel 4
```

**Performance:**
- Single-threaded: ~100 documents/minute
- 4 parallel workers: ~350 documents/minute
- Memory usage: ~2GB per worker

## Error Handling

The pipeline includes robust error handling:

- **Retry Logic**: 3 retries with exponential backoff
- **Partial Failures**: Continue processing on individual errors
- **Error Logging**: Detailed logs in `logs/ingestion.log`
- **Recovery**: Resume from last successful batch

### View Errors

```bash
# Check ingestion log
docker compose exec backend tail -f logs/ingestion.log

# Filter for errors only
docker compose exec backend grep ERROR logs/ingestion.log
```

## Data Quality Checks

### Post-Ingestion Validation

```bash
# Run validation suite
docker compose exec backend python scripts/validate_ingestion.py

# Checks:
# ✓ Database record counts
# ✓ Required fields populated
# ✓ Cross-reference integrity
# ✓ Search index completeness
# ✓ Graph relationship consistency
```

### Duplicate Detection

The system automatically detects duplicates using:

- **Document ID**: Unique identifier per act
- **Act Number**: Official citation number
- **Title + Jurisdiction**: Composite key
- **Content Hash**: SHA-256 of full text

## Performance Optimization

### Database Indexes

```sql
-- Key indexes for fast ingestion
CREATE INDEX idx_regulations_act_number ON regulations(act_number);
CREATE INDEX idx_sections_regulation_id ON sections(regulation_id);
CREATE INDEX idx_sections_section_number ON sections(section_number);
```

### Bulk Operations

Use bulk operations for better performance:

```python
# Batch insert sections (100x faster)
db.bulk_insert_mappings(Section, section_dicts)
db.commit()
```

### Parallel Processing

```bash
# Use 4 parallel workers
python ingestion/data_pipeline.py \
  --parallel 4 \
  --batch-size 50
```

## Storage Requirements

### Per 1,000 Regulations

- **PostgreSQL**: ~500MB
- **Elasticsearch**: ~800MB
- **Neo4j**: ~300MB
- **Total**: ~1.6GB

### Current Data (1,827 regulations)

- **PostgreSQL**: 1.2GB (1,817 regulations + 275,995 sections)
- **Elasticsearch**: 1.8GB (277,812 documents)
- **Neo4j**: 600MB (278,858 nodes + 470,353 relationships)
- **Total**: 3.6GB

## Backup & Restore

### Backup

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U postgres regulatory_db > backup.sql

# Backup Neo4j
docker compose exec neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j.dump

# Backup Elasticsearch
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_1?wait_for_completion=true"
```

### Restore

```bash
# Restore PostgreSQL
docker compose exec -T postgres psql -U postgres regulatory_db < backup.sql

# Restore Neo4j
docker compose exec neo4j neo4j-admin load --from=/backups/neo4j.dump --database=neo4j --force

# Restore Elasticsearch
curl -X POST "localhost:9200/_snapshot/backup/snapshot_1/_restore"
```

## Troubleshooting

### Common Issues

**Issue**: Out of memory during ingestion  
**Solution**: Reduce batch size: `--batch-size 25`

**Issue**: XML parsing errors  
**Solution**: Validate XML schema with `--validate-only` flag

**Issue**: Slow Elasticsearch indexing  
**Solution**: Increase refresh interval temporarily

**Issue**: Graph relationships missing  
**Solution**: Run graph builder separately: `python scripts/rebuild_graph.py`

### Re-ingestion

To completely re-ingest data:

```bash
# Clear all data
docker compose exec backend python scripts/clear_all_data.py

# Re-run ingestion
docker compose exec backend python seed_data.py
```

## See Also

- [Architecture](./ARCHITECTURE.md) - System design
- [API Reference](./API_REFERENCE.md) - Ingestion endpoints
- [Development](./DEVELOPMENT.md) - Developer setup
