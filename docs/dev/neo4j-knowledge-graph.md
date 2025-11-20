# Neo4j Knowledge Graph Documentation

## Overview

The Regulatory Intelligence Assistant uses a Neo4j knowledge graph to model complex relationships between legislation, regulations, policies, programs, and applicable situations. This graph-based approach enables powerful traversal queries and relationship discovery.

## Graph Schema

### Node Types

#### 1. Legislation
Primary legislative documents such as Acts and Statutes.

**Properties:**
- `id` (String, UUID): Unique identifier
- `title` (String): Full title of the legislation
- `act_number` (String): Official act number (e.g., "S.C. 1996, c. 23")
- `jurisdiction` (String): Jurisdiction level (federal, provincial, municipal)
- `authority` (String): Issuing authority (e.g., "Parliament of Canada")
- `effective_date` (Date): Date when legislation became effective
- `status` (String): Current status (active, amended, repealed)
- `full_text` (String): Complete text of the legislation
- `metadata` (JSON String): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Indexes:**
- Unique constraint on `id`
- Index on `title`
- Index on `jurisdiction`
- Index on `effective_date`
- Index on `status`
- Full-text search index on `title` and `full_text`

#### 2. Section
Individual sections and subsections within legislation.

**Properties:**
- `id` (String, UUID): Unique identifier
- `section_number` (String): Section designation (e.g., "7(1)(a)")
- `title` (String): Section title/heading
- `content` (String): Full text of the section
- `level` (Integer): Nesting level (0 for top-level sections)
- `metadata` (JSON String): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Indexes:**
- Unique constraint on `id`
- Index on `section_number`
- Index on `title`
- Full-text search index on `title` and `content`

#### 3. Regulation
Regulatory provisions and administrative rules.

**Properties:**
- `id` (String, UUID): Unique identifier
- `title` (String): Regulation title
- `authority` (String): Regulatory authority
- `effective_date` (Date): Date of effect
- `status` (String): Current status
- `full_text` (String): Complete regulation text
- `metadata` (JSON String): Additional metadata (e.g., regulation number)
- `created_at` (DateTime): Node creation timestamp

**Indexes:**
- Unique constraint on `id`
- Index on `title`
- Index on `authority`
- Full-text search index on `title` and `full_text`

#### 4. Policy
Government policies and operational guidelines.

**Properties:**
- `id` (String, UUID): Unique identifier
- `title` (String): Policy title
- `department` (String): Responsible department
- `version` (String): Policy version number
- `effective_date` (Date): Date of effect
- `metadata` (JSON String): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Indexes:**
- Unique constraint on `id`
- Index on `title`
- Index on `department`

#### 5. Program
Government programs and public services.

**Properties:**
- `id` (String, UUID): Unique identifier
- `name` (String): Program name
- `department` (String): Administering department
- `description` (String): Program description
- `eligibility_criteria` (List[String]): Eligibility requirements
- `metadata` (JSON String): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Indexes:**
- Unique constraint on `id`
- Index on `name`
- Index on `department`

#### 6. Situation
Real-world scenarios and use cases.

**Properties:**
- `id` (String, UUID): Unique identifier
- `description` (String): Situation description
- `tags` (List[String]): Categorization tags
- `metadata` (JSON String): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Indexes:**
- Unique constraint on `id`
- Index on `description`

### Relationship Types

#### 1. HAS_SECTION
Links legislation to its constituent sections.

**Direction:** Legislation → Section

**Properties:**
- `order` (Integer): Sequential order within legislation
- `created_at` (DateTime): Relationship creation timestamp

**Example Query:**
```cypher
MATCH (l:Legislation {title: "Employment Insurance Act"})-[:HAS_SECTION]->(s:Section)
RETURN l, s
ORDER BY s.order
```

#### 2. REFERENCES
Cross-references between sections.

**Direction:** Section → Section

**Properties:**
- `citation_text` (String): Citation text
- `context` (String): Context of the reference
- `created_at` (DateTime): Relationship creation timestamp

