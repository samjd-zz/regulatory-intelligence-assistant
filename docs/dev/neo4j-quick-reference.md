# Neo4j Knowledge Graph - Quick Reference

## Setup & Initialization

```bash
# Start Neo4j (uses custom Docker image with APOC + GDS plugins pre-installed)
docker compose up -d neo4j

# Initialize with comprehensive data (15+ regulations)
cd backend
python scripts/seed_graph_data.py

# Verify setup
python scripts/verify_graph.py
```

> **Note**: The project uses a custom Neo4j 5.15 Docker image located at `backend/neo4j/Dockerfile` with pre-installed APOC and Graph Data Science plugins. The container handles restarts gracefully without data loss.

## Access Neo4j Browser

- URL: http://localhost:7474
- Username: `neo4j`
- Password: `password123`

## Python API Usage

### Import and Initialize

```python
from backend.services.graph_service import get_graph_service
from backend.utils.neo4j_client import get_neo4j_client

service = get_graph_service()
client = get_neo4j_client()
```

### Create Legislation

```python
from datetime import date

legislation = service.create_legislation(
    title="Example Act",
    jurisdiction="federal",
    authority="Parliament of Canada",
    effective_date=date(2024, 1, 1),
    status="active",
    act_number="S.C. 2024, c. 1"
)
```

### Create Section

```python
section = service.create_section(
    section_number="7(1)",
    title="Eligibility",
    content="Requirements for eligibility...",
    level=0
)

# Link to legislation
service.link_section_to_legislation(
    section['id'],
    legislation['id'],
    order=0
)
```

### Create Program

```python
program = service.create_program(
    name="Benefit Program",
    department="Service Canada",
    description="Program description",
    eligibility_criteria=["Criterion 1", "Criterion 2"]
)
```

### Query Examples

```python
# Find legislation by title
results = service.find_legislation_by_title("Employment")

# Get legislation with all sections
data = service.get_legislation_with_sections(legislation_id)

# Get graph statistics
stats = service.get_graph_overview()
print(stats['nodes'])  # Node counts by type
print(stats['relationships'])  # Relationship counts
```

## Essential Cypher Queries

### View All Data (Limited)

```cypher
MATCH (n) RETURN n LIMIT 50
```

### Node Statistics

```cypher
MATCH (n)
RETURN labels(n)[0] as Type, count(*) as Count
ORDER BY Count DESC
```

### Find Legislation

```cypher
MATCH (l:Legislation)
WHERE l.title CONTAINS 'Employment'
RETURN l
```

### Legislation with Sections

```cypher
MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
WHERE l.title = 'Employment Insurance Act'
RETURN l, s
ORDER BY s.order
```

### Regulations Implementing Legislation

```cypher
MATCH (r:Regulation)-[:IMPLEMENTS]->(l:Legislation)
RETURN r.title, l.title
```

### Sections Relevant for Situation

```cypher
MATCH (s:Section)-[r:RELEVANT_FOR]->(sit:Situation)
WHERE sit.description CONTAINS 'retirement'
RETURN s.section_number, s.title, r.relevance_score
ORDER BY r.relevance_score DESC
```

### Full-Text Search

```cypher
CALL db.index.fulltext.queryNodes('legislation_fulltext', 'employment insurance')
YIELD node, score
RETURN node.title, score
ORDER BY score DESC
LIMIT 10
```

### Cross-References

```cypher
MATCH (s1:Section)-[r:REFERENCES]->(s2:Section)
RETURN s1.section_number, s2.section_number, r.citation_text
```

### Graph Paths

```cypher
MATCH path = (l:Legislation)-[*1..3]-(p:Program)
RETURN path
LIMIT 10
```

## Common Tasks

### Clear All Data

```cypher
MATCH (n) DETACH DELETE n
```

### Delete Specific Node Type

```cypher
MATCH (s:Situation) DETACH DELETE s
```

### Update Node Property

```cypher
MATCH (l:Legislation {id: $id})
SET l.status = 'amended'
RETURN l
```

### Count Relationships

```cypher
MATCH ()-[r]->()
RETURN type(r) as Type, count(*) as Count
ORDER BY Count DESC
```

## Troubleshooting

### Check Connection

```python
from backend.utils.neo4j_client import get_neo4j_client
client = get_neo4j_client()
print(client.verify_connectivity())  # Should return True
```

### View Constraints

```cypher
SHOW CONSTRAINTS
```

### View Indexes

```cypher
SHOW INDEXES
```

### Check Neo4j Status

```bash
docker compose ps neo4j
docker compose logs neo4j
```

## File Locations

- **Schema Definition**: `backend/scripts/init_graph.cypher`
- **Neo4j Client**: `backend/utils/neo4j_client.py`
- **Graph Service**: `backend/services/graph_service.py`
- **Initialization**: `backend/scripts/init_neo4j.py`
- **Data Seeding**: `backend/scripts/seed_graph_data.py`
- **Verification**: `backend/scripts/verify_graph.py`
- **Docker Configuration**: `backend/neo4j/Dockerfile`
- **Entrypoint Wrapper**: `backend/neo4j/docker-entrypoint-wrapper.sh`
- **Documentation**: `docs/dev/neo4j-schema.md`

## Node Types Quick Reference

| Type          | Description             | Key Properties              |
| ------------- | ----------------------- | --------------------------- |
| `Legislation` | Acts, Statutes          | title, jurisdiction, status |
| `Section`     | Sections of legislation | section_number, content     |
| `Regulation`  | Implementing rules      | title, authority            |
| `Policy`      | Government policies     | title, department           |
| `Program`     | Government services     | name, eligibility_criteria  |
| `Situation`   | Use case scenarios      | description, tags           |

## Relationship Types Quick Reference

| Type           | Direction                 | Description           |
| -------------- | ------------------------- | --------------------- |
| `HAS_SECTION`  | Legislation → Section     | Contains section      |
| `REFERENCES`   | Section → Section         | Cross-reference       |
| `IMPLEMENTS`   | Regulation → Legislation  | Implements law        |
| `APPLIES_TO`   | Regulation → Program      | Applies to program    |
| `RELEVANT_FOR` | Section → Situation       | Relevant for scenario |
| `AMENDED_BY`   | Section → Section         | Amendment             |
| `SUPERSEDES`   | Legislation → Legislation | Replacement           |

## Environment Variables

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123
```

## Next Steps

1. Explore data in Neo4j Browser
2. Try example queries
3. Build API endpoints using `graph_service`
4. Add more regulations with `seed_graph_data.py`
5. Integrate with frontend application
