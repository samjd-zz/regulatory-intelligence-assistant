# Knowledge Graph Implementation

## Overview

The Knowledge Graph subsystem creates a Neo4j-based graph database that models relationships between legislation, regulations, policies, sections, programs, and real-world situations. This enables advanced querying, relationship discovery, and compliance checking.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                       │
│  ┌────────────┐  ┌──────────┐  ┌────────┐  ┌──────────────┐ │
│  │ Documents  │  │ Sections │  │ Cross  │  │   Metadata   │ │
│  │   Table    │  │  Table   │  │  Refs  │  │    Tables    │ │
│  └────────────┘  └──────────┘  └────────┘  └──────────────┘ │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
         ┌──────────────────────────┐
         │    Graph Builder         │
         │  ┌────────────────────┐  │
         │  │ Entity Extraction  │  │
         │  │ - Programs         │  │
         │  │ - Situations       │  │
         │  │ - Relationships    │  │
         │  └────────────────────┘  │
         └──────────┬───────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│                     Neo4j Knowledge Graph                     │
│                                                               │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │Legislation├───►│ Section  ├───►│Situation │              │
│  └────┬─────┘    └────┬─────┘    └──────────┘              │
│       │               │                                      │
│       │               │                                      │
│  ┌────▼─────┐    ┌───▼──────┐                              │
│  │Regulation│    │ Program  │                              │
│  └──────────┘    └──────────┘                              │
│                                                               │
│  Relationships: HAS_SECTION, REFERENCES, IMPLEMENTS,         │
│                 APPLIES_TO, RELEVANT_FOR, SUPERSEDES         │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. Graph Builder (`services/graph_builder.py`)

Core service that builds the knowledge graph from parsed documents.

**Key Methods:**

- `build_document_graph(document_id)`: Build graph for single document
- `build_all_documents(limit)`: Build graphs for multiple documents
- `create_inter_document_relationships()`: Link related documents
- `_extract_programs()`: Extract program mentions from text
- `_extract_situations()`: Extract applicable situations

**Features:**

- **Automatic Entity Extraction**: Identifies programs and situations using regex patterns
- **Relationship Building**: Creates typed relationships between entities
- **Hierarchy Construction**: Builds parent-child relationships for sections
- **Cross-Reference Mapping**: Links sections that reference each other

### 2. Population Script (`tasks/populate_graph.py`)

Command-line tool for batch graph population.

**Usage:**

```bash
# Setup constraints and indexes
python3 tasks/populate_graph.py --setup-only

# Create sample documents and populate
python3 tasks/populate_graph.py --create-samples 50

# Populate from existing documents
python3 tasks/populate_graph.py --limit 100

# Clear and repopulate
python3 tasks/populate_graph.py --clear --create-samples 100
```

**Options:**

- `--clear`: Clear existing graph (requires confirmation)
- `--limit N`: Process max N documents
- `--types TYPE1 TYPE2`: Filter by document types
- `--create-samples N`: Create N sample documents
- `--setup-only`: Setup constraints/indexes only

### 3. Graph API Routes (`routes/graph.py`)

REST API endpoints for graph operations.

**Endpoints:**

```
POST /graph/build
  - Build graph for multiple documents (background task)
  - Request: { document_ids?, document_types?, limit? }
  - Response: { status, message, stats }

POST /graph/build/{document_id}
  - Build graph for single document (synchronous)
  - Response: { status, message, stats }

GET /graph/stats
  - Get graph statistics
  - Response: { nodes, relationships, summary }

GET /graph/search?query=...&limit=10
  - Full-text search across graph
  - Response: { query, results, count }

GET /graph/legislation/{id}/related?relationship_type=...
  - Find related legislation/regulations
  - Response: { legislation_id, related_items, count }

GET /graph/section/{id}/references?max_depth=2
  - Get section cross-references
  - Response: { section_id, references, count }

DELETE /graph/clear?confirm=true
  - Clear entire graph (DESTRUCTIVE)
  - Response: { status, message }
```

### 4. Neo4j Client (`utils/neo4j_client.py`)

Low-level Neo4j connection and query utilities.

**Key Methods:**

- `connect()`: Establish Neo4j connection
- `execute_query()`: Run read query
- `execute_write()`: Run write transaction
- `create_node()`: Create single node
- `create_relationship()`: Create relationship
- `find_node()`: Find node by properties
- `find_related_nodes()`: Traverse relationships

