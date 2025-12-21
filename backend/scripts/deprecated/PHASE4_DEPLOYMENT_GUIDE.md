# Phase 4 Database Optimizations - Deployment Guide

**Feature**: Multi-Tier RAG Search Enhancement  
**Phase**: 4 - Database Optimizations  
**Date**: 2025-12-12  
**Status**: Ready for Deployment

---

## 📋 Overview

Phase 4 adds critical database optimizations to support Tier 3 (Neo4j) and Tier 4 (PostgreSQL) fallback searches in the multi-tier RAG system. These optimizations enable fast full-text search across all 270k+ documents when Elasticsearch returns insufficient results.

### What's Included

1. **PostgreSQL Full-Text Search Indexes** (Phase 4.1)
   - Generated `tsvector` columns for regulations and sections
   - GIN indexes for sub-second full-text search
   - Bilingual support (English and French)

2. **Neo4j Index Optimizations** (Phase 4.2)
   - Full-text search indexes for semantic search
   - Property indexes for fast filtering
   - Relationship indexes for graph traversal

---

## 🎯 Prerequisites

### System Requirements
- Docker and Docker Compose running
- PostgreSQL 16+ (current: 16-alpine)
- Neo4j 5.15+ (current: 5.15-community)
- At least 4GB available RAM

### Data Requirements
- Existing regulations and sections data in PostgreSQL
- Existing knowledge graph data in Neo4j
- Backup of both databases (recommended)

### Access Requirements
- Database admin credentials
- SSH/terminal access to deployment environment
- Permission to run migrations

---

## 🚀 Deployment Steps

### Step 1: Pre-Deployment Checks

```bash
# Verify all services are running
docker ps | grep -E "regulatory-(postgres|neo4j|backend)"

# Check PostgreSQL connectivity
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db -c "SELECT COUNT(*) FROM regulations;"

# Check Neo4j connectivity
docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN count(n) LIMIT 1;"

# Verify Alembic is up to date (run inside Docker container)
docker exec -it regulatory-backend python -m alembic current
```

Expected output:
- All 3 services running
- PostgreSQL returns row count (e.g., `270000+`)
- Neo4j returns count
- Alembic shows current head revision

### Step 2: Backup Databases (IMPORTANT!)

```bash
# Backup PostgreSQL
docker exec regulatory-postgres pg_dump -U postgres regulatory_db > backup_postgres_$(date +%Y%m%d_%H%M%S).sql

# Backup Neo4j (stops container briefly)
docker exec regulatory-neo4j neo4j-admin database dump neo4j --to-path=/var/lib/neo4j/backups/
docker cp regulatory-neo4j:/var/lib/neo4j/backups/ ./neo4j_backup_$(date +%Y%m%d_%H%M%S)/
```

### Step 3: Apply PostgreSQL Migration (Phase 4.1)

```bash
# Run the migration inside the Docker container
docker exec -it regulatory-backend python -m alembic upgrade head

# Verify migration applied successfully
docker exec -it regulatory-backend python -m alembic current

# Check that new columns exist
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db -c "\d regulations"
```

Expected output:
```
Column            | Type      | Collation | Nullable | Default | Storage
------------------+-----------+-----------+----------+---------+---------
...
search_vector     | tsvector  |           |          |         | extended
search_vector_fr  | tsvector  |           |          |         | extended
```

**Estimated Time**: 2-5 minutes (depending on data size)

### Step 4: Verify PostgreSQL Indexes

```bash
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db << 'EOF'
-- Check indexes were created
SELECT indexname, tablename 
FROM pg_indexes 
WHERE indexname LIKE '%search_vector%';

-- Test full-text search performance
EXPLAIN ANALYZE
SELECT id, title 
FROM regulations 
WHERE search_vector @@ to_tsquery('english', 'employment & insurance')
LIMIT 10;
EOF
```

Expected output:
- 4 indexes: `ix_regulations_search_vector`, `ix_sections_search_vector`, and French versions
- Query plan should show "Bitmap Index Scan using ix_regulations_search_vector"
- Execution time: <50ms