**Example Query:**
```cypher
MATCH (s1:Section)-[r:REFERENCES]->(s2:Section)
RETURN s1.section_number, r.citation_text, s2.section_number
```

#### 3. AMENDED_BY
Tracks amendments to sections.

**Direction:** Section → Section

**Properties:**
- `effective_date` (Date): Amendment effective date
- `description` (String): Nature of amendment
- `created_at` (DateTime): Relationship creation timestamp

#### 4. IMPLEMENTS
Links regulations to the legislation they implement.

**Direction:** Regulation → Legislation

**Properties:**
- `description` (String): Implementation details
- `created_at` (DateTime): Relationship creation timestamp

**Example Query:**
```cypher
MATCH (r:Regulation)-[:IMPLEMENTS]->(l:Legislation)
RETURN r.title, l.title
```

#### 5. INTERPRETS
Links policies to legislation they interpret.

**Direction:** Policy → Legislation

**Properties:**
- `description` (String): Interpretation details
- `created_at` (DateTime): Relationship creation timestamp

#### 6. APPLIES_TO
Links regulations to programs they govern.

**Direction:** Regulation → Program

**Properties:**
- `description` (String): Application details
- `created_at` (DateTime): Relationship creation timestamp

**Example Query:**
```cypher
MATCH (r:Regulation)-[:APPLIES_TO]->(p:Program)
RETURN r.title, p.name, p.description
```

#### 7. RELEVANT_FOR
Links sections to applicable situations.

**Direction:** Section → Situation

**Properties:**
- `relevance_score` (Float): Relevance score (0.0-1.0)
- `description` (String): Relevance explanation
- `created_at` (DateTime): Relationship creation timestamp

**Example Query:**
```cypher
MATCH (s:Section)-[r:RELEVANT_FOR]->(sit:Situation)
WHERE r.relevance_score > 0.9
RETURN s.title, sit.description, r.relevance_score
ORDER BY r.relevance_score DESC
```

#### 8. SUPERSEDES
Tracks replacement of legislation.

**Direction:** Legislation → Legislation

**Properties:**
- `effective_date` (Date): Supersession date
- `description` (String): Supersession details
- `created_at` (DateTime): Relationship creation timestamp

#### 9. PART_OF
Hierarchical parent-child relationships between sections.

**Direction:** Section → Section

**Properties:**
- `order` (Integer): Position within parent
- `created_at` (DateTime): Relationship creation timestamp

## Sample Data

The graph includes sample Canadian federal legislation:

### Legislation
1. **Employment Insurance Act** (S.C. 1996, c. 23)
   - 2 sections on eligibility and qualification
   
2. **Canada Pension Plan** (R.S.C. 1985, c. C-8)
   - 1 section on retirement pension
   
3. **Old Age Security Act** (R.S.C. 1985, c. O-9)
   - 1 section on eligibility
   
4. **Immigration and Refugee Protection Act** (S.C. 2001, c. 27)

### Regulations
1. **Employment Insurance Regulations** (SOR/96-332)
   - Implements EI Act
   - Applies to EI Benefits program

### Programs
1. **Employment Insurance Benefits** (ESDC)
2. **Canada Pension Plan Retirement Pension** (Service Canada)
3. **Old Age Security Pension** (Service Canada)

### Situations
1. **Temporary foreign worker seeking employment benefits**
   - Relevant sections from EI Act
   
2. **Planning for retirement benefits**
   - Relevant sections from CPP and OAS Acts

## Common Query Patterns

### 1. Find All Sections of a Legislation
```cypher
MATCH (l:Legislation {title: "Employment Insurance Act"})-[:HAS_SECTION]->(s:Section)
RETURN s
ORDER BY s.section_number
```

### 2. Find Related Regulations
```cypher
MATCH (l:Legislation {title: "Employment Insurance Act"})<-[:IMPLEMENTS]-(r:Regulation)
RETURN r
```

### 3. Find Cross-Referenced Sections
```cypher
MATCH (s:Section {section_number: "7(1)"})-[:REFERENCES*1..2]-(related:Section)
RETURN related
```

