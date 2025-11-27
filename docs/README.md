# Documentation Index

Welcome to the **Regulatory Intelligence Assistant** documentation. This guide helps you navigate all project documentation organized by category.

## 📋 Quick Navigation

- **[Main README](../README.md)** - Project overview, features, and quick start
- **[Getting Started](../GETTING_STARTED.md)** - Detailed setup instructions
- **[Deployment Checklist](../DEPLOYMENT_CHECKLIST.md)** - Production deployment guide

---

## 📁 Documentation Categories

### 🎯 Planning & Requirements ([planning/](./planning/))

Strategic planning, product requirements, and project roadmaps.

- **[prd.md](./planning/prd.md)** - Complete Product Requirements Document with features, architecture, and success metrics
- **[idea.md](./planning/idea.md)** - Initial concept and vision for the Regulatory Intelligence Assistant
- **[plan.md](./planning/plan.md)** - Detailed 2-week implementation plan with daily tasks
- **[parallel-plan.md](./planning/parallel-plan.md)** - Optimized parallel execution plan for 4-developer team

### 🎨 Design & Architecture ([design/](./design/))

UI/UX designs, system architecture, and technical specifications.

- **[design.md](./design/design.md)** - Complete technical architecture and system design
- **[ui-design.md](./design/ui-design.md)** - UI/UX design specifications and patterns
- **[mvp-ui-plan.md](./design/mvp-ui-plan.md)** - MVP user interface implementation plan
- **[ui-implementation-plan.md](./design/ui-implementation-plan.md)** - Detailed UI component implementation guide
- **[G7_JUDGING_CRITERIA_UI_ENHANCEMENTS.md](./design/G7_JUDGING_CRITERIA_UI_ENHANCEMENTS.md)** - G7 Challenge-specific UI enhancements

### 🛠️ Development Guides ([dev/](./dev/))

Technical documentation for developers working on the system.

#### Setup & Configuration
- **[BAITMAN_developer_setup.md](./dev/BAITMAN_developer_setup.md)** - Complete developer environment setup guide
- **[developer-assignments.md](./dev/developer-assignments.md)** - Team member responsibilities and work streams

#### Core Services
- **[BAITMAN_legal-nlp-service.md](./dev/BAITMAN_legal-nlp-service.md)** - Legal NLP service documentation (entity extraction, query parsing)
- **[BAITMAN_rag-service.md](./dev/BAITMAN_rag-service.md)** - RAG Q&A system with Gemini API
- **[BAITMAN_search-service.md](./dev/BAITMAN_search-service.md)** - Hybrid search system (keyword + semantic)
- **[compliance-engine.md](./dev/compliance-engine.md)** - Compliance checking engine with validation types
- **[document-parser.md](./dev/document-parser.md)** - Multi-format document parsing (PDF, XML, HTML, TXT, DOCX)

#### Knowledge Graph
- **[neo4j-knowledge-graph.md](./dev/neo4j-knowledge-graph.md)** - Complete graph schema and query patterns
- **[neo4j-schema.md](./dev/neo4j-schema.md)** - Detailed Neo4j schema documentation
- **[neo4j-visual-schema.md](./dev/neo4j-visual-schema.md)** - Visual guide to graph structure
- **[neo4j-quick-reference.md](./dev/neo4j-quick-reference.md)** - Quick reference for common queries
- **[neo4j-implementation-summary.md](./dev/neo4j-implementation-summary.md)** - Implementation summary and architecture
- **[neo4j-mcp-setup.md](./dev/neo4j-mcp-setup.md)** - MCP server configuration for AI operations
- **[knowledge-graph-implementation.md](./dev/knowledge-graph-implementation.md)** - Knowledge graph construction from documents
- **[KNOWLEDGE_GRAPH_COMPLETE.md](./dev/KNOWLEDGE_GRAPH_COMPLETE.md)** - Graph completion status and summary

#### Database & Infrastructure
- **[database-management.md](./dev/database-management.md)** - PostgreSQL schema, models, and migrations
- **[GEMINI_RAG_FIX_REPORT.md](./dev/GEMINI_RAG_FIX_REPORT.md)** - Gemini API integration fixes and solutions

### 🧪 Testing & Quality ([testing/](./testing/))

Test reports, coverage analysis, and quality metrics.

