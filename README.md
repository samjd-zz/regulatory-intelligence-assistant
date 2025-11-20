# Regulatory Intelligence Assistant for Public Service

> **G7 GovAI Grand Challenge 2025** - Statement 2: Navigating Complex Regulations

AI-powered regulatory intelligence system that helps public servants and citizens navigate complex regulatory landscapes through semantic search, natural language Q&A, compliance checking, and guided workflows.

## 🎯 Project Overview

This project addresses the challenge of navigating complex regulatory environments by creating an intelligent system that combines knowledge graphs, semantic search, and AI-powered Q&A to make regulations accessible and actionable.

### Challenge Statement
**"Navigate complex regulations efficiently and accurately"**

### Target Impact
- 60-80% reduction in time to find relevant regulations
- 50-70% reduction in compliance errors
- 40-60% faster application processing
- 80% improvement in regulatory clarity
- 90% user satisfaction with search results

## ✨ Key Features

### Regulatory Knowledge Graph
- **Neo4j Graph Database**: Interconnected regulations, policies, and precedents
- **Automatic Relationship Extraction**: Links between regulations
- **Entity Linking**: Programs, situations, and affected parties
- **Version Control**: Track amendments and changes over time
- **Visual Exploration**: Interactive graph visualization

### Semantic Search
- **Natural Language Queries**: Ask questions in plain language
- **Hybrid Search**: Combines keyword (BM25) + vector (semantic) search
- **Graph Traversal**: Find related regulations automatically
- **Faceted Filtering**: Jurisdiction, date, type, department
- **Relevance Ranking**: ML-powered result ordering

### AI-Powered Q&A
- **RAG System**: Retrieval-Augmented Generation with Gemini API
- **Citation Support**: Links to specific sections in responses
- **Confidence Scoring**: Reliability indicators for answers
- **Context Awareness**: Understands user situation and needs
- **Plain Language**: Translates legalese into clear explanations

### Compliance Checking
- **Requirement Extraction**: Automatically identify requirements from regulatory text using pattern matching
  - 4 pattern types: mandatory, prohibited, conditional, eligibility
  - Confidence scoring for extracted requirements
  - Source citations from regulations
- **Real-time Validation**: Field-level validation as users type
  - 8 validation types: required, pattern, length, range, in_list, date_format, conditional, combined
  - Sub-50ms response time for instant feedback
- **Full Compliance Checks**: Comprehensive validation before submission
  - Rule caching for performance (1-hour TTL)
  - Confidence scoring (0.5-0.95 range)
  - Severity levels: critical, high, medium, low
- **Intelligent Reporting**: Actionable compliance reports with:
  - Issue descriptions with field-specific errors
  - Regulatory citations for each requirement
  - Suggestions for resolving issues
  - Next steps and recommendations
- **RESTful API**: 6 endpoints for compliance operations
  - `/check`: Full compliance validation
  - `/validate-field`: Real-time field validation
  - `/requirements/extract`: Extract requirements from text
  - `/requirements/{program_id}`: Get program rules
  - `/metrics`: Compliance analytics
  - `/cache/{program_id}`: Cache management

### Guided Workflows
- **Step-by-Step Assistance**: Walk users through complex processes
- **Contextual Help**: Relevant information at each step
- **Progress Tracking**: Visual workflow completion status
- **Smart Forms**: Auto-fill and validation
- **Decision Trees**: Guide users through eligibility

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React, TypeScript, Tailwind CSS
- **Backend**: FastAPI (Python)
- **Graph Database**: Neo4j (Community Edition)
- **Search**: Elasticsearch (keyword + vector)
- **Relational DB**: PostgreSQL
- **Cache**: Redis
- **AI Services**: Gemini API (RAG), OpenAI (embeddings)

### System Components
```
┌─────────────────┐
│  React Frontend │
└────────┬────────┘
         │
┌────────▼────────┐
│   FastAPI API   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Search │ │  RAG   │ │ Graph  │ │Compliance│
│Service │ │Service │ │Query   │ │ Checker │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │
     └──────────┴──────────┴──────────┘
                │
         ┌──────┴───────┬────────────┐
         ▼              ▼            ▼
    ┌────────┐   ┌──────────┐  ┌────────┐
    │Postgres│   │Elasticsearch│ │ Neo4j  │
    └────────┘   └──────────┘  └────────┘
```