### 4. Find Applicable Programs
```cypher
MATCH (l:Legislation {title: "Employment Insurance Act"})<-[:IMPLEMENTS]-(r:Regulation)-[:APPLIES_TO]->(p:Program)
RETURN p
```

### 5. Find Relevant Sections for a Situation
```cypher
MATCH (sit:Situation {description: "Temporary foreign worker seeking employment benefits"})<-[r:RELEVANT_FOR]-(s:Section)
RETURN s, r.relevance_score
ORDER BY r.relevance_score DESC
```

### 6. Full-Text Search
```cypher
CALL db.index.fulltext.queryNodes('legislation_fulltext', 'employment insurance')
YIELD node, score
RETURN node.title, score
ORDER BY score DESC
LIMIT 10
```

### 7. Graph Traversal - Find Related Legislation
```cypher
MATCH path = (l1:Legislation {title: "Employment Insurance Act"})-[:IMPLEMENTS|HAS_SECTION|REFERENCES*1..3]-(l2:Legislation)
WHERE l1 <> l2
RETURN DISTINCT l2.title
```

## Python API Usage

### Using the Neo4j Client
```python
from backend.utils.neo4j_client import get_neo4j_client

client = get_neo4j_client()

# Execute a query
results = client.execute_query(
    "MATCH (l:Legislation) RETURN l.title as title LIMIT 5"
)

for result in results:
    print(result['title'])
```

### Using the Graph Service
```python
from backend.services.graph_service import get_graph_service

service = get_graph_service()

# Create legislation
legislation = service.create_legislation(
    title="New Act",
    jurisdiction="federal",
    authority="Parliament of Canada",
    effective_date=date(2024, 1, 1),
    status="active"
)

# Find legislation
results = service.find_legislation_by_title("Employment")

# Get graph overview
stats = service.get_graph_overview()
print(stats['nodes'])  # Node counts by type
print(stats['relationships'])  # Relationship counts by type
```

## Visualization

### Neo4j Browser
Access the Neo4j Browser at http://localhost:7474

**Useful visualization queries:**

1. **View all nodes:**
   ```cypher
   MATCH (n) RETURN n LIMIT 50
   ```

2. **View legislation with sections:**
   ```cypher
   MATCH (l:Legislation)-[r:HAS_SECTION]->(s:Section)
   RETURN l, r, s
   LIMIT 20
   ```

3. **View complete regulatory framework:**
   ```cypher
   MATCH (l:Legislation)-[:IMPLEMENTS]-(r:Regulation)-[:APPLIES_TO]->(p:Program)
   RETURN l, r, p
   ```

## Performance Considerations

1. **Indexes**: All key properties are indexed for fast lookups
2. **Constraints**: Unique constraints ensure data integrity
3. **Connection Pooling**: Client uses connection pooling for efficiency
4. **Batch Operations**: Use batch methods for bulk inserts
5. **Query Optimization**: Use EXPLAIN and PROFILE for query tuning

## Maintenance

### Backup
```bash
# Create backup
docker exec regulatory-neo4j neo4j-admin database dump neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump

# Restore backup
docker exec regulatory-neo4j neo4j-admin database load neo4j --from=/backups/neo4j-20240101.dump
```

### Clear All Data
```cypher
MATCH (n) DETACH DELETE n
```

### Reinitialize
```bash
python backend/scripts/init_neo4j.py
```

### Verify Data
```bash
python backend/scripts/verify_graph.py
```

## Next Steps

1. **Expand Sample Data**: Add more Canadian legislation
2. **Build Search API**: RESTful endpoints for graph queries
3. **Implement RAG**: Use graph context with Gemini API
4. **Add Versioning**: Track legislative amendments over time
5. **Create Admin UI**: Web interface for graph management
6. **Performance Tuning**: Optimize queries for production scale

## Resources

- **Neo4j Documentation**: https://neo4j.com/docs/
- **Cypher Reference**: https://neo4j.com/docs/cypher-manual/current/
- **Python Driver**: https://neo4j.com/docs/python-manual/current/
- **Graph Data Science**: https://neo4j.com/docs/graph-data-science/current/
