# Knowledge Graph Population Tasks

This directory contains scripts for populating the Neo4j knowledge graph with regulatory documents.

## Overview

The graph population pipeline:
1. Reads processed documents from PostgreSQL
2. Extracts entities (legislation, sections, programs, situations)
3. Creates nodes in Neo4j
4. Builds relationships between nodes
5. Links related documents

## Quick Start

### 1. Setup Neo4j Constraints (First Time Only)

```bash
cd backend
python tasks/populate_graph.py --setup-only
```

### 2. Create Sample Documents and Populate Graph

```bash
# Create 50 sample documents and populate graph
python tasks/populate_graph.py --create-samples 50 --limit 50
```

### 3. Populate from Existing Documents

```bash
# Populate from all processed documents
python tasks/populate_graph.py

# Populate only first 100 documents
python tasks/populate_graph.py --limit 100

# Populate only legislation
python tasks/populate_graph.py --types legislation

# Populate legislation and regulations
python tasks/populate_graph.py --types legislation regulation
```

### 4. Clear and Repopulate

```bash
# Clear existing graph and repopulate (DESTRUCTIVE!)
python tasks/populate_graph.py --clear --create-samples 100
```

## Command Line Options

- `--clear`: Clear existing graph before populating (requires confirmation)
- `--limit N`: Process maximum N documents
- `--types TYPE1 TYPE2`: Filter by document types (legislation, regulation, policy, guideline, directive)
- `--create-samples N`: Create N sample documents before populating
- `--setup-only`: Only setup constraints and indexes, don't populate

## Graph Schema

### Node Types Created

1. **Legislation** - Primary legislative documents
   - Properties: id, title, jurisdiction, authority, effective_date, status, act_number
   
2. **Regulation** - Regulatory provisions
   - Properties: id, title, authority, effective_date, status
   
3. **Policy** - Government policies and guidelines
   - Properties: id, title, department, version, effective_date
   
4. **Section** - Individual sections of documents
   - Properties: id, section_number, title, content, level
   
5. **Program** - Government programs (auto-extracted)
   - Properties: id, name, department, description
   
6. **Situation** - Applicable scenarios (auto-extracted)
   - Properties: id, description, tags

### Relationship Types Created

1. **HAS_SECTION**: Legislation/Regulation → Section
   - Properties: order
   
2. **PART_OF**: Section → Section (parent-child hierarchy)
   - Properties: order
   
3. **REFERENCES**: Section → Section (cross-references)
   - Properties: citation_text, context
   
4. **IMPLEMENTS**: Regulation → Legislation
   - Properties: description
   
5. **INTERPRETS**: Policy → Legislation
   - Properties: description
   
6. **APPLIES_TO**: Regulation → Program
   - Properties: description
   
7. **RELEVANT_FOR**: Section → Situation
   - Properties: relevance_score, description
   
8. **SUPERSEDES**: Legislation → Legislation (newer supersedes older)
   - Properties: effective_date

## Entity Extraction

The system automatically extracts:

### Programs
Detected from patterns like:
- "employment insurance program"
- "old age security benefits"
- "canada pension plan benefits"
- "workers' compensation program"

### Situations
Extracted from conditional clauses:
- "if you are unemployed..."
- "where a person has..."
- "in the case of retirement..."
- "when an individual is disabled..."

### Tags
Auto-tagged with keywords:
- employment, disability, retirement
- maternity, parental, sickness
- temporary_worker, caregiver

## Examples

### Example 1: Basic Population

```bash
# Create 50 sample documents and populate
python tasks/populate_graph.py --create-samples 50
```

Output:
```
INFO - Creating 50 sample documents...
INFO - ✓ Created 50 sample documents
INFO - Parsing documents to create sections...
INFO - ✓ Sections created
INFO - Starting graph population from PostgreSQL...
INFO - Found 50 documents to process
INFO - Processing document 1/50: Employment Insurance Act (Version 1)
INFO -   ✓ Created 8 nodes, 12 relationships
...
INFO - GRAPH POPULATION SUMMARY
INFO - Total documents processed: 50
INFO - Successful: 50
INFO - Failed: 0
INFO - Total nodes created: 425
INFO - Total relationships created: 680
```

### Example 2: Incremental Update

```bash
# Process only new unprocessed documents
python tasks/populate_graph.py --limit 10
```

### Example 3: Type-Specific Population

```bash
# Process only legislation documents
python tasks/populate_graph.py --types legislation --limit 25
```

### Example 4: Full Reset

```bash
# Clear everything and start fresh with 100 documents
python tasks/populate_graph.py --clear --create-samples 100
```

## Verification

After population, verify the graph:

```bash
# Check graph statistics
python scripts/verify_graph.py
```

Or query Neo4j directly:

```cypher
// Count nodes by type
MATCH (n)
RETURN labels(n) as type, count(n) as count
ORDER BY count DESC

// Count relationships by type
MATCH ()-[r]->()
RETURN type(r) as relationship, count(r) as count
ORDER BY count DESC

// Find legislation with most sections
MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
RETURN l.title, count(s) as section_count
ORDER BY section_count DESC
LIMIT 10
```

## Performance

- **Small dataset (50 docs)**: ~30 seconds
- **Medium dataset (100-500 docs)**: 2-10 minutes
- **Large dataset (1000+ docs)**: 20+ minutes

Performance tips:
- Use `--limit` to process in batches
- Ensure Neo4j has sufficient memory (4GB+ recommended)
- Run during off-peak hours for large imports

## Troubleshooting

### Neo4j Connection Error

```
ERROR - Failed to connect to Neo4j
```

**Solution**: Verify Neo4j is running and credentials are correct in `.env`:
```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### Constraint Already Exists

```
WARNING - Constraint/index may already exist
```

**Solution**: This is normal. The script checks if constraints exist before creating them.

### Memory Errors

```
ERROR - Out of memory
```

**Solution**: 
- Reduce batch size with `--limit`
- Increase Neo4j heap size in neo4j.conf:
  ```
  dbms.memory.heap.initial_size=2g
  dbms.memory.heap.max_size=4g
  ```

## Integration

### Use in FastAPI Routes

```python
from services.graph_builder import GraphBuilder
from utils.neo4j_client import get_neo4j_client

@router.post("/documents/upload")
async def upload_document(...):
    # After document parsing
    neo4j = get_neo4j_client()
    builder = GraphBuilder(db, neo4j)
    builder.build_document_graph(document.id)
```

### Batch Processing

```python
from tasks.populate_graph import populate_from_postgresql

# Process all unprocessed documents
stats = populate_from_postgresql(db, neo4j, limit=100)
print(f"Created {stats['total_nodes']} nodes")
```

## Architecture

```
┌─────────────────────┐
│   PostgreSQL DB     │
│  (Source Documents) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Graph Builder     │
│  - Extract entities │
│  - Create nodes     │
│  - Build relations  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Neo4j Graph DB    │
│  - Legislation      │
│  - Sections         │
│  - Programs         │
│  - Situations       │
└─────────────────────┘
```

## Next Steps

After populating the graph:

1. **Query the graph** using Neo4j Browser (http://localhost:7474)
2. **Build search APIs** that leverage graph relationships
3. **Create visualizations** of regulatory connections
4. **Implement compliance checking** using graph paths
5. **Add ML-based entity extraction** for better accuracy

## Files

- `populate_graph.py` - Main population script
- `../services/graph_builder.py` - Graph construction logic
- `../utils/neo4j_client.py` - Neo4j connection client
- `../scripts/verify_graph.py` - Graph verification script