## 📚 Documentation

### Planning & Architecture
- **[Idea Document](./docs/idea.md)**: Initial concept and vision
- **[PRD](./docs/prd.md)**: Comprehensive product requirements
- **[Design Document](./docs/design.md)**: Technical architecture and implementation details
- **[Implementation Plan](./docs/plan.md)**: 2-week sprint plan with detailed steps
- **[Parallel Execution Plan](./docs/parallel-plan.md)**: Optimized parallel work streams for 4-developer team

### Technical Documentation
- **[Neo4j Knowledge Graph](./docs/dev/neo4j-knowledge-graph.md)**: Complete graph schema, query patterns, and API usage
- **[Neo4j MCP Setup](./docs/dev/neo4j-mcp-setup.md)**: MCP server configuration for AI-powered graph operations
- **[Database Management](./docs/dev/database-management.md)**: PostgreSQL schema, models, and migrations guide
- **[Compliance Engine](./docs/dev/compliance-engine.md)**: Comprehensive compliance checking system with validation types, API reference, and integration guide

### Development Guides
- **[Developer Assignments](./docs/developer-assignments.md)**: Team member responsibilities and work streams

## 🚀 Quick Start (MVP)

### Prerequisites
- Python 3.11+ or 3.12
- Node.js 18+
- Docker & Docker Compose
- Git
- API Keys: Gemini API (for RAG), OpenAI API (for embeddings)

**Note:** All database services (PostgreSQL, Neo4j, Elasticsearch, Redis) run in Docker containers - no local installation needed!

### Installation

```bash
# Clone the repository
git clone https://github.com/samjd-zz/regulatory-intelligence-assistant.git
cd regulatory-intelligence-assistant

# Set up environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your database credentials and API keys

# Start all services with Docker Compose
docker-compose up -d

# This starts:
# - PostgreSQL (port 5432) - Relational database
# - Neo4j (ports 7474, 7687) - Knowledge graph database
# - Elasticsearch (port 9200) - Search engine
# - Redis (port 6379) - Cache layer

# Wait ~30 seconds for services to be ready, then verify:
docker ps

# Set up backend environment
cd backend

# Option 1: Using Python venv (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Option 2: Using conda (if you prefer)
# conda create -n regulatory-ai python=3.12
# conda activate regulatory-ai

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations (PostgreSQL)
alembic upgrade head

# Initialize Neo4j knowledge graph with schema and sample data
python scripts/init_neo4j.py

# (Optional) Seed PostgreSQL with additional sample data
python seed_data.py

# Start FastAPI backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In a new terminal: Install frontend dependencies
cd frontend
npm install
npm run dev
```

### Verify Installation

```bash
# Check all services are healthy
curl http://localhost:8000/health/all | jq

# Expected output:
# {
#   "status": "healthy",
#   "services": {
#     "postgres": { "status": "healthy", "tables": 11, ... },
#     "neo4j": { "status": "healthy", ... },
#     "elasticsearch": { "status": "healthy", ... },
#     "redis": { "status": "healthy", ... }
#   }
# }

# Verify Neo4j knowledge graph specifically
cd backend
python scripts/verify_graph.py

# Expected output:
# ============================================================
# Neo4j Knowledge Graph Verification
# ============================================================
#
# 1. Checking Neo4j connectivity...
#    ✓ Connected to Neo4j successfully
#
# 2. Graph Statistics:
#    Nodes:
#      - Legislation: 4
#      - Section: 4
#      - Regulation: 1
#      - Program: 3
#      - Situation: 2
#    ...

# View API documentation
open http://localhost:8000/docs

# Explore Neo4j graph visually
open http://localhost:7474
# Login: neo4j / password123
# Run query: MATCH (n) RETURN n LIMIT 50
```