### Step 5: Apply Neo4j Optimizations (Phase 4.2)

```bash
# Run the optimization script
cat backend/scripts/optimize_neo4j_indexes.cypher | \
  docker exec -i regulatory-neo4j cypher-shell -u neo4j -p password123

# Alternative: Run from file
docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 \
  < backend/scripts/optimize_neo4j_indexes.cypher
```

Expected output:
```
0 rows available after X ms, consumed after another Y ms
Added Z constraints
Added W indexes
```

**Estimated Time**: 1-5 minutes (depending on graph size)

### Step 6: Verify Neo4j Indexes

```bash
docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 << 'EOF'
// Verify indexes
CALL db.indexes()
YIELD name, type, state, populationPercent
WHERE name CONTAINS 'legislation' OR name CONTAINS 'section'
RETURN name, type, state, populationPercent
ORDER BY name;

// Verify constraints
CALL db.constraints()
YIELD name, type
RETURN name, type;
EOF
```

Expected output:
- All indexes in "ONLINE" state
- populationPercent should be 100.0
- Multiple constraints for legislation, section, regulation

### Step 7: Performance Testing

#### Test PostgreSQL Full-Text Search

```bash
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db << 'EOF'
-- Test English search
EXPLAIN ANALYZE
SELECT id, title, ts_rank(search_vector, query) AS rank
FROM regulations, to_tsquery('english', 'employment & insurance') query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 20;

-- Test French search
EXPLAIN ANALYZE
SELECT id, title, ts_rank(search_vector_fr, query) AS rank
FROM regulations, to_tsquery('french', 'assurance & emploi') query
WHERE search_vector_fr @@ query
ORDER BY rank DESC
LIMIT 20;
EOF
```

Expected: Query times <100ms

#### Test Neo4j Full-Text Search

```bash
docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 << 'EOF'
// Test full-text search
CALL db.index.fulltext.queryNodes('legislation_fulltext', 'employment insurance')
YIELD node, score
RETURN node.title, score
ORDER BY score DESC
LIMIT 10;

// Test graph traversal
MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
WHERE l.jurisdiction = 'federal'
RETURN l.title, count(s) as SectionCount
ORDER BY SectionCount DESC
LIMIT 10;
EOF
```

Expected: Query times <200ms

### Step 8: Integration Testing

```bash
# Test multi-tier RAG system
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can temporary residents apply for employment insurance?",
    "num_context_docs": 20
  }' | jq '.metadata.tier_used'

# Should return tier info (1, 2, 3, or 4)
```

### Step 9: Monitor Performance

```bash
# Check PostgreSQL query stats
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db << 'EOF'
SELECT schemaname, tablename, 
       idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexrelname LIKE '%search_vector%';
EOF

# Check Neo4j index usage
docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 << 'EOF'
CALL db.indexes()
YIELD name, type, labelsOrTypes, properties, state, populationPercent
WHERE name CONTAINS 'legislation' OR name CONTAINS 'section'
RETURN name, type, state, populationPercent;
EOF
```

---

## 🔄 Rollback Procedure

If issues occur, follow these steps:

### Rollback PostgreSQL Migration

```bash
# Check current revision (run inside Docker container)
docker exec -it regulatory-backend python -m alembic current

# Rollback one migration
docker exec -it regulatory-backend python -m alembic downgrade -1

# Verify rollback
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db -c "\d regulations"
```

The `search_vector` and `search_vector_fr` columns should be removed.

### Rollback Neo4j Indexes

```bash
docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 << 'EOF'
// Drop full-text indexes
DROP INDEX legislation_fulltext IF EXISTS;
DROP INDEX section_fulltext IF EXISTS;
DROP INDEX regulation_fulltext IF EXISTS;

// Drop property indexes
DROP INDEX section_number_idx IF EXISTS;
DROP INDEX legislation_jurisdiction_idx IF EXISTS;
DROP INDEX legislation_status_idx IF EXISTS;
DROP INDEX legislation_language_idx IF EXISTS;
DROP INDEX legislation_jurisdiction_status_idx IF EXISTS;

// Drop relationship indexes
DROP INDEX has_section_rel_idx IF EXISTS;
DROP INDEX references_rel_idx IF EXISTS;
DROP INDEX amended_by_rel_idx IF EXISTS;
EOF
```

