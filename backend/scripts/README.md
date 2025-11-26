# Neo4j Knowledge Graph Scripts

This directory contains scripts for initializing, populating, and managing the Neo4j knowledge graph.

## Prerequisites

1. **Neo4j Running**: Ensure Neo4j is running via Docker:

   ```bash
   docker compose up -d neo4j
   ```

   > **Note**: The project uses a custom Neo4j Docker image (`backend/neo4j/Dockerfile`) with pre-installed APOC and Graph Data Science plugins. The container handles restarts gracefully.

2. **Environment Variables**: Copy `.env.example` to `.env` and configure:

   ```bash
   cp .env.example .env
   ```

   Verify these settings:

   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=password123
   ```

3. **Python Dependencies**: Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Scripts Overview

### 1. `init_graph.cypher`

Cypher script defining the graph schema (constraints, indexes, full-text search).

**Purpose:** Sets up the foundational schema for the knowledge graph.

**Contains:**

- Unique constraints on all node IDs
- Performance indexes on frequently queried properties
- Full-text search indexes for legislation and sections
- Documentation of node and relationship types

### 2. `init_neo4j.py`

Python script that initializes the Neo4j database with schema and sample data.

**Usage:**

```bash
cd backend
python scripts/init_neo4j.py
```

**What it does:**

- Executes the Cypher schema from `init_graph.cypher`
- Creates 4 sample legislation documents
- Creates sections for each legislation
- Sets up regulations, programs, and situations
- Establishes relationships between entities
- Displays a summary of created nodes

**Expected Output:**

```
============================================================
Neo4j Knowledge Graph Initialization
============================================================

Initializing Neo4j schema...
✓ Schema initialization complete

Populating sample data...
✓ Created: Employment Insurance Act
✓ Created: Canada Pension Plan
✓ Created: Old Age Security Act
✓ Created: Immigration and Refugee Protection Act
...
```

### 3. `seed_graph_data.py`

Comprehensive data seeding script with 15+ regulations.

**Usage:**

```bash
cd backend
python scripts/seed_graph_data.py
```

**What it does:**

- Creates 15+ federal legislation documents covering:
  - Employment & Labor (EI Act, Labour Code, Employment Equity)
  - Pension & Retirement (CPP, OAS)
  - Immigration & Citizenship (IRPA, Citizenship Act)
  - Health & Social Services (Canada Health Act)
  - Human Rights & Accessibility
  - Student Assistance
  - Family Benefits (Canada Child Benefit)
  - Disability Benefits
  - Privacy & Data Protection
- Creates sections for key legislation
- Establishes regulations implementing legislation
- Creates 5 government programs
- Creates 5 real-world situations
- Links sections to relevant situations
- Creates cross-references between sections

**Expected Output:**

```
============================================================
Neo4j Knowledge Graph - Comprehensive Data Seeding
============================================================

✓ Created: Employment Insurance Act
✓ Created: Canada Pension Plan
✓ Created: Old Age Security Act
...
✓ Created program: Employment Insurance Regular Benefits
...
✓ Created situation: Temporary foreign worker seeking employment benefits
...

Graph Statistics
============================================================
Legislation created: 15
Regulations created: 2
Sections created: 12
Programs created: 5
Situations created: 5
```

### 4. `verify_graph.py`

Verification and diagnostic script for the knowledge graph.

**Usage:**

```bash
cd backend
python scripts/verify_graph.py
```

**What it does:**

- Tests Neo4j connectivity
- Displays schema information (constraints and indexes)
- Shows node counts by type
- Shows relationship counts by type
- Displays sample data from each node type
- Shows example relationships
- Provides useful Cypher queries for exploration

**Expected Output:**

```
======================================================================
                Neo4j Knowledge Graph Verification
======================================================================

1. Verifying Neo4j Connectivity
============================================================
✓ Successfully connected to Neo4j

2. Verifying Schema (Constraints & Indexes)
============================================================
Constraints:
  ✓ legislation_id: UNIQUENESS
  ✓ section_id: UNIQUENESS
  ...

