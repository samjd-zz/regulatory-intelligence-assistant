# Deployment Checklist - Regulatory Intelligence Assistant

## ✅ Completed

### Backend Implementation
- [x] Document models for PostgreSQL (6 tables)
- [x] Legal text parser with section extraction
- [x] Document parser supporting PDF/HTML/XML/TXT
- [x] Document upload API (9 endpoints)
- [x] Alembic migrations for document tables
- [x] Neo4j schema with 6 node types, 9 relationships
- [x] Neo4j client with connection pooling
- [x] Graph service with 20+ operations
- [x] Sample data seeding (15+ regulations)
- [x] Compliance checker service
- [x] API routers registered in main.py

### Documentation
- [x] Getting Started guide
- [x] Document Parser documentation
- [x] Neo4j implementation summary
- [x] Neo4j schema documentation
- [x] Neo4j visual schema
- [x] Neo4j quick reference

### Testing
- [x] Test script for document API
- [x] Verification script for Neo4j
- [x] Unit tests for compliance checker

## 🔧 Setup Tasks (Run These Next)

### 1. Install Dependencies ⏳
```bash
cd backend
pip install -r requirements.txt
```

**Verify:**
- PyPDF2==3.0.1 installed
- beautifulsoup4==4.12.3 installed
- lxml==5.1.0 installed

### 2. Start Services ⏳
```bash
# From project root
docker compose up -d
```

**Verify:**
- PostgreSQL running on port 5432
- Neo4j running on port 7687 (browser on 7474)
- Redis running on port 6379
- Elasticsearch running on port 9200

### 3. Run Database Migrations ⏳
```bash
cd backend
alembic upgrade head
```

**Verify:**
- Migration 001_initial_schema applied
- Migration 002_document_models applied
- 6 document tables created

### 4. Initialize Neo4j ⏳
```bash
cd backend
python scripts/init_neo4j.py
```

**Verify:**
- Constraints created
- Indexes created
- Full-text search indexes created

### 5. Seed Neo4j Data ⏳
```bash
cd backend
python scripts/seed_graph_data.py
```

**Verify:**
- 15+ legislation nodes
- 2+ regulation nodes
- 5+ program nodes
- 5+ situation nodes
- Relationships created

### 6. Start API Server ⏳
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Verify:**
- Server starts without errors
- API docs accessible at http://localhost:8000/docs
- Health check passes

### 7. Run Tests ⏳
```bash
cd backend

# Test document API
python scripts/test_document_api.py

# Verify Neo4j graph
python scripts/verify_graph.py

# Run unit tests
pytest -v
```

**Verify:**
- All tests pass
- Document upload works
- Sections extracted correctly
- Cross-references detected

## 🚀 Post-Deployment Verification

### Database Checks
- [ ] PostgreSQL tables exist: `psql -U postgres -d regulatory_db -c "\dt"`
- [ ] Document count: `SELECT COUNT(*) FROM documents;`
- [ ] Neo4j nodes: Query `MATCH (n) RETURN count(n);` in Neo4j Browser

### API Checks
- [ ] Upload a sample document via API
- [ ] Search for documents
- [ ] Retrieve document sections
- [ ] Get cross-references
- [ ] Check statistics

### Neo4j Checks
- [ ] View all legislation: `MATCH (l:Legislation) RETURN l;`
- [ ] Check relationships: `MATCH ()-[r]->() RETURN count(r);`
- [ ] Test full-text search

## 📝 Quick Commands Reference

### Database Operations
```bash
# Check migration status
alembic current

# Rollback migration
alembic downgrade -1

# Apply specific migration
alembic upgrade <revision>

# Generate new migration
alembic revision --autogenerate -m "description"
```

### Docker Operations
```bash
# View logs
docker compose logs -f postgres
docker compose logs -f neo4j

# Restart service
docker compose restart postgres
docker compose restart neo4j

# Stop all services
docker compose down

# Clean restart (removes data)
docker compose down -v
docker compose up -d
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_compliance_checker.py -v
```

### Neo4j Operations
```bash
# Initialize schema
python scripts/init_neo4j.py

# Seed data
python scripts/seed_graph_data.py

# Verify graph
python scripts/verify_graph.py

# Clear all data (WARNING)
python scripts/init_neo4j.py --clear
```

## 🐛 Troubleshooting

### Common Issues

**Issue: `ModuleNotFoundError: No module named 'PyPDF2'`**
```bash
pip install PyPDF2 beautifulsoup4 lxml
```

**Issue: `Connection refused` to PostgreSQL**
```bash
docker compose restart postgres
# Check logs
docker compose logs postgres
```

**Issue: `Connection refused` to Neo4j**
```bash
docker compose restart neo4j
# Wait 30 seconds for Neo4j to start
# Check logs
docker compose logs neo4j
```

**Issue: Alembic can't find models**
```bash
# Make sure you're in backend/ directory
cd backend
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue: PDF extraction fails**
```bash
# Try alternative library
pip install pdfplumber
# Or install dependencies
sudo apt-get install libpoppler-cpp-dev  # Ubuntu/Debian
```

## 📊 Success Metrics

After completing all tasks, you should have:
- ✅ 6 PostgreSQL tables created
- ✅ 15+ legislation documents in Neo4j
- ✅ 20+ relationships in knowledge graph
- ✅ API server running on port 8000
- ✅ All tests passing
- ✅ Sample document uploaded and parsed
- ✅ Cross-references detected

## 🎯 Next Development Tasks

### Short Term
- [ ] Add OCR support for scanned PDFs
- [ ] Implement document versioning
- [ ] Add batch upload capability
- [ ] Enhance cross-reference matching
- [ ] Add document comparison features

### Medium Term
- [ ] Integrate Elasticsearch for full-text search
- [ ] Build React frontend
- [ ] Add user authentication
- [ ] Implement caching with Redis
- [ ] Add document change tracking

### Long Term
- [ ] Machine learning for better parsing
- [ ] Natural language query interface
- [ ] Multi-language support
- [ ] Advanced visualization
- [ ] Production deployment

## 📚 Resources

- API Documentation: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474
- Project Documentation: `docs/`
- Neo4j Schema: `docs/dev/neo4j-schema.md`
- Document Parser Guide: `docs/dev/document-parser.md`

---

**Last Updated:** 2024-11-22

**Status:** Ready for deployment testing
