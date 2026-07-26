# Real Canadian Public Data Ingestion Plan

**Date**: November 30, 2025  
**Feature Branch**: `feature/real-canadian-data-ingestion`  
**Status**: ✅ IN PROGRESS - Executing Option 1  
**Priority**: High - Production Data Required  
**Deployment**: Docker-based (backend runs in container)

---

## Executive Summary

This report outlines the plan to replace the current sample/test dataset with **real Canadian federal regulatory data** from official government sources. The current system contains 100 sample XML files used for testing. For production readiness, we need to ingest 500+ real Canadian federal acts and regulations.

**Key Objectives:**
1. Replace sample data with official Justice Laws Canada XML files
2. Increase dataset from 100 sample files to 500+ real regulations
3. Maintain data authenticity and legal accuracy
4. Ensure all three backend systems (PostgreSQL, Neo4j, Elasticsearch) are properly seeded
5. Validate data integrity after ingestion

---

## Current Data State

### What We Have (Sample Data)

**Location**: `backend/data/regulations/canadian_laws/`  
**Files**: 100 generated XML files  
**Type**: Sample/test data with basic structure  
**Purpose**: Pipeline testing, system validation, demos  
**Content**: NOT real legal content - placeholder text only

**Database State:**
- **PostgreSQL**: 103 regulations, 703 sections, 101 amendments
- **Neo4j**: 820 nodes, 1,114 relationships  
- **Elasticsearch**: 806 documents indexed

**Limitations:**
- ❌ Not legally authoritative
- ❌ Missing actual regulatory text
- ❌ Incomplete cross-references
- ❌ No real amendments or consolidation dates
- ❌ Unsuitable for production use

### What We Need (Real Data)

**Source**: Official Justice Laws Canada XML files  
**Coverage**: 500+ Canadian federal acts and regulations  
**Format**: Structured XML with complete legal content  
**Quality**: Legally authoritative, regularly updated by Justice Canada

**Features Required:**
- ✅ Complete regulatory text (sections, subsections, clauses)
- ✅ Amendment history with dates
- ✅ Cross-references between regulations
- ✅ Metadata (act numbers, effective dates, consolidation dates)
- ✅ Bilingual support (English and French)

---

## Data Source Analysis

### OPTION 1: Open Canada Portal ⭐ **RECOMMENDED**

**URL**: [Open Canada - Consolidated Federal Acts and Regulations (XML)](https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa)

**Alignment Score**: ⭐⭐⭐⭐⭐ (Excellent)

**Advantages:**
- ✅ Complete dataset of all Canadian federal acts and regulations
- ✅ Official government source (Justice Canada)
- ✅ Rich metadata with versioning and amendment tracking
- ✅ XML format matches our existing parser
- ✅ Open Government License - Canada (free to use)
- ✅ Regularly updated by Justice Canada
- ✅ ~50 MB compressed (manageable size)

**Details:**
- **File Name**: "Consolidated Federal Acts and Regulations (XML)"
- **Format**: ZIP archive containing XML files
- **Structure**: One XML file per act/regulation
- **XML Schema**: Justice Laws Canada format (already supported by our parser)
- **Coverage**: All federal legislation
- **Update Frequency**: Regular consolidations

**Download Process:**
1. Visit the Open Canada Portal dataset page
2. Click "Download" button for the XML dataset
3. Save ZIP file (~50 MB)
4. Extract to a staging directory
5. Copy XML files to `backend/data/regulations/canadian_laws/`

**Quality Assessment:**
- **Content Accuracy**: ⭐⭐⭐⭐⭐ (Official government source)
- **Metadata Richness**: ⭐⭐⭐⭐⭐ (Complete versioning, amendments)
- **Parser Compatibility**: ⭐⭐⭐⭐⭐ (Matches existing format)
- **Production Ready**: ✅ YES

---

### OPTION 2: Justice Laws Website (Individual Acts)

