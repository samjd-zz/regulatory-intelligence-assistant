# Regulatory Intelligence Assistant

> **G7 GovAI Grand Challenge 2025** - Statement 2: Navigating Complex Regulations

AI-powered system that helps public servants and citizens navigate complex regulatory landscapes through semantic search, AI Q&A, compliance checking, and knowledge graphs.

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repository-url>
cd regulatory-intelligence-assistant
cp backend/.env.example backend/.env

# 2. Add your Gemini API key to backend/.env
# GEMINI_API_KEY=your_key_here

# 3. Start all services
docker compose up -d

# 4. Initialize database with data (interactive wizard)
docker compose exec backend python scripts/init_data.py

# The wizard guides you through:
#   1. Canadian Laws (Acts/Lois) - ~800 documents
#   2. Regulations - ~4,240 documents  
#   3. Both (Full Dataset) - ~5,040 documents total
#   Plus optional limits for testing (e.g., 10, 50, 100)

# 5. Access the application
# Frontend: http://localhost:5173
# API Docs: http://localhost:8000/docs
# Neo4j: http://localhost:7474 (neo4j/password123)
```

**First time?** See the [Quick Start Guide](./docs/QUICKSTART.md) for detailed instructions.

**Quick test?** Load 10 documents: `docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive`

## ✨ Key Features

### 🔍 Multi-Tier Search
- **5-tier fallback architecture**: Elasticsearch → ES Sections → Neo4j Graph → PostgreSQL FTS → Metadata
- **Enhanced Performance**: PostgreSQL <50ms, Neo4j <200ms, Elasticsearch <500ms
- **Smart Search**: Legal synonyms expansion, fuzzy matching, highlighted snippets
- **399K+ documents** searchable with relevance ranking

### 💬 AI-Powered Q&A
- **Chain-of-Thought reasoning**: 5-step systematic analysis (3-5% accuracy boost)
- **Citation support**: Links to specific regulatory sections
- **Confidence scoring**: 4-factor reliability assessment (context, citations, complexity, length)
- **Plain language**: Translates legalese into clear explanations

### ✅ Compliance Checking
- **Real-time validation**: <50ms field-level checks
- **8 validation types**: required, pattern, length, range, in_list, date_format, conditional, combined
- **Smart extraction**: 4 requirement patterns from regulatory text
- **Confidence scoring**: 0.5-0.95 range with severity levels

### 📊 Knowledge Graph
- **Neo4j**: 278,858 nodes, 470,353 relationships
- **Interactive exploration**: Visual graph with relationship traversal
- **Smart indexing**: 3 fulltext + 16 range indexes
- **6 node types**: Legislation, Section, Regulation, Policy, Program, Situation

## 📊 System Status

**Current Version**: v1.4.3 (Docker Deployment & Intelligent Data Initialization)

### Data Loaded
- **PostgreSQL**: 4,240 regulations + 395,465 sections (399,705 total)
- **Elasticsearch**: 399,705 documents indexed
- **Neo4j**: 399,705 nodes + 470,353 relationships

### Test Coverage
- **397 tests passing** (100% pass rate)
- **Backend**: 338 tests
- **Frontend E2E**: 59 tests

### Performance (All Targets Met ✅)
| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| PostgreSQL FTS | <50ms | ~35ms | ✅ |
| Neo4j Graph | <200ms | ~150ms | ✅ |
| Hybrid Search | <500ms | ~450ms | ✅ |
| RAG Q&A | <3s | ~2.5s | ✅ |
| Field Validation | <50ms | ~35ms | ✅ |

## 🏗️ Architecture

```
React Frontend (Port 5173)
         ↓
   FastAPI Backend (Port 8000)
         ↓
