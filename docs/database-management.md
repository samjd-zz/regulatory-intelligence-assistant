# Database Management Strategy

## Overview
The Regulatory Intelligence Assistant uses a **dual-database architecture** combining PostgreSQL for relational data and Neo4j for graph relationships. Both databases are managed through MCP servers for seamless AI-assisted development.

## Database Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Application Layer                        │
│            (FastAPI Backend + React Frontend)            │
└───────────────┬─────────────────────┬───────────────────┘
                │                     │
        ┌───────▼────────┐    ┌──────▼──────────┐
        │   PostgreSQL   │    │      Neo4j      │
        │   (Port 5432)  │    │  (Port 7687)    │
        │                │    │                 │
        │  Structured    │    │  Knowledge      │
        │  Data & Meta   │    │  Graph          │
        └───────┬────────┘    └──────┬──────────┘
                │                     │
        ┌───────▼────────┐    ┌──────▼──────────┐
        │  Supabase MCP  │    │  Neo4j MCP      │
        │    Server      │    │   Server        │
        └────────────────┘    └─────────────────┘
```

## PostgreSQL - Structured Data

### Purpose
- **User Management**: Authentication, profiles, permissions
- **Metadata Storage**: Document metadata, search indexes, cache
- **Application State**: User queries, history, preferences
- **Structured Content**: Parsed regulation text, sections, amendments

### Connection Details
- **Host**: localhost
- **Port**: 5432
- **Database**: regulatory_db
- **User**: postgres
- **Password**: postgres

### Managed By
**Supabase MCP Server** (`github.com/alexander-zuev/supabase-mcp-server`)

Available tools:
- `get_schemas` - List all database schemas
- `get_tables` - List tables in a schema
- `get_table_schema` - Get table structure
- `execute_postgresql` - Execute SQL queries

### Schema Design
```sql
-- Users and Authentication
users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  role VARCHAR,
  created_at TIMESTAMP
)

-- Regulatory Documents
documents (
  id UUID PRIMARY KEY,
  title VARCHAR,
  jurisdiction VARCHAR,
  document_type VARCHAR,
  effective_date DATE,
  content_hash VARCHAR,
  created_at TIMESTAMP
)

-- Sections (for search and reference)
sections (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES documents(id),
  section_number VARCHAR,
  title VARCHAR,
  content TEXT,
  embedding VECTOR(1536),  -- For semantic search
  created_at TIMESTAMP
)

-- Search History
search_queries (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  query TEXT,
  results JSONB,
  created_at TIMESTAMP
)

-- Compliance Checks
compliance_checks (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  scenario JSONB,
  results JSONB,
  created_at TIMESTAMP
)
```

## Neo4j - Knowledge Graph

### Purpose
- **Regulatory Relationships**: Links between laws, sections, policies
- **Semantic Connections**: Cross-references, amendments, dependencies
- **Graph Traversal**: Find related regulations automatically
- **Contextual Memory**: Persistent knowledge across conversations

### Connection Details
- **Host**: localhost
- **Port**: 7687 (Bolt), 7474 (HTTP/Browser)
- **Database**: neo4j
- **User**: neo4j
- **Password**: password123

### Managed By
**Neo4j MCP Server** (`github.com/neo4j-contrib/mcp-neo4j`)

Available tools:
- `read_graph` - Read entire knowledge graph
- `search_nodes` - Search for specific entities
- `find_nodes` - Find nodes by name
- `create_entities` - Add new regulatory entities
- `create_relations` - Define relationships
- `add_observations` - Add details to entities

### Graph Schema
```cypher
// Node Types
(:Legislation {name, jurisdiction, year, citation})
(:Section {number, title, content_summary})
(:Regulation {name, authority, effective_date})
(:Policy {name, department, description})
(:Program {name, eligibility, benefits})
(:Situation {description, keywords})

// Relationship Types
(:Legislation)-[:HAS_SECTION]->(:Section)
(:Section)-[:REFERENCES]->(:Section)
(:Section)-[:AMENDED_BY]->(:Section)
(:Regulation)-[:IMPLEMENTS]->(:Legislation)
(:Regulation)-[:APPLIES_TO]->(:Program)
(:Section)-[:RELEVANT_FOR]->(:Situation)
```

## Using MCP Servers for Database Management

### PostgreSQL Operations (via Supabase MCP)

**Create Tables:**
```
Create a users table with id, email, role, and timestamps
```

**Query Data:**
```
Show me all documents from 2024 in the employment jurisdiction
```

**Analyze Schema:**
```
What tables exist in the regulatory_db database?
```

### Neo4j Operations (via Neo4j MCP)

**Create Entities:**
```
Add the Employment Insurance Act and its key sections to the knowledge graph
```

**Define Relationships:**
```
Create a relationship showing that Section 7 of the EI Act applies to 
temporary foreign workers
```

**Query Graph:**
```
Find all regulations that reference the Immigration Act
```

## Database Integration Workflow

### 1. Document Ingestion
```
User uploads regulation → 
  PostgreSQL: Store metadata, text, parse sections →
  Neo4j: Create entities, relationships, cross-references