### Access Points
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Neo4j Browser: http://localhost:7474
- Elasticsearch: http://localhost:9200

## 👥 Team Structure (4 People)

- **Developer 1**: Full-Stack (React + Python/FastAPI)
- **Developer 2**: AI/ML Engineer (NLP, RAG, Legal Language Processing)
- **Developer 3**: Backend/Graph Engineer (Neo4j, Knowledge Graph, Data Pipeline)
- **Developer 4**: Frontend/UX (Search Interface, Workflow UI)

## 📅 Timeline

**2-Week MVP Sprint** (November 17 - December 1, 2025)

### Week 1: Foundation & Knowledge
- Days 1-2: Setup, Neo4j graph, database schema
- Days 3-4: Document ingestion, graph population, legal NLP
- Days 5-7: Elasticsearch, hybrid search, Gemini RAG

### Week 2: Features & Demo
- Days 8-10: Compliance checking, React UI, workflows
- Days 11-12: Testing, quality evaluation, bug fixes
- Days 13-14: Demo preparation, documentation

## 🎯 MVP Scope

### In Scope
✅ Regulatory knowledge graph with 50-100 regulations  
✅ Neo4j graph database for relationships  
✅ Semantic search with Elasticsearch  
✅ Q&A system using Gemini API RAG  
✅ Compliance checking for basic scenarios  
✅ Simple web interface for search and Q&A  
✅ Demo video showing regulatory search and compliance  

### Future Enhancements
- Change monitoring and alerting
- Multi-jurisdiction support
- Advanced workflow engine
- Integration with case management
- Mobile app for field workers
- API for third-party integrations

## 🧪 Testing

### Search Quality Testing
- Precision@10 metrics
- Legal expert evaluation
- User testing with caseworkers

### RAG Accuracy Testing
- Answer quality ratings
- Citation accuracy verification
- Legal expert validation

### Compliance Testing
- Test scenarios for various regulations
- False positive/negative rates
- Edge case handling

### Quality Metrics
- Search Precision@10: >80%
- RAG answer quality: >4/5
- Citation accuracy: >95%
- Compliance detection: >80%
- Response time: <5 seconds

## 🔍 Knowledge Graph Structure

### Node Types
- **Legislation**: Acts, laws, statutes
- **Section**: Individual sections and subsections
- **Regulation**: Regulatory provisions
- **Policy**: Government policies and guidelines
- **Program**: Government programs and services
- **Situation**: Applicable scenarios

### Relationship Types
- **HAS_SECTION**: Legislation → Section
- **REFERENCES**: Section → Section (cross-references)
- **AMENDED_BY**: Section → Section (amendments)
- **APPLIES_TO**: Regulation → Program
- **RELEVANT_FOR**: Section → Situation
- **IMPLEMENTS**: Regulation → Legislation

## 🤖 RAG System

### How It Works
1. User asks a question in natural language
2. System performs hybrid search to find relevant regulations
3. Top results sent to Gemini API with the question
4. Gemini generates answer with citations
5. System extracts and validates citations
6. Response returned with confidence score

### Example
**Question**: "Can a temporary resident apply for employment insurance?"

**Answer**: "Yes, temporary residents can apply for employment insurance if they have a valid work permit. According to Section 7(1) of the Employment Insurance Act, benefits are payable to insured persons who meet the eligibility requirements, which include being authorized to work in Canada."

**Citations**: 
- Employment Insurance Act, S.C. 1996, c. 23, s. 7(1)
- Confidence: High

## 🔒 Security & Compliance

- JWT authentication with refresh tokens
- RBAC with fine-grained permissions
- Document-level access control
- Audit trail of all queries
- No storage of personal case data
- Anonymized query logging
- Content authenticity verification
- Cryptographic signatures on regulations

## 📊 Success Metrics

### Time Savings
- Search time: -60-80%
- Application processing: -40-60%
- Research time: -50-70%
- Staff time freed: 30-40%

### Quality Improvements
- Compliance errors: -50-70%
- Application accuracy: +40-60%
- User confidence: +80%
- Self-service success: +70%

## 🤝 Contributing