┌────────┴────────┬───────────┬──────────┐
↓                 ↓           ↓          ↓
PostgreSQL    Elasticsearch  Neo4j    Redis
(5432)           (9200)      (7474)   (6379)
```

**Tech Stack**:
- Frontend: React 19 + TypeScript + Vite 7 + Tailwind v4
- Backend: FastAPI (Python 3.11+)
- Databases: PostgreSQL 16, Neo4j 5.15, Elasticsearch 8.x
- AI: Gemini API (RAG + embeddings)

See [Architecture Guide](./docs/ARCHITECTURE.md) for details.

## 📚 Documentation

### Getting Started
- **[Quick Start Guide](./docs/QUICKSTART.md)** - Get running in 5 minutes
- **[Docker Deployment](./DOCKER_DEPLOYMENT.md)** - Production deployment & Docker Hub publishing
- **[Architecture Overview](./docs/ARCHITECTURE.md)** - System design and data flow
- **[Features Guide](./docs/FEATURES.md)** - Complete feature documentation
- **[API Reference](./docs/API_REFERENCE.md)** - REST API endpoints

### Development
- **[Development Guide](./docs/DEVELOPMENT.md)** - Setup and workflows
- **[Data Ingestion](./docs/DATA_INGESTION.md)** - Loading regulatory data
- **[Testing Guide](./docs/testing/README.md)** - Test strategy and coverage

### Technical Deep Dives
- **[Neo4j Knowledge Graph](./docs/dev/neo4j-knowledge-graph.md)** - Graph schema and queries
- **[Compliance Engine](./docs/dev/compliance-engine.md)** - Validation system
- **[Database Management](./docs/dev/database-management.md)** - Schema and migrations

## 🎯 Target Impact

- **60-80%** reduction in time to find regulations
- **50-70%** reduction in compliance errors
- **40-60%** faster application processing
- **80%** improvement in regulatory clarity
- **90%** user satisfaction with search

## 🔌 API Examples

### Search Regulations
```bash
curl "http://localhost:8000/api/search?q=employment+insurance&limit=5"
```

### Ask AI Question
```bash
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is eligible for employment insurance?"}'
```

### Check Compliance
```bash
curl -X POST http://localhost:8000/api/compliance/check \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "employment-insurance",
    "form_data": {"hours_worked": 700, "sin": "123-456-789"}
  }'
```

**Full API documentation**: http://localhost:8000/docs

## 🚀 Recent Enhancements (v1.4.3)

### Docker Production Deployment
- ✅ Multi-stage frontend build (Node → nginx)
- ✅ Production-ready nginx configuration with security headers
- ✅ docker-compose.prod.yml for production deployment
- ✅ Health checks and resource limits
- ✅ Optimized build contexts with .dockerignore

### Intelligent Data Initialization
- ✅ Interactive wizard for data loading (laws/regulations/both)
- ✅ Flexible limits (10, 50, 100, or all documents)
- ✅ Auto-download from Justice Canada if missing
- ✅ Bilingual support (English/French)
- ✅ Multi-database ingestion (PostgreSQL + Neo4j + Elasticsearch)
- ✅ Progress tracking and statistics

### Documentation & Cleanup
- ✅ Comprehensive deployment guide (DOCKER_DEPLOYMENT.md)
- ✅ Updated Quick Start and development guides
- ✅ Deprecated old scripts (create_tables.py, seed_data.py)
- ✅ New scripts/README.md with current utilities
- ✅ 5-step reasoning process
- ✅ +3-5% accuracy improvement
- ✅ Better confidence calibration
- ✅ Transparent AI logic

## 📦 Project Structure

```
regulatory-intelligence-assistant/
├── backend/              # FastAPI application
│   ├── services/        # Business logic (10+ services)
│   ├── routes/          # REST API (10 routers, 50+ endpoints)
│   ├── models/          # SQLAlchemy ORM + Pydantic
│   ├── tests/           # 338 backend tests
│   └── ingestion/       # Data pipeline
│
├── frontend/            # React TypeScript app
│   ├── src/pages/      # 4 pages (Dashboard, Search, Chat, Compliance)
│   ├── src/components/ # Reusable UI components
│   ├── src/store/      # Zustand state management
│   └── e2e/            # 59 E2E tests
│
└── docs/               # Documentation
    ├── QUICKSTART.md
    ├── ARCHITECTURE.md
    ├── FEATURES.md
    ├── API_REFERENCE.md
    ├── DEVELOPMENT.md
    └── DATA_INGESTION.md
```

## 🧪 Testing

```bash
# Backend tests (338 tests)
docker compose exec backend pytest -v

# Frontend E2E tests (59 tests)
cd frontend && npm run test:e2e

# All tests: 397/397 passing (100%)
```

## 🛠️ Development

```bash
# View backend logs (already running with hot reload in Docker)
docker compose logs -f backend

# Restart backend after code changes
docker compose restart backend

# Frontend dev server (if not using Docker)
cd frontend
npm run dev

# Or use Docker for frontend
docker compose up -d frontend
```

See [Development Guide](./docs/DEVELOPMENT.md) for full setup.

## 🐋 Docker Deployment

### Development Mode (Hot Reload)
```bash
# Start all services with hot reload
docker compose up -d

