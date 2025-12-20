# Elasticsearch Node Type Implementation

## Overview
Updated Elasticsearch indexing to support the distinction between **Legislation** (Acts/Lois) and **Regulation** (SOR/DORS) document types, aligning with the Neo4j knowledge graph node classification.

## Date
2025-01-XX

## Changes Made

### 1. Elasticsearch Mappings Update
**File:** `backend/config/elasticsearch_mappings.json`

Added new `node_type` field to distinguish between Legislation and Regulation nodes:

```json
"node_type": {
  "type": "keyword",
  "fields": {
    "raw": {
      "type": "text"
    }
  }
}
```

**Purpose:** Enable filtering and classification by legal document category (Legislation vs Regulation).

### 2. Data Pipeline Updates
**File:** `backend/ingestion/data_pipeline.py`

#### Added Helper Method
```python
def _determine_node_type(self, title: str) -> str:
    """
    Determine if a regulation should be classified as Legislation or Regulation.
    Uses the same logic as graph_builder.py to ensure consistency.
    """
    title_lower = title.lower()
    
    # Acts and Lois (French for laws) are considered Legislation
    if ' act' in title_lower or title_lower.startswith('act ') or title_lower.endswith(' act'):
        return 'Legislation'
    if ' loi' in title_lower or title_lower.startswith('loi ') or title_lower.endswith(' loi'):
        return 'Legislation'
    
    # Everything else is a Regulation (rules, regulations, etc.)
    return 'Regulation'
```

#### Updated Indexing Logic
- Modified `_index_in_elasticsearch()` to determine and include `node_type` for each document
- Both regulation-level and section-level documents now include the `node_type` field
- Sections inherit the `node_type` from their parent regulation

**Changes:**
- Line ~545: Added `node_type = self._determine_node_type(regulation.title)`
- Line ~553: Added `'node_type': node_type` to regulation document
- Line ~591: Added `'node_type': node_type` to section document (inherited)

### 3. Search Service Updates
**File:** `backend/services/search_service.py`

Added `node_type` filter support in `_build_filters()` method:

```python
# Node type filter (Legislation vs Regulation)
if 'node_type' in filters:
    filter_clauses.append({"term": {"node_type": filters['node_type']}})
```

**Purpose:** Enable API queries to filter by `node_type=Legislation` or `node_type=Regulation`.

### 4. Re-indexing Script Updates
**File:** `backend/scripts/reindex_elasticsearch.py`

Updated to include `node_type` when re-indexing existing data:

1. Added `determine_node_type()` helper function (same logic as data pipeline)
2. Modified regulation indexing to include `'node_type': node_type`
3. Modified section indexing to inherit parent's `node_type`

**Purpose:** Ensure all existing PostgreSQL data can be re-indexed with proper node types.

## Classification Logic

The node type is determined by examining the document title:

| Title Pattern | Node Type | Examples |
|--------------|-----------|----------|
| Contains " act", starts with "act ", or ends with " act" | **Legislation** | "Employment Insurance Act", "Canada Labour Code" |
| Contains " loi", starts with "loi ", or ends with " loi" | **Legislation** | "Loi sur l'assurance-emploi" |
| All other titles | **Regulation** | "SOR/96-445", "Employment Insurance Regulations" |

This logic is **consistent** across:
- `services/graph_builder.py` - Neo4j node creation
- `ingestion/data_pipeline.py` - Elasticsearch indexing during ingestion
- `scripts/reindex_elasticsearch.py` - Elasticsearch re-indexing

## Usage

### Filtering by Node Type in Search API

```python
# Search only Legislation documents (Acts/Lois)
results = search_service.hybrid_search(
    query="employment insurance benefits",
    filters={"node_type": "Legislation"}
)

# Search only Regulation documents (SOR/DORS)
results = search_service.hybrid_search(
    query="immigration application process",
    filters={"node_type": "Regulation"}
)

# Search both (no filter)
results = search_service.hybrid_search(
    query="pension eligibility"
)
```

### API Query Examples

```bash
# Search only Acts
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "employment insurance",
    "filters": {"node_type": "Legislation"}
  }'

# Search only Regulations
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "immigration regulations",
    "filters": {"node_type": "Regulation"}
  }'
```

## Re-indexing Existing Data

After these changes, you **must re-index** existing Elasticsearch data to populate the `node_type` field:

```bash
cd backend
python scripts/reindex_elasticsearch.py
```

This will:
1. Recreate the Elasticsearch index with updated mappings
2. Re-index all regulations from PostgreSQL
3. Calculate and include `node_type` for each document
4. Index all sections with inherited `node_type`

**Expected Output:**
```
Starting re-indexing process...
Creating/recreating Elasticsearch index with proper mappings...
Index created successfully with custom mappings
Found 1827 regulations to index
Progress: 100/1827 regulations indexed (15,123 sections)
...
Re-indexing complete!
Indexed 1827 regulations
Indexed 277,027 sections
Total documents: 278,854
```

## Expected Data Distribution

Based on current database analysis:

| Node Type | Count | Percentage |
|-----------|-------|-----------|
| **Legislation** | ~1,804 | 98.7% |
| **Regulation** | ~23 | 1.3% |

**Note:** Currently we have mostly Acts because we haven't downloaded SOR/DORS regulations yet. After downloading regulations from the separate endpoint, the distribution will shift to include thousands of Regulation documents.

## Benefits

1. **Consistency:** Elasticsearch classification now matches Neo4j graph structure
2. **Filtering:** Users can search specifically for Acts vs Regulations
3. **Analytics:** Can track which type of document is most relevant for queries
4. **Future-proof:** Ready for when we ingest SOR/DORS regulation data
5. **Alignment:** Maintains same classification logic across all systems

## Related Documentation

- [Missing Document Types Analysis](./MISSING_DOCUMENT_TYPES_ANALYSIS.md) - Why we need this distinction
- [Knowledge Graph Architecture](../docs/design/KNOWLEDGE_GRAPH_ARCHITECTURE.md) - Neo4j node types
- [Real Data Ingestion Guide](../docs/REAL_DATA_INGESTION_GUIDE.md) - Full ingestion process

## Next Steps

1. ✅ Update Elasticsearch mappings (completed)
2. ✅ Update data pipeline indexing (completed)
3. ✅ Update re-indexing script (completed)
4. ⏳ Run re-indexing on existing data
5. ⏳ Download SOR/DORS regulations
6. ⏳ Ingest regulation XML files
7. ⏳ Verify node_type distribution matches expectations

## Testing

After re-indexing, verify the implementation:

```python
# Test 1: Check that documents have node_type
from services.search_service import SearchService
search = SearchService()

# Search all documents
results = search.hybrid_search("canada", size=5)
for hit in results['hits']:
    print(f"{hit['source']['title']}: {hit['source'].get('node_type', 'MISSING')}")

# Test 2: Filter by Legislation
leg_results = search.hybrid_search("insurance", filters={"node_type": "Legislation"})
print(f"Found {len(leg_results['hits'])} Legislation documents")

# Test 3: Filter by Regulation
reg_results = search.hybrid_search("insurance", filters={"node_type": "Regulation"})
print(f"Found {len(reg_results['hits'])} Regulation documents")
```

**Expected:** All documents should have a `node_type` field, and filtering should work correctly.