- **[TEST_EXECUTION_REPORT.md](./testing/TEST_EXECUTION_REPORT.md)** - Comprehensive test execution report (338/338 tests passing)
- **[TEST_COVERAGE_REPORT.md](./testing/TEST_COVERAGE_REPORT.md)** - Code coverage analysis by service

### 📊 Reports & Status ([reports/](./reports/))

Progress reports, compliance status, and data ingestion summaries.

- **[DATA_INGESTION_MVP_COMPLETE.md](./reports/DATA_INGESTION_MVP_COMPLETE.md)** - MVP data ingestion completion report
- **[DATA_INGESTION_COMPLETE.md](./reports/DATA_INGESTION_COMPLETE.md)** - Full data ingestion pipeline report
- **[DATA_VERIFICATION_REPORT.md](./reports/DATA_VERIFICATION_REPORT.md)** - Data quality verification across databases
- **[BAITMAN_COMPLIANCE_REPORT.md](./reports/BAITMAN_COMPLIANCE_REPORT.md)** - System compliance and quality report
- **[DEVELOPER_METRICS.md](./reports/DEVELOPER_METRICS.md)** - Development velocity and metrics

### 🚀 Deployment ([deployment/](./deployment/))

Production deployment guides and checklists.

- **[BAITMAN_production_deployment_checklist.md](./deployment/BAITMAN_production_deployment_checklist.md)** - Production deployment tasks and verification

---

## 🎓 Learning Paths

### For New Developers

1. Start with **[BAITMAN_developer_setup.md](./dev/BAITMAN_developer_setup.md)** for environment setup
2. Read **[prd.md](./planning/prd.md)** to understand project goals
3. Review **[design.md](./design/design.md)** for system architecture
4. Check **[developer-assignments.md](./dev/developer-assignments.md)** for team structure
5. Explore service-specific docs in [dev/](./dev/) based on your role

### For Understanding the System