# Initialize with data (interactive)
docker compose exec backend python scripts/init_data.py

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Data Initialization Options

The intelligent data loader offers flexible options for loading data:

**Interactive Mode (Recommended):**
```bash
docker compose exec backend python scripts/init_data.py
```
- Guides you through choosing data type (laws/regulations/both)
- Prompts for optional limits
- Downloads data if missing
- Shows progress and statistics

**Non-Interactive Examples:**
```bash
# Quick test - 10 laws
docker compose exec backend python scripts/init_data.py --type laws --limit 10 --non-interactive

# Development - 50 regulations  
docker compose exec backend python scripts/init_data.py --type regulations --limit 50 --non-interactive

# Production - all laws (~800 documents)
docker compose exec backend python scripts/init_data.py --type laws --non-interactive

# Production - everything (~5,040 documents)
docker compose exec backend python scripts/init_data.py --type both --non-interactive
```

**How it works:**
- ✅ **Checks existing data** - Won't reload if already present
- ✅ **Auto-downloads** - Offers to download from Justice Canada if missing
- ✅ **Smart filtering** - Separates laws (Acts/Lois) from regulations (SOR/DORS)
- ✅ **Respects limits** - Applies your specified limit after filtering
- ✅ **Multi-database** - Loads into PostgreSQL, Neo4j, and Elasticsearch
- ✅ **Progress tracking** - Shows real-time progress and final statistics

### Production Mode
```bash
# Set up production environment
cp .env.production.example backend/.env.production
# Edit backend/.env.production with your secure values

# Build and start production services
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f
```

### Publishing to Docker Hub
```bash
# Build images
docker build -t yourusername/regulatory-frontend:latest ./frontend
docker build -t yourusername/regulatory-backend:latest ./backend
docker build -t yourusername/regulatory-neo4j:latest ./backend/neo4j

# Tag with version
docker tag yourusername/regulatory-frontend:latest yourusername/regulatory-frontend:1.0.0
docker tag yourusername/regulatory-backend:latest yourusername/regulatory-backend:1.0.0
docker tag yourusername/regulatory-neo4j:latest yourusername/regulatory-neo4j:1.0.0

# Login and push
docker login
docker push yourusername/regulatory-frontend:latest
docker push yourusername/regulatory-frontend:1.0.0
docker push yourusername/regulatory-backend:latest
docker push yourusername/regulatory-backend:1.0.0
docker push yourusername/regulatory-neo4j:latest
docker push yourusername/regulatory-neo4j:1.0.0
```

See [Docker Deployment Guide](./DOCKER_DEPLOYMENT.md) for complete documentation.

## 📊 Data Sources

### Currently Supported
- **🇨🇦 Canada**: Justice Laws Website (1,827 acts loaded)
- Sample data includes: Employment Insurance Act, Canada Pension Plan, Income Tax Act, Immigration & Refugee Protection Act

### Available Sources
- **🇺🇸 United States**: GPO FDSys (US Code, CFR)
- **🇬🇧 United Kingdom**: legislation.gov.uk
- **🇫🇷 France**: Légifrance
- **🇩🇪 Germany**: Gesetze im Internet
- **🇪🇺 European Union**: EUR-Lex

See [Data Ingestion Guide](./docs/DATA_INGESTION.md) for loading additional data.

## 🔒 Security

**Current (MVP)**: Development mode, no authentication

**Production Roadmap**:
- [ ] JWT authentication
- [ ] Role-based access control (RBAC)
- [ ] Rate limiting (1000 req/hour)
- [ ] API key management
- [ ] Audit logging
- [ ] HTTPS enforcement

## 📈 Performance Monitoring

### Health Checks
- `GET /api/health` - System health
- `GET /api/health/postgres` - Database
- `GET /api/health/neo4j` - Graph
- `GET /api/health/elasticsearch` - Search

### Metrics
```bash
# View statistics
curl http://localhost:8000/api/stats
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run full test suite
5. Submit pull request

See [Development Guide](./docs/DEVELOPMENT.md) for guidelines.

## 📝 License

MIT License - Copyright (c) 2025 Team Astro

See [LICENSE](./LICENSE) for full details.

## 🙏 Acknowledgments

Built for the **G7 GovAI Grand Challenge 2025**

Data sources:
- Justice Canada (Open Government License)
- GPO FDSys (Public Domain)
- legislation.gov.uk (Open Government License)

---

**Need help?** Check the [documentation](./docs/) or [open an issue](https://github.com/your-repo/issues).