3. Verifying Graph Data
============================================================
Node Counts by Label:
  Legislation: 15
  Program: 5
  Regulation: 2
  Section: 12
  Situation: 5
...
```

## Typical Workflow

### Initial Setup (First Time)

```bash
# 1. Start Neo4j
docker compose up -d neo4j

# 2. Wait for Neo4j to be ready (check logs)
docker compose logs -f neo4j

# 3. Initialize schema and create sample data
cd backend
python scripts/init_neo4j.py

# 4. Verify the setup
python scripts/verify_graph.py
```

### Adding More Data

```bash
# Run the comprehensive seeding script
cd backend
python scripts/seed_graph_data.py

# Verify the data
python scripts/verify_graph.py
```

### Resetting the Database

If you need to start fresh:

```bash
# Option 1: Clear all data via Neo4j Browser
# Navigate to http://localhost:7474 and run:
# MATCH (n) DETACH DELETE n

# Option 2: Stop and remove Neo4j container/volume
docker compose down
docker volume rm regulatory-intelligence-assistant_neo4j_data
docker compose up -d neo4j

# Then re-initialize
cd backend
python scripts/init_neo4j.py
```

## Exploring the Graph

### Neo4j Browser

1. Open http://localhost:7474
2. Login with:
   - Username: `neo4j`
   - Password: `password123`

### Useful Cypher Queries

**View all nodes (limited):**

```cypher
MATCH (n) RETURN n LIMIT 50
```

**View legislation with sections:**

```cypher
MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
RETURN l, s
LIMIT 25
```

**View regulations implementing legislation:**

```cypher
MATCH (r:Regulation)-[:IMPLEMENTS]->(l:Legislation)
RETURN r, l
```

**Find sections relevant for a situation:**

```cypher
MATCH (s:Section)-[r:RELEVANT_FOR]->(sit:Situation)
WHERE sit.description CONTAINS 'retirement'
RETURN s, r, sit
```

**Search legislation by title:**

```cypher
MATCH (l:Legislation)
WHERE l.title CONTAINS 'Employment'
RETURN l
```

**Get graph statistics:**

```cypher
// Node counts
MATCH (n)
RETURN labels(n)[0] as NodeType, count(*) as Count
ORDER BY Count DESC

// Relationship counts
MATCH ()-[r]->()
RETURN type(r) as RelationType, count(*) as Count
ORDER BY Count DESC
```

## Troubleshooting

### "Module not found" errors

```bash
# Ensure you're running from the backend directory
cd backend
python scripts/init_neo4j.py

# Or use absolute imports from project root
cd ..
python -m backend.scripts.init_neo4j
```

### "Connection refused" errors

```bash
# Check if Neo4j is running
docker compose ps

# Check Neo4j logs
docker compose logs neo4j

# Restart Neo4j (safe - handles restarts gracefully)
docker compose restart neo4j
```

### "Authentication failed" errors

```bash
# Verify credentials in .env file
cat .env | grep NEO4J

# Reset Neo4j password via Docker (WARNING: deletes all data)
docker compose down
docker volume rm regulatory-intelligence-assistant_neo4j_data
docker compose up -d neo4j
# Wait 30 seconds, then try again
```

## Next Steps

After setting up the knowledge graph:

1. **Integrate with API**: Use the graph service in FastAPI endpoints
2. **Add More Data**: Extend `seed_graph_data.py` with additional regulations
3. **Build Query Endpoints**: Create API endpoints for graph traversal
4. **Add Graph Algorithms**: Use Neo4j GDS for path finding, centrality, etc.
5. **Implement Search**: Build full-text search using Neo4j's indexes

## Related Documentation

- [Neo4j Schema Documentation](../../docs/dev/neo4j-schema.md)
- [Neo4j Knowledge Graph Overview](../../docs/dev/neo4j-knowledge-graph.md)
- [Graph Service API](../services/graph_service.py)
- [Neo4j Client Utilities](../utils/neo4j_client.py)