## Node Types

### Legislation
Primary legislative documents (Acts, Statutes)

```python
{
  "id": "uuid",
  "title": "Employment Insurance Act",
  "jurisdiction": "federal",
  "authority": "Parliament of Canada",
  "effective_date": "1996-06-30",
  "status": "active",
  "act_number": "S.C. 1996, c. 23",
  "full_text": "...",
  "metadata": {...}
}
```

### Section
Individual sections of documents

```python
{
  "id": "uuid",
  "section_number": "7(1)",
  "title": "Eligibility for benefits",
  "content": "Subject to this Part...",
  "level": 0
}
```

### Regulation
Regulatory provisions

```python
{
  "id": "uuid",
  "title": "Employment Insurance Regulations",
  "authority": "Governor in Council",
  "effective_date": "1996-07-30",
  "status": "active"
}
```

### Program
Government programs (auto-extracted)

```python
{
  "id": "uuid",
  "name": "Employment Insurance Regular Benefits",
  "department": "Employment and Social Development Canada",
  "description": "Provides temporary financial assistance"
}
```

### Situation
Applicable scenarios (auto-extracted)

```python
{
  "id": "uuid",
  "description": "Temporary foreign worker seeking benefits",
  "tags": ["temporary_worker", "employment_insurance"]
}
```

## Relationship Types

### HAS_SECTION
Connects legislation to its sections

```cypher
(Legislation)-[:HAS_SECTION {order: 0}]->(Section)
```

### PART_OF
Parent-child hierarchy for sections

```cypher
(Section)-[:PART_OF {order: 0}]->(Section)
```

### REFERENCES
Cross-references between sections

```cypher
(Section)-[:REFERENCES {
  citation_text: "See Section 7(2)",
  context: "Eligibility determination"
}]->(Section)
```

### IMPLEMENTS
Regulation implements legislation

```cypher
(Regulation)-[:IMPLEMENTS {
  description: "Implements EI Act provisions"
}]->(Legislation)
```

### APPLIES_TO
Regulation applies to program

```cypher
(Regulation)-[:APPLIES_TO]->(Program)
```

### RELEVANT_FOR
Section is relevant for situation

```cypher
(Section)-[:RELEVANT_FOR {
  relevance_score: 0.95,
  description: "Eligibility for temporary workers"
}]->(Situation)
```

### SUPERSEDES
One legislation supersedes another

```cypher
(Legislation)-[:SUPERSEDES {
  effective_date: "2020-01-01"
}]->(Legislation)
```

## Entity Extraction

### Program Extraction

Patterns detected:
```regex
- "employment insurance (program|benefits)"
- "old age security (program|benefits)"
- "canada pension plan (benefits|program)"
- "workers' compensation (program|benefits)"
- "disability benefits program"
- "parental benefits program"
```

Example matches:
- "Employment Insurance benefits"
- "Old Age Security program"
- "Canada Pension Plan benefits"

### Situation Extraction

Patterns detected:
```regex
- "if (you|a person) (is|are|has|have) ..."
- "where (a|an|the) ..."
- "in the case of ..."
- "when (a|an|the) ..."
```

Example matches:
- "if you are unemployed and available for work"
- "where a person has been dismissed"
- "in the case of retirement before age 65"

### Automatic Tagging

Tags extracted from situation text:
- `employment`: unemployed, job, work
- `disability`: disabled, impairment
- `retirement`: retired, pension
- `maternity`: pregnancy, pregnant
- `parental`: parent, child care
- `sickness`: sick, illness
- `temporary_worker`: temporary, foreign worker
- `caregiver`: caring for

## Usage Examples

### Example 1: Build Graph via API

```bash
# Build graph for specific document
curl -X POST http://localhost:8000/graph/build/d2685b3b-60a2-4369-a025-9f92ed92db67

# Build graph for all legislation (background)
curl -X POST http://localhost:8000/graph/build \
  -H "Content-Type: application/json" \
  -d '{"document_types": ["legislation"], "limit": 50}'

# Get graph statistics
curl http://localhost:8000/graph/stats
```

### Example 2: Query Graph Relationships

```bash
# Find legislation related to a specific document
curl http://localhost:8000/graph/legislation/uuid-123/related

# Get section cross-references
curl http://localhost:8000/graph/section/uuid-456/references?max_depth=3

# Search graph
curl "http://localhost:8000/graph/search?query=employment+insurance&limit=20"
```