### Restore from Backup (Last Resort)

```bash
# Restore PostgreSQL
docker exec -i regulatory-postgres psql -U postgres -d regulatory_db < backup_postgres_YYYYMMDD_HHMMSS.sql

# Restore Neo4j
docker stop regulatory-neo4j
docker cp neo4j_backup_YYYYMMDD_HHMMSS/ regulatory-neo4j:/var/lib/neo4j/backups/
docker exec regulatory-neo4j neo4j-admin database load neo4j --from-path=/var/lib/neo4j/backups/
docker start regulatory-neo4j
```

---

## 📊 Success Metrics

After deployment, monitor these metrics:

### PostgreSQL Performance
- Full-text search queries: <100ms (P95)
- Index hit rate: >90%
- Index size: ~10-20% of table size

### Neo4j Performance
- Full-text search queries: <100ms (P95)
- Graph traversal queries: <200ms (P95)
- Index population: 100%

### RAG System
- Tier 4 usage: <5% of queries (most should use Tier 1-2)
- Zero-result rate: <3% (down from 15-20%)
- Average response time: <4s for fallback tiers

---

## 🐛 Troubleshooting

### PostgreSQL Issues

**Problem**: Migration fails with "column already exists"
```bash
# Solution: Check if migration was partially applied
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db -c "\d regulations"
# If columns exist, mark migration as complete
docker exec -it regulatory-backend python -m alembic stamp head
```

**Problem**: Slow full-text queries
```bash
# Solution: Rebuild indexes
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db << 'EOF'
REINDEX INDEX CONCURRENTLY ix_regulations_search_vector;
REINDEX INDEX CONCURRENTLY ix_sections_search_vector;
EOF
```

**Problem**: Out of disk space
```bash
# Solution: Clean up old data or increase disk
docker exec -it regulatory-postgres psql -U postgres -d regulatory_db -c "VACUUM FULL;"
```

### Neo4j Issues

**Problem**: Index creation fails
```bash
# Solution: Check Neo4j logs
docker logs regulatory-neo4j --tail 100

# Check memory usage
docker exec regulatory-neo4j cypher-shell -u neo4j -p password123 "CALL dbms.listConfig() YIELD name, value WHERE name CONTAINS 'memory' RETURN name, value;"
```

**Problem**: Index in "POPULATING" state
```bash
# Solution: Wait for completion (can take 5-10 minutes for large graphs)
docker exec regulatory-neo4j cypher-shell -u neo4j -p password123 "CALL db.indexes() YIELD name, state, populationPercent RETURN name, state, populationPercent;"
```

**Problem**: Slow full-text queries
```bash
# Solution: Rebuild full-text index
docker exec regulatory-neo4j cypher-shell -u neo4j -p password123 << 'EOF'
DROP INDEX legislation_fulltext IF EXISTS;
CREATE FULLTEXT INDEX legislation_fulltext FOR (l:Legislation) ON EACH [l.title, l.full_text];
EOF
```

---

## 📝 Post-Deployment Checklist

- [ ] PostgreSQL migration applied successfully
- [ ] Neo4j indexes created successfully
- [ ] Performance tests passing
- [ ] Integration tests passing
- [ ] Monitoring dashboards updated
- [ ] Backups verified
- [ ] Documentation updated
- [ ] Team notified of changes
- [ ] Rollback procedure documented
- [ ] Production deployment scheduled

---

## 📞 Support

**Questions or Issues?**
- Check logs: `docker logs regulatory-postgres` or `docker logs regulatory-neo4j`
- Review this guide's troubleshooting section
- Contact: Development Team
- Escalate: Technical Lead

---

**Last Updated**: 2025-12-12  
**Version**: 1.0  
**Author**: Development Team