```

### 2. Semantic Search
```
User searches → 
  PostgreSQL: Vector similarity search on embeddings →
  Neo4j: Graph traversal for related regulations →
  Combine results for comprehensive answer
```

### 3. Compliance Checking
```
User submits scenario →
  Neo4j: Find applicable regulations via graph →
  PostgreSQL: Retrieve full text and requirements →
  Analyze and report compliance status
```

### 4. Q&A with RAG
```
User asks question →
  PostgreSQL: Retrieve relevant document sections →
  Neo4j: Find related regulations and context →
  Gemini API: Generate answer with citations
```

## Best Practices

### When to Use PostgreSQL
✅ User authentication and authorization  
✅ Structured metadata and search indexes  
✅ Document content and embeddings  
✅ Application logs and analytics  
✅ Transactional data

### When to Use Neo4j
✅ Regulatory relationships and cross-references  
✅ Graph-based queries (find all related...)  
✅ Amendment tracking and version history  
✅ Complex eligibility chains  
✅ Contextual memory across sessions

### Data Consistency
- **Document IDs**: Use same UUID in both databases
- **Sync Strategy**: PostgreSQL is source of truth for content
- **Graph Updates**: Rebuild relationships when documents change
- **Backups**: Backup both databases together

## Migration Strategy

### Initial Setup (Empty Databases)
1. Use Supabase MCP to create PostgreSQL schema
2. Use Neo4j MCP to initialize knowledge graph
3. Ingest sample regulatory documents
4. Build initial relationships

### Adding New Regulations
1. Store in PostgreSQL with metadata
2. Create corresponding Neo4j entities
3. Extract and create relationships
4. Update search indexes

### Schema Evolution
1. PostgreSQL: Use migrations (Alembic)
2. Neo4j: Add new node/relationship types as needed
3. Test with MCP tools before deploying

## Monitoring and Maintenance

### PostgreSQL
```bash
# Check database size
docker exec regulatory-postgres psql -U postgres -d regulatory_db -c "\l+"

# View connections
docker exec regulatory-postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"

# Backup
docker exec regulatory-postgres pg_dump -U postgres regulatory_db > backup.sql
```

### Neo4j
```bash
# Check graph statistics
docker exec regulatory-neo4j cypher-shell -u neo4j -p password123 "CALL db.stats()"

# View node counts
docker exec regulatory-neo4j cypher-shell -u neo4j -p password123 "MATCH (n) RETURN labels(n), count(*)"

# Backup
docker exec regulatory-neo4j neo4j-admin dump --database=neo4j --to=/backups/neo4j-backup.dump
```

## Access Methods

### Via MCP Servers (AI-Assisted)
Use natural language with Cline to:
- Create tables and schemas
- Insert and query data
- Build knowledge graphs
- Analyze relationships

### Via Direct Connection (Application Code)
```python
# PostgreSQL
from sqlalchemy import create_engine
engine = create_engine('postgresql://postgres:postgres@localhost:5432/regulatory_db')

# Neo4j
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password123'))
```

### Via Admin Interfaces
- **PostgreSQL**: Use pgAdmin or psql CLI
- **Neo4j**: Use Neo4j Browser at http://localhost:7474

## Security Considerations

⚠️ **Current Setup (Development)**
- Default passwords (change for production!)
- No SSL/TLS encryption
- All services on localhost

🔒 **Production Checklist**
- [ ] Change all default passwords
- [ ] Enable SSL/TLS for database connections
- [ ] Configure firewall rules
- [ ] Set up database user roles and permissions
- [ ] Enable audit logging
- [ ] Configure backup automation
- [ ] Use secrets management (AWS Secrets Manager, etc.)

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if container is running
docker ps | grep regulatory-postgres

# View logs
docker logs regulatory-postgres

# Test connection
psql postgresql://postgres:postgres@localhost:5432/regulatory_db
```

### Neo4j Connection Issues
```bash
# Check if container is running
docker ps | grep regulatory-neo4j

# View logs
docker logs regulatory-neo4j

# Test connection
curl http://localhost:7474
```

### MCP Server Issues
1. Verify database containers are running
2. Check connection strings in cline_mcp_settings.json
3. Restart MCP servers through Cline settings
4. Check server logs in VSCode Output panel

## Next Steps

1. **Initialize Schemas**: Use Supabase MCP to create PostgreSQL tables
2. **Build Knowledge Graph**: Use Neo4j MCP to add initial entities
3. **Integrate with Backend**: Connect FastAPI to both databases
4. **Test Workflow**: Ingest a sample regulation end-to-end