### Example 3: Direct Cypher Queries

```cypher
// Find all programs related to employment insurance
MATCH (l:Legislation {title: "Employment Insurance Act"})
  -[:HAS_SECTION]->(s:Section)
  -[:RELEVANT_FOR]->(sit:Situation)
RETURN l, s, sit
LIMIT 50

// Find regulations implementing specific legislation
MATCH (r:Regulation)-[:IMPLEMENTS]->(l:Legislation)
WHERE l.jurisdiction = 'federal'
RETURN r.title, l.title

// Find most referenced sections
MATCH (s:Section)<-[r:REFERENCES]-()
RETURN s.section_number, s.title, count(r) as ref_count
ORDER BY ref_count DESC
LIMIT 10

// Find situations relevant to disability
MATCH (s:Section)-[rel:RELEVANT_FOR]->(sit:Situation)
WHERE 'disability' IN sit.tags
RETURN s, rel, sit
```

### Example 4: Compliance Path Finding

```cypher
// Find path from situation to applicable programs
MATCH path = (sit:Situation)<-[:RELEVANT_FOR]-(s:Section)
  <-[:HAS_SECTION]-(l:Legislation)
  <-[:IMPLEMENTS]-(r:Regulation)
  -[:APPLIES_TO]->(p:Program)
WHERE sit.description CONTAINS 'unemployed'
RETURN path
LIMIT 5
```

## Performance Optimization

### Constraints (Required for Performance)

```cypher
CREATE CONSTRAINT legislation_id IF NOT EXISTS
FOR (l:Legislation) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT section_id IF NOT EXISTS
FOR (s:Section) REQUIRE s.id IS UNIQUE;
```

### Indexes

```cypher
CREATE INDEX legislation_title IF NOT EXISTS
FOR (l:Legislation) ON (l.title);

CREATE INDEX section_number IF NOT EXISTS
FOR (s:Section) ON (s.section_number);
```

### Full-Text Indexes

```cypher
CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
FOR (l:Legislation) ON EACH [l.title, l.full_text];

CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
FOR (s:Section) ON EACH [s.title, s.content];
```

## Configuration

### Environment Variables

```bash
# Neo4j connection
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# PostgreSQL connection
DATABASE_URL=postgresql://user:pass@localhost/regulatory_db
```

### Neo4j Memory Settings

For large graphs (1000+ documents), increase heap size:

```conf
# neo4j.conf
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=4g
dbms.memory.pagecache.size=1g
```

## Monitoring

### Graph Statistics

```bash
# Via API
curl http://localhost:8000/graph/stats

# Via CLI
python3 scripts/verify_graph.py
```

### Neo4j Browser

Access at http://localhost:7474

```cypher
// Count all nodes
MATCH (n) RETURN count(n)

// Count all relationships
MATCH ()-[r]->() RETURN count(r)

// Node distribution
MATCH (n)
RETURN labels(n) as type, count(n) as count
ORDER BY count DESC
```

## Troubleshooting

### Issue: Graph population fails with connection error

**Solution**: Verify Neo4j is running and credentials are correct

```bash
# Check Neo4j status
docker ps | grep neo4j

# Test connection
python3 -c "from utils.neo4j_client import Neo4jClient; c = Neo4jClient(); print(c.verify_connectivity())"
```

### Issue: Slow queries

**Solution**: Ensure constraints and indexes are created

```bash
python3 tasks/populate_graph.py --setup-only
```

### Issue: Memory errors during population

**Solution**: Process in smaller batches

```bash
python3 tasks/populate_graph.py --limit 50
```

## Future Enhancements

- [ ] Machine learning-based entity extraction
- [ ] Automated relationship inference
- [ ] Graph embeddings for similarity search
- [ ] Time-based graph versioning
- [ ] Visual graph explorer UI
- [ ] Integration with compliance checker
- [ ] Advanced path-finding algorithms
- [ ] Graph-based recommendation system

## Files

- `services/graph_builder.py` - Graph construction logic
- `tasks/populate_graph.py` - Batch population script
- `routes/graph.py` - REST API endpoints
- `utils/neo4j_client.py` - Neo4j connection client
- `docs/dev/neo4j-schema.md` - Detailed schema documentation