1. **Overview**: [Main README](../README.md)
2. **Architecture**: [design.md](./design/design.md)
3. **Data Flow**: [DATA_INGESTION_MVP_COMPLETE.md](./reports/DATA_INGESTION_MVP_COMPLETE.md)
4. **Knowledge Graph**: [neo4j-knowledge-graph.md](./dev/neo4j-knowledge-graph.md)
5. **API Reference**: [http://localhost:8000/docs](http://localhost:8000/docs) (when running)

### For Deployment

1. **[Getting Started](../GETTING_STARTED.md)** - Local development setup
2. **[DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md)** - Deployment verification
3. **[BAITMAN_production_deployment_checklist.md](./deployment/BAITMAN_production_deployment_checklist.md)** - Production tasks

---

## 🔍 Finding Documentation

### By Topic

| Topic | Primary Documentation | Related Docs |
|-------|---------------------|--------------|
| **Setup** | [BAITMAN_developer_setup.md](./dev/BAITMAN_developer_setup.md) | [Getting Started](../GETTING_STARTED.md), [Deployment Checklist](../DEPLOYMENT_CHECKLIST.md) |
| **Search** | [BAITMAN_search-service.md](./dev/BAITMAN_search-service.md) | [design.md](./design/design.md) |
| **Q&A/RAG** | [BAITMAN_rag-service.md](./dev/BAITMAN_rag-service.md) | [GEMINI_RAG_FIX_REPORT.md](./dev/GEMINI_RAG_FIX_REPORT.md) |
| **Compliance** | [compliance-engine.md](./dev/compliance-engine.md) | [BAITMAN_COMPLIANCE_REPORT.md](./reports/BAITMAN_COMPLIANCE_REPORT.md) |
| **Knowledge Graph** | [neo4j-knowledge-graph.md](./dev/neo4j-knowledge-graph.md) | [neo4j-schema.md](./dev/neo4j-schema.md), [KNOWLEDGE_GRAPH_COMPLETE.md](./dev/KNOWLEDGE_GRAPH_COMPLETE.md) |
| **Legal NLP** | [BAITMAN_legal-nlp-service.md](./dev/BAITMAN_legal-nlp-service.md) | [document-parser.md](./dev/document-parser.md) |
| **Data Ingestion** | [DATA_INGESTION_MVP_COMPLETE.md](./reports/DATA_INGESTION_MVP_COMPLETE.md) | [backend/ingestion/README.md](../backend/ingestion/README.md) |
| **Testing** | [TEST_EXECUTION_REPORT.md](./testing/TEST_EXECUTION_REPORT.md) | [TEST_COVERAGE_REPORT.md](./testing/TEST_COVERAGE_REPORT.md) |
| **UI/Frontend** | [ui-design.md](./design/ui-design.md) | [frontend/README.md](../frontend/README.md), [frontend/TESTING.md](../frontend/TESTING.md) |
| **Database** | [database-management.md](./dev/database-management.md) | [backend/alembic/](../backend/alembic/) |

### By Developer Role

#### Full-Stack Developer
- [BAITMAN_developer_setup.md](./dev/BAITMAN_developer_setup.md)
- [design.md](./design/design.md)
- [database-management.md](./dev/database-management.md)
- [ui-implementation-plan.md](./design/ui-implementation-plan.md)

#### AI/ML Engineer
- [BAITMAN_legal-nlp-service.md](./dev/BAITMAN_legal-nlp-service.md)
- [BAITMAN_rag-service.md](./dev/BAITMAN_rag-service.md)
- [BAITMAN_search-service.md](./dev/BAITMAN_search-service.md)
- [document-parser.md](./dev/document-parser.md)

#### Backend/Graph Engineer
- [neo4j-knowledge-graph.md](./dev/neo4j-knowledge-graph.md)
- [knowledge-graph-implementation.md](./dev/knowledge-graph-implementation.md)
- [neo4j-implementation-summary.md](./dev/neo4j-implementation-summary.md)
- [DATA_INGESTION_MVP_COMPLETE.md](./reports/DATA_INGESTION_MVP_COMPLETE.md)

#### Frontend/UX Developer
- [ui-design.md](./design/ui-design.md)
- [mvp-ui-plan.md](./design/mvp-ui-plan.md)
- [ui-implementation-plan.md](./design/ui-implementation-plan.md)
- [G7_JUDGING_CRITERIA_UI_ENHANCEMENTS.md](./design/G7_JUDGING_CRITERIA_UI_ENHANCEMENTS.md)

---

## 📚 External Resources

### Code Documentation
- **Backend API**: http://localhost:8000/docs (Interactive Swagger docs)
- **Backend Tests**: [backend/tests/README_TESTING.md](../backend/tests/README_TESTING.md)
- **Frontend**: [frontend/README.md](../frontend/README.md)
- **Frontend E2E**: [frontend/e2e/README.md](../frontend/e2e/README.md)
- **Data Ingestion**: [backend/ingestion/README.md](../backend/ingestion/README.md)

### Neo4j Resources
- **Neo4j Browser**: http://localhost:7474 (Visual graph exploration)
- **Neo4j Schema**: [neo4j-schema.md](./dev/neo4j-schema.md)
- **Quick Reference**: [neo4j-quick-reference.md](./dev/neo4j-quick-reference.md)

### AI/ML Resources
- **Gemini API**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **RAG Service**: [BAITMAN_rag-service.md](./dev/BAITMAN_rag-service.md)
- **NLP Service**: [BAITMAN_legal-nlp-service.md](./dev/BAITMAN_legal-nlp-service.md)

---

## 🆘 Getting Help

### Common Issues
1. Check [Getting Started](../GETTING_STARTED.md) troubleshooting section
2. Review service-specific docs in [dev/](./dev/)
3. Check [TEST_EXECUTION_REPORT.md](./testing/TEST_EXECUTION_REPORT.md) for known test issues
4. See [GEMINI_RAG_FIX_REPORT.md](./dev/GEMINI_RAG_FIX_REPORT.md) for Gemini API issues

### Documentation Updates
This documentation is actively maintained. Last major update: **November 27, 2025**

---

## 📝 Document Conventions

### File Naming
- **UPPERCASE**: Important checklists and reports (e.g., `DEPLOYMENT_CHECKLIST.md`)
- **lowercase**: Technical documentation (e.g., `design.md`, `prd.md`)
- **BAITMAN_prefix**: Service-specific technical guides
- **kebab-case**: Implementation guides (e.g., `neo4j-knowledge-graph.md`)

### Status Indicators
- ✅ **Complete** - Feature fully implemented and tested
- 🚧 **In Progress** - Feature under active development
- 📋 **Planned** - Feature in roadmap
- ⚠️ **Known Issue** - Issue documented with workaround

---

**Need something not listed here?** Check the [Main README](../README.md) or explore the repository structure at the project root.