This is a G7 GovAI Challenge submission. For collaboration inquiries, please contact the team.

## 📄 License

To be determined based on challenge requirements.

## 🏆 G7 Challenge Information

- **Competition**: G7 GovAI Grand Challenge 2025
- **Host**: Government of Canada (Treasury Board Secretariat)
- **Period**: November 17 - December 1, 2025
- **Funding**: Up to $10,000 CAD for selected solutions
- **Challenge Statement**: #2 - Navigating Complex Regulations

## 💡 Use Cases

### Caseworkers
- Quickly find applicable regulations
- Understand eligibility criteria
- Check application compliance
- Get guided workflows for complex cases

### Policy Analysts
- Research regulatory landscape
- Find related regulations and precedents
- Track regulatory changes
- Analyze policy impacts

### Citizens
- Understand government requirements
- Self-assess eligibility
- Get step-by-step guidance
- Access plain language explanations

### Legal Researchers
- Search across jurisdictions
- Find cross-references and relationships
- Track amendments and versions
- Export citations

## 📞 Contact

For questions or support, please refer to the project documentation or contact the development team.

---

**Status**: 🚧 In Development (MVP Phase - Phase 1 Complete)  
**Last Updated**: November 20, 2025

### Current Progress

**Phase 1: Foundation (Days 1-2)** ✅ COMPLETE
- ✅ Stream 1A: Backend Setup & Database (Developer 1)
  - PostgreSQL database with 10 models and Alembic migrations
  - FastAPI server with comprehensive health checks
  - Docker Compose with all services (PostgreSQL, Neo4j, Elasticsearch, Redis)
  
- ✅ Stream 1B: Neo4j Knowledge Graph Setup (Developer 3)
  - Complete graph schema with 6 node types and 9 relationship types
  - Neo4j client with connection pooling and JSON serialization
  - Graph service with full CRUD operations
  - Sample data: 4 Acts, 4 Sections, 1 Regulation, 3 Programs, 2 Situations
  - Comprehensive documentation and verification scripts

**Phase 4: Compliance & Frontend (Days 8-10)** - IN PROGRESS
- ✅ Stream 4A: Compliance Checking Engine (Developer 1) - COMPLETE
  - **Architecture**: 3-tier system (RequirementExtractor → RuleEngine → ComplianceChecker)
  - **Schemas**: Comprehensive Pydantic v2 models for all compliance operations
  - **RequirementExtractor**: Pattern-based extraction from regulatory text
    - 4 pattern types: mandatory_field, prohibited_action, conditional_requirement, eligibility_criteria
    - Priority-ordered matching to handle complex sentences
    - Confidence scoring and source citations
  - **RuleEngine**: 8 validation types with flexible logic
    - Basic: required, pattern, min/max_length
    - Advanced: range, in_list, date_format, conditional
    - Combined: multiple validations per field
  - **ComplianceChecker**: Full orchestration with optimization
    - Rule caching with 1-hour TTL
    - Confidence scoring (coverage + pass_rate)
    - Severity levels (critical, high, medium, low)
    - Actionable recommendations and next steps
  - **REST API**: 6 endpoints for complete compliance workflow
    - POST `/check`: Full compliance validation (<200ms)
    - POST `/validate-field`: Real-time field validation (<50ms)
    - POST `/requirements/extract`: Requirement extraction (<500ms)
    - GET `/requirements/{program_id}`: Retrieve program rules
    - GET `/metrics`: Compliance analytics and reporting
    - DELETE `/cache/{program_id}`: Manual cache invalidation
  - **Testing**: 24 unit tests with 100% pass rate
  - **Documentation**: Complete API reference, validation guide, and integration examples
  - **Performance**: Optimized with caching and async operations

**Next Streams**: 
- Stream 2A: Document Parsing & Graph Population (Developer 3)
- Stream 2B: Legal NLP Processing (Developer 2)
- Stream 3A: Hybrid Search System (Developers 2 & 4)
- Stream 3B: Gemini RAG System (Developer 2)
- Stream 4B: Frontend Development (Developer 4)