**URL**: [Justice Laws Website](https://laws-lois.justice.gc.ca/eng/)

**Alignment Score**: ⭐⭐⭐⭐ (Very Good)

**Advantages:**
- ✅ Individual act selection (for targeted updates)
- ✅ Same XML format as Open Canada Portal
- ✅ Official government source
- ✅ Most current versions available

**Disadvantages:**
- ❌ Manual download (one act at a time)
- ❌ Time-consuming for large datasets
- ❌ Requires individual navigation for each act

**When to Use:**
- Specific act updates after initial bulk load
- Testing with individual acts
- Verifying XML format for new legislation

**Download Process:**
1. Visit Justice Laws Website
2. Search for specific act (e.g., "Employment Insurance Act")
3. Click "XML" button on the act page
4. Save XML file to `backend/data/regulations/canadian_laws/`

---

### OPTION 3: Bulk Download from Justice Canada

**Contact**: laws-lois@justice.gc.ca

**Alignment Score**: ⭐⭐⭐⭐ (Very Good)

**Advantages:**
- ✅ Can request custom datasets
- ✅ Provincial/territorial regulations available
- ✅ Historical versions available
- ✅ Tailored to specific needs

**Disadvantages:**
- ❌ Requires formal request
- ❌ Response time unknown
- ❌ May require data use agreement

**When to Use:**
- Provincial/territorial regulations needed
- Historical version analysis required
- Custom dataset requirements
- Research projects

---

## Recommended Data Ingestion Strategy

### Phase 1: Initial Load (OPTION 1 - Open Canada Portal)

**Timeline**: 2-3 hours  
**Risk Level**: Low  
**Priority**: High

**Steps:**

1. **Download Dataset**
   ```bash
   # Create staging directory
   mkdir -p backend/data/staging/canadian_laws
   
   # Download from Open Canada Portal
   # Visit: https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa
   # Click "Download" button
   # Save to: backend/data/staging/canadian_laws.zip
   
   # Extract ZIP archive
   cd backend/data/staging
   unzip canadian_laws.zip -d canadian_laws/
   ```

2. **Backup Current Data**
   ```bash
   # Backup sample data (optional)
   cd backend/data/regulations
   mv canadian_laws canadian_laws.sample.backup
   mkdir -p canadian_laws
   ```

3. **Copy Real Data**
   ```bash
   # Copy extracted XML files
   cp backend/data/staging/canadian_laws/*.xml backend/data/regulations/canadian_laws/
   
   # Verify file count
   ls -l backend/data/regulations/canadian_laws/*.xml | wc -l
   # Expected: 500+ files
   ```

4. **Clear Existing Database Content** (Docker)
   ```bash
   # Option A: Clear PostgreSQL tables using Docker
   docker compose exec backend python -c "
   from database import SessionLocal
   from models.models import Regulation, Section, Amendment, Citation
   db = SessionLocal()
   db.query(Citation).delete()
   db.query(Amendment).delete()
   db.query(Section).delete()
   db.query(Regulation).delete()
   db.commit()
   print('✅ PostgreSQL cleared')
   "
   
   # Option B: Recreate database (more thorough) using Docker
   docker compose exec backend alembic downgrade base
   docker compose exec backend alembic upgrade head
   ```

5. **Clear Neo4j Graph** (Docker)
   ```bash
   # Option A: Using Neo4j Browser
   # Visit http://localhost:7474
   # Login: neo4j / password123
   # Run query: MATCH (n) DETACH DELETE n
   
   # Option B: Using Python script in Docker
   docker compose exec backend python -c "
   from utils.neo4j_client import Neo4jClient
   client = Neo4jClient()
   client.clear_graph()
   print('✅ Neo4j graph cleared')
   "
   ```

6. **Clear Elasticsearch Index**
   ```bash
   # Delete and recreate index
   curl -X DELETE "localhost:9200/regulatory_documents"
   curl -X PUT "localhost:9200/regulatory_documents" \
     -H 'Content-Type: application/json' \
     -d @backend/config/elasticsearch_mappings.json
   
   echo "✅ Elasticsearch index cleared"
   ```

7. **Run Data Ingestion Pipeline** (Docker)
   ```bash
   # Full ingestion with validation using Docker
   docker compose exec backend python -m ingestion.data_pipeline \
     data/regulations/canadian_laws \
     --limit 500 \
     --validate \
     --log-level INFO
   
   # Expected output:
   # - 500+ regulations processed
   # - ~3,500+ sections created
   # - ~1,000+ amendments tracked
   # - Neo4j: 5,000+ nodes, 8,000+ relationships
   # - Elasticsearch: 4,500+ documents indexed
   ```

8. **Verify Data Integrity** (Docker)
   ```bash
   # Run verification script using Docker
   docker compose exec backend python scripts/verify_graph.py
   
   # Check API health
   curl http://localhost:8000/health/all | jq
   
   # Test search functionality
   curl -X POST "http://localhost:8000/api/search/keyword" \
     -H "Content-Type: application/json" \
     -d '{"query": "employment insurance", "size": 5}' | jq
   ```

---

## Potential Code Changes Required

### 1. Parser Enhancements (If Needed)

**File**: `backend/ingestion/canadian_law_xml_parser.py`

**Potential Issues:**
- Real XML may have additional namespaces or schema versions
- Edge cases in act numbering (e.g., S.C. 1985, c. C-46)
- French language content handling
- Complex amendment structures

**Mitigation:**
- Test parser with sample real XML files first
- Add error handling for unexpected XML structures
- Log parsing warnings/errors for manual review
- Create parser regression tests with real data samples

**Code Changes (Example):**
```python
# Add support for additional XML namespaces
NAMESPACES = {
    'ns': 'http://www.justice.gc.ca/xml/schema/legislation',
    'ns2': 'http://www.justice.gc.ca/xml/schema/common',
    # Add new namespace if needed
    'ns3': 'http://www.justice.gc.ca/xml/schema/bilingual'
}

# Enhanced error handling
try:
    sections = root.findall('.//ns:Section', NAMESPACES)
except XMLSyntaxError as e:
    logger.error(f"XML parsing error in {filename}: {e}")
    # Continue to next file instead of failing
    return None
```

### 2. Database Schema Updates (If Needed)

**File**: `backend/models/models.py`

**Potential Issues:**
- Additional metadata fields in real data
- Longer text fields (content may exceed current limits)
- New citation formats

**Mitigation:**
- Review real data samples for field requirements
- Create database migration if schema changes needed
- Test with sample real data before full ingestion

**Code Changes (Example):**
```python
# If content fields need to be larger
class Section(Base):
    __tablename__ = "sections"
    
    # Already unlimited Text type
    content = Column(Text, nullable=False)
    
    # Add new metadata fields if needed
    consolidation_date = Column(Date, nullable=True)
    bilingual_note = Column(Text, nullable=True)
```

### 3. Ingestion Pipeline Updates (If Needed)

**File**: `backend/ingestion/data_pipeline.py`

**Potential Issues:**
- Duplicate detection with real data (different hashing)
- Memory usage with larger dataset
- Processing time optimization

**Mitigation:**
- Batch processing for large datasets
- Progress checkpointing (resume from failures)
- Parallel processing for faster ingestion

**Code Changes (Example):**
```python
# Add batch processing
BATCH_SIZE = 50  # Process 50 files at a time

for i in range(0, len(xml_files), BATCH_SIZE):
    batch = xml_files[i:i + BATCH_SIZE]
    for xml_file in batch:
        # Process file
        pass
    # Checkpoint progress
    save_checkpoint(i + BATCH_SIZE)
```

---

## Testing Strategy

### Pre-Ingestion Testing

1. **Sample Data Test** (5-10 real XML files)
   ```bash
   # Test with small sample first
   python -m ingestion.data_pipeline \
     data/regulations/sample_real \
     --limit 10 \
     --validate
   ```

2. **Parser Validation**
   ```bash
   # Run parser unit tests with real data
   pytest backend/tests/test_ingestion_xml_parser.py -v
   ```

3. **Schema Compatibility**
   ```bash
   # Verify database can handle real data
   python -c "
   from ingestion.canadian_law_xml_parser import CanadianLawXMLParser
   parser = CanadianLawXMLParser()
   result = parser.parse_file('sample_real_act.xml')
   print('Schema compatible:', result is not None)
   "
   ```

### Post-Ingestion Validation

1. **Data Integrity Check**
   ```bash
   # Verify all systems have data
   python scripts/verify_graph.py
   curl http://localhost:8000/health/all | jq
   ```

2. **Search Quality Test**
   ```bash
   # Test search for known acts
   curl -X POST "http://localhost:8000/api/search/keyword" \
     -H "Content-Type: application/json" \
     -d '{"query": "Income Tax Act", "size": 5}' | jq
   ```

3. **RAG System Test**
   ```bash
   # Test Q&A with real regulations
   curl -X POST "http://localhost:8000/api/rag/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the EI eligibility requirements?"}' | jq
   ```

4. **Frontend Smoke Test**
   ```bash
   # Start frontend and verify pages load
   cd frontend
   npm run dev
   # Visit http://localhost:5173
   # Test Search page, Chat page, Compliance page
   ```

---

## Rollback Plan

If ingestion fails or data quality issues are discovered:

### Quick Rollback (Restore Sample Data)

```bash
# Stop services
docker compose down

# Restore sample data
cd backend/data/regulations
rm -rf canadian_laws
mv canadian_laws.sample.backup canadian_laws

# Restore databases from backup (if created)
psql -h localhost -U postgres -d regulatory < backup.sql

# Restart services
docker compose up -d

# Re-run sample data ingestion
python -m ingestion.data_pipeline \
  data/regulations/canadian_laws \
  --limit 100 \
  --validate
```

### Create Backup Before Ingestion (Recommended)

```bash
# Backup PostgreSQL
pg_dump -h localhost -U postgres -d regulatory > backup_$(date +%Y%m%d).sql

# Backup Neo4j (export to Cypher)
# Visit http://localhost:7474
# Run: CALL apoc.export.cypher.all('backup.cypher', {})

# Backup Elasticsearch (snapshot)
curl -X PUT "localhost:9200/_snapshot/backup/snapshot_$(date +%Y%m%d)?wait_for_completion=true"
```

---

## Timeline & Resource Estimates

### Time Estimates

| Task | Duration | Dependencies |
|------|----------|--------------|
| Download real data | 15-30 min | Internet speed |
| Backup current data | 10 min | Database size |
| Clear databases | 5 min | - |
| Test parser with samples | 30 min | Sample real data |
| Full ingestion (500 files) | 1-2 hours | Server performance |
| Validation & testing | 30 min | - |
| **Total** | **3-4 hours** | - |

### Resource Requirements

- **Disk Space**: ~500 MB for XML files + ~200 MB database growth
- **Memory**: 4 GB RAM minimum during ingestion
- **CPU**: Multi-core recommended for faster processing
- **Network**: Stable connection for dataset download

---

## Success Criteria

### Must Have (Required)

- ✅ 500+ real Canadian federal acts loaded
- ✅ All three databases populated (PostgreSQL, Neo4j, Elasticsearch)
- ✅ Zero critical errors during ingestion
- ✅ Search functionality returns real regulatory content
- ✅ RAG system provides answers from real regulations
- ✅ All API health checks pass

### Should Have (Desirable)

- ✅ <5% warning rate during parsing
- ✅ Complete cross-reference extraction
- ✅ Bilingual content properly handled
- ✅ Amendment tracking for all acts

### Could Have (Nice to Have)

- ✅ Historical versions loaded
- ✅ Provincial/territorial regulations
- ✅ French language search working
- ✅ Performance optimization (sub-second search)

---

## Risk Assessment

### High Risk

**Risk**: Real XML structure incompatible with parser  
**Mitigation**: Test with sample files first  
**Contingency**: Update parser to handle new format

**Risk**: Database schema insufficient for real data  
**Mitigation**: Review sample data before full load  
**Contingency**: Create migration, reload data

### Medium Risk

**Risk**: Large dataset causes memory/performance issues  
**Mitigation**: Batch processing, monitoring  
**Contingency**: Incremental loading, server upgrade

**Risk**: Cross-references more complex than expected  
**Mitigation**: Enhanced regex patterns  
**Contingency**: Manual validation of critical references

### Low Risk

**Risk**: Duplicate detection fails  
**Mitigation**: SHA-256 hashing already implemented  
**Contingency**: Manual deduplication script

---

## Next Steps

### Immediate Actions (Next 24 Hours)

1. ✅ Create feature branch (DONE)
2. ✅ Create this planning document (DONE)
3. ✅ Update plan for Docker deployment (DONE)
4. ⏳ Download real data from Open Canada Portal
5. ⏳ Test parser with 5-10 sample real XML files
6. ⏳ Review and address any parser compatibility issues

### Short Term (Next 48 Hours)

6. ⏳ Create database backups
7. ⏳ Clear existing sample data
8. ⏳ Run full ingestion pipeline
9. ⏳ Validate data integrity
10. ⏳ Test all API endpoints with real data

### Medium Term (Next Week)

11. ⏳ Performance optimization if needed
12. ⏳ Create updated documentation
13. ⏳ Commit changes and create PR
14. ⏳ Deploy to staging environment
15. ⏳ User acceptance testing

---

## Conclusion

This plan provides a comprehensive approach to replacing sample data with real Canadian federal regulatory data. The Open Canada Portal (Option 1) is the recommended source due to its completeness, official status, and compatibility with our existing parser.

**Key Takeaways:**
- ✅ Existing parser should handle real data with minimal changes
- ✅ Clear step-by-step process reduces risk
- ✅ Testing strategy ensures data quality
- ✅ Rollback plan provides safety net
- ✅ Timeline is realistic (3-4 hours for full ingestion)

**Recommendation**: Proceed with Phase 1 (Initial Load) using the Open Canada Portal dataset. Begin with a small sample test (5-10 files) to validate compatibility, then proceed to full ingestion of 500+ acts.

---

**Document Status**: Draft v1.0  
**Next Review**: After sample data testing  
**Author**: AI Development Team  
**Approver**: Project Lead
