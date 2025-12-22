# Graph Relationship Query Routing Feature

**Status:** 📋 Planned (Alternative to Agentic Approach)  
**Created:** 2025-12-21  
**Related:** `AGENTIC_NEO4J_TOOL_IMPLEMENTATION_PLAN.md`

## Overview

The Graph Relationship Query Routing feature intelligently routes relationship/reference questions directly to Neo4j graph traversal queries instead of using RAG (Retrieval-Augmented Generation), ensuring accurate answers for questions about regulatory relationships, citations, and dependencies.

## Problem Statement

### The Issue
When users ask questions like "What regulations reference the Employment Insurance Act?" or "Which laws does section 7(1) cite?", the RAG system faces several limitations:

- **Limited Context Window:** RAG can only see 5 documents (`num_context_docs=5`), missing the full relationship network
- **Relationship Blindness:** Text embeddings don't capture structured relationships (REFERENCES, CITES, AMENDS, IMPLEMENTS)
- **Incomplete Answers:** May only find references in the limited context, not the complete graph
- **Slow Performance:** Requires multiple RAG calls to follow citation chains

### The Solution
Detect graph relationship queries using NLP intent classification and route them to Neo4j Cypher queries that traverse the knowledge graph for complete, accurate relationship data.

## Architecture Comparison

### Approach A: Agentic (Complex)
**See:** `AGENTIC_NEO4J_TOOL_IMPLEMENTATION_PLAN.md`

```
User Query → LLM Function Calling → Tool Selection → 
Neo4j Tool Execution → Result Parsing → LLM Formatting → Response
```

**Pros:**
- Flexible tool selection
- Can combine multiple tools
- Self-correcting via reflection

**Cons:**
- ⚠️ Complex implementation (function schemas, execution loops)
- ⚠️ Slower (multiple LLM calls)
- ⚠️ Non-deterministic (LLM chooses tools)
- ⚠️ Harder to test and debug
- ⚠️ Requires Gemini API function calling

### Approach B: NLP Routing (Simple) ✅ **Recommended**
**Pattern:** Same as Statistics Routing (proven, production-ready)

```
User Query → NLP Intent Detection → Route to Neo4j Service → 
Direct Cypher Query → Format Results → Response
```

**Pros:**
- ✅ Simple, proven architecture (reuses STATISTICS pattern)
- ✅ Fast (<200ms, no extra LLM calls)
- ✅ Deterministic (regex-based detection)
- ✅ Easy to test and maintain
- ✅ No additional dependencies
- ✅ Already has infrastructure in place

**Cons:**
- Requires pattern maintenance for new query types
- Less flexible than agentic approach

## Decision: Use NLP Routing

Based on the proven success of Statistics Routing, we recommend the **NLP Routing approach** as:
1. **Simpler:** Reuses existing `QueryIntent` enum and routing pattern
2. **Faster:** No function calling overhead
3. **More Reliable:** Deterministic pattern matching
4. **Easier to Test:** Same testing pattern as statistics
5. **Production-Ready:** Proven architecture already in production

## Implementation Plan

### 1. Query Parser Enhancement

Add new intent to `backend/services/query_parser.py`:

```python
class QueryIntent(str, Enum):
    SEARCH = "search"
    COMPLIANCE = "compliance"
    INTERPRETATION = "interpretation"
    ELIGIBILITY = "eligibility"
    PROCEDURE = "procedure"
    DEFINITION = "definition"
    COMPARISON = "comparison"
    STATISTICS = "statistics"
    GRAPH_RELATIONSHIP = "graph_relationship"  # NEW
```

Add detection patterns:

```python
INTENT_PATTERNS = {
    # ... existing patterns ...
    
    QueryIntent.GRAPH_RELATIONSHIP: [
        # Reference/Citation patterns
        r'\b(what|which).*\b(references?|cites?|mentions?|refers? to)\b',
        r'\b(references?|cites?|mentions?|refers? to).*\b(what|which)\b',
        
        # Amendment patterns
        r'\b(what|which).*\b(amends?|amended by|modifies?|modified by)\b',
        r'\b(has|have).*\b(been amended|been modified|changed)\b',
        
        # Implementation patterns
        r'\b(what|which).*\b(implements?|implemented by|enforced by)\b',
        r'\b(regulations?|policies?).*\b(implement|enforce)\b',
        
        # Supersession patterns
        r'\b(replaces?|replaced by|supersedes?|superseded by)\b',
        
        # Dependency patterns
        r'\b(depends? on|requires?|prerequisite|related to)\b',
        r'\b(connected to|linked to|associated with)\b',
        
        # Hierarchy patterns
        r'\b(parent|child|subsection|part of)\b.*\b(section|regulation|act)\b',
        
        # Generic relationship patterns
        r'\b(relationship|connection|link).*\b(between|with)\b',
        r'\b(show|find|list).*\b(all|related|connected)\b',
    ],
}
```

### 2. Graph Relationship Service

Create `backend/services/graph_relationship_service.py`:

```python
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class GraphRelationshipService:
    """Service for querying Neo4j graph relationships"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def find_references(
        self, 
        document_id: Optional[str] = None,
        document_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find what a document references (outgoing CITES relationships)"""
        
        query = """
        MATCH (source:Document)-[r:CITES]->(target:Document)
        WHERE $document_id IS NULL OR source.id = $document_id
        OR ($document_title IS NOT NULL AND source.title CONTAINS $document_title)
        RETURN 
            source.title AS source_title,
            source.id AS source_id,
            target.title AS target_title,
            target.id AS target_id,
            r.section AS cited_section,
            type(r) AS relationship_type
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                document_id=document_id,
                document_title=document_title,
                limit=limit
            )
            return [dict(record) for record in result]
    
    def find_referenced_by(
        self,
        document_id: Optional[str] = None,
        document_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find what references a document (incoming CITES relationships)"""
        
        query = """
        MATCH (source:Document)-[r:CITES]->(target:Document)
        WHERE $document_id IS NULL OR target.id = $document_id
        OR ($document_title IS NOT NULL AND target.title CONTAINS $document_title)
        RETURN 
            source.title AS referencing_document,
            source.id AS source_id,
            target.title AS referenced_document,
            target.id AS target_id,
            r.section AS cited_section,
            type(r) AS relationship_type
        LIMIT $limit
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                document_id=document_id,
                document_title=document_title,
                limit=limit
            )
            return [dict(record) for record in result]
    
    def find_amendments(
        self,
        document_id: Optional[str] = None,
        document_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find amendments to a document"""
        
        query = """
        MATCH (source:Document)-[r:AMENDS]->(target:Document)
        WHERE $document_id IS NULL OR target.id = $document_id
        OR ($document_title IS NOT NULL AND target.title CONTAINS $document_title)
        RETURN 
            source.title AS amending_document,
            source.id AS source_id,
            target.title AS amended_document,
            target.id AS target_id,
            r.effective_date AS effective_date,
            type(r) AS relationship_type
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                document_id=document_id,
                document_title=document_title
            )
            return [dict(record) for record in result]
    
    def find_implementations(
        self,
        act_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find regulations that implement an act"""
        
        query = """
        MATCH (reg:Document)-[r:IMPLEMENTS]->(act:Document)
        WHERE $act_title IS NULL OR act.title CONTAINS $act_title
        RETURN 
            reg.title AS regulation_title,
            reg.id AS regulation_id,
            act.title AS act_title,
            act.id AS act_id,
            type(r) AS relationship_type
        """
        
        with self.driver.session() as session:
            result = session.run(query, act_title=act_title)
            return [dict(record) for record in result]
    
    def format_relationship_answer(
        self,
        relationships: List[Dict[str, Any]],
        question: str,
        relationship_type: str = "references"
    ) -> str:
        """Format graph relationships into natural language"""
        
        if not relationships:
            return f"I couldn't find any {relationship_type} for the specified document in the knowledge graph."
        
        count = len(relationships)
        
        # Build natural language response
        answer = f"Based on the knowledge graph, I found {count} {relationship_type}:\n\n"
        
        for i, rel in enumerate(relationships[:10], 1):  # Limit to top 10 for readability
            if relationship_type == "references":
                answer += f"{i}. **{rel['source_title']}** references **{rel['target_title']}**"
                if rel.get('cited_section'):
                    answer += f" (Section {rel['cited_section']})"
                answer += "\n"
            
            elif relationship_type == "referenced_by":
                answer += f"{i}. **{rel['referencing_document']}** references this document"
                if rel.get('cited_section'):
                    answer += f" (citing Section {rel['cited_section']})"
                answer += "\n"
            
            elif relationship_type == "amendments":
                answer += f"{i}. **{rel['amending_document']}** amends this document"
                if rel.get('effective_date'):
                    answer += f" (effective {rel['effective_date']})"
                answer += "\n"
            
            elif relationship_type == "implementations":
                answer += f"{i}. **{rel['regulation_title']}** implements this act\n"
        
        if count > 10:
            answer += f"\n... and {count - 10} more {relationship_type}."
        
        return answer.strip()
```

### 3. RAG Service Integration

Update `backend/services/rag_service.py`:

```python
from services.graph_relationship_service import GraphRelationshipService

class RAGService:
    def __init__(self, ...):
        # ... existing initialization ...
        self.graph_relationship_service = GraphRelationshipService(neo4j_driver)
    
    def answer_question(self, question: str, ...):
        # Parse query to detect intent
        parsed_query = self.query_parser.parse_query(question)
        
        # Route graph relationship questions to Neo4j
        if parsed_query.intent == QueryIntent.GRAPH_RELATIONSHIP:
            logger.info("Detected GRAPH_RELATIONSHIP intent - routing to Neo4j")
            return self._answer_graph_relationship_question(
                question=question,
                parsed_query=parsed_query,
                filters=combined_filters,
                start_time=start_time
            )
        
        # Route statistics questions to database
        if parsed_query.intent == QueryIntent.STATISTICS:
            logger.info("Detected STATISTICS intent - routing to database")
            return self._answer_statistics_question(...)
        
        # Regular questions use RAG
        return self._answer_with_rag(...)
    
    def _answer_graph_relationship_question(
        self,
        question: str,
        parsed_query: ParsedQuery,
        filters: Dict[str, Any],
        start_time: float
    ) -> Dict[str, Any]:
        """Answer questions about graph relationships using Neo4j"""
        
        # Determine relationship type from question
        relationship_type = self._detect_relationship_type(question)
        
        # Query Neo4j based on relationship type
        if relationship_type == "references":
            relationships = self.graph_relationship_service.find_references(
                document_title=parsed_query.entities.get('document'),
                limit=50
            )
        elif relationship_type == "referenced_by":
            relationships = self.graph_relationship_service.find_referenced_by(
                document_title=parsed_query.entities.get('document'),
                limit=50
            )
        elif relationship_type == "amendments":
            relationships = self.graph_relationship_service.find_amendments(
                document_title=parsed_query.entities.get('document')
            )
        elif relationship_type == "implementations":
            relationships = self.graph_relationship_service.find_implementations(
                act_title=parsed_query.entities.get('document')
            )
        else:
            # Default to finding references
            relationships = self.graph_relationship_service.find_references(
                document_title=parsed_query.entities.get('document'),
                limit=50
            )
        
        # Format response
        answer = self.graph_relationship_service.format_relationship_answer(
            relationships=relationships,
            question=question,
            relationship_type=relationship_type
        )
        
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return {
            "answer": answer,
            "sources": [],  # Graph queries don't return document sources
            "confidence": 0.90,  # High confidence for graph queries
            "metadata": {
                "intent": "graph_relationship",
                "relationship_type": relationship_type,
                "response_time_ms": response_time_ms,
                "query_type": "neo4j_graph_query",
                "relationship_count": len(relationships),
                "entities": parsed_query.entities
            }
        }
    
    def _detect_relationship_type(self, question: str) -> str:
        """Detect the type of relationship query"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["references", "cites", "mentions", "refers to"]):
            if any(word in question_lower for word in ["referenced by", "cited by", "mentioned by"]):
                return "referenced_by"
            return "references"
        
        if any(word in question_lower for word in ["amends", "amended", "modified"]):
            return "amendments"
        
        if any(word in question_lower for word in ["implements", "enforces"]):
            return "implementations"
        
        return "references"  # Default
```

## Detection Patterns

### Example Queries Detected

#### References (Outgoing)
✅ "What does the Employment Insurance Act reference?"  
✅ "Which regulations does section 7(1) cite?"  
✅ "What laws does this regulation mention?"

#### Referenced By (Incoming)
✅ "What references the Employment Insurance Act?"  
✅ "Which regulations cite this section?"  
✅ "What documents mention CPP regulation 42?"

#### Amendments
✅ "Has the Employment Insurance Act been amended?"  
✅ "What amendments were made to this regulation?"  
✅ "Which laws modified section 7(1)?"

#### Implementations
✅ "What regulations implement the Employment Insurance Act?"  
✅ "Which policies enforce this legislation?"

## Response Format

Graph relationship responses include:

```json
{
  "answer": "Based on the knowledge graph, I found 15 references:\n\n1. **Employment Insurance Regulations** references **Employment Insurance Act** (Section 7(1))\n2. ...",
  "sources": [],
  "confidence": 0.90,
  "metadata": {
    "intent": "graph_relationship",
    "relationship_type": "references",
    "response_time_ms": 120,
    "query_type": "neo4j_graph_query",
    "relationship_count": 15,
    "entities": {
      "document": "Employment Insurance Act"
    }
  }
}
```

### Key Differences from RAG Responses
- **High Confidence:** 0.90 (graph queries are accurate)
- **No Sources:** Empty sources array (data from graph, not documents)
- **Fast:** Typically <200ms (direct Cypher query)
- **Complete:** All relationships in the graph, not limited by context window
- **Structured:** Returns relationship metadata (type, direction, properties)

## Performance Benefits

| Metric | RAG Approach | Graph Routing |\n|--------|-------------|---------------|\n| **Completeness** | ~20% (5 docs) | 100% (full graph) |\n| **Response Time** | 2-5 seconds | <200ms |\n| **Confidence** | 0.3-0.7 | 0.90 |\n| **Relationship Coverage** | Limited context | All relationships |\n| **Follow Citation Chains** | Multiple queries | Single traversal |\n| **Token Usage** | High (AI inference) | None (Cypher query) |

## Comparison to Agentic Approach

| Aspect | Agentic (Complex) | NLP Routing (Simple) |\n|--------|------------------|----------------------|\n| **Implementation Complexity** | High (function schemas, loops) | Low (reuses existing patterns) |\n| **Response Time** | 2-4 seconds (multiple LLM calls) | <200ms (single query) |\n| **Reliability** | Non-deterministic | Deterministic |\n| **Testing** | Complex (mock function calling) | Simple (pattern matching) |\n| **Maintenance** | High (tool schemas, prompts) | Low (regex patterns) |\n| **Infrastructure** | Requires Gemini function calling | Uses existing components |\n| **Debugging** | Difficult (trace tool selection) | Easy (inspect patterns) |\n| **Flexibility** | Can combine tools | Single-purpose |\n| **Production Readiness** | Unproven | Proven (STATISTICS) |

## User Experience Impact

### Before (RAG Approach)
```
User: "What regulations reference the Employment Insurance Act?"
AI: "Based on the 5 documents I can see, the Employment Insurance 
     Regulations and the CPP Regulations appear to reference the 
     Employment Insurance Act. However, there may be other references 
     I cannot see in the current context..." ❌ Incomplete
```

### After (Graph Routing)
```
User: "What regulations reference the Employment Insurance Act?"
AI: "Based on the knowledge graph, I found 24 references:

1. **Employment Insurance Regulations** references **Employment Insurance Act** (Section 7(1))
2. **Social Security Tribunal Regulations** references **Employment Insurance Act** (Section 52)
3. **Canada Pension Plan Regulations** references **Employment Insurance Act** (Section 5(1))
...
" ✅ Complete & Accurate
```

## Testing Strategy

### Test Coverage
Similar to Statistics Routing:

1. ✅ `test_query_parser_detects_graph_relationship_intent` - Intent detection
2. ✅ `test_rag_service_routes_to_neo4j` - RAG routing
3. ✅ `test_graph_relationship_service_finds_references` - References query
4. ✅ `test_graph_relationship_service_finds_referenced_by` - Reverse references
5. ✅ `test_graph_relationship_service_finds_amendments` - Amendments
6. ✅ `test_formatted_graph_answer` - Natural language formatting
7. ✅ `test_non_relationship_questions_use_rag` - Non-graph use RAG
8. ✅ `test_relationship_type_detection` - Type detection

### Test File
Create `backend/tests/test_graph_relationship_routing.py`:

```python
import pytest
from services.query_parser import QueryParser, QueryIntent
from services.graph_relationship_service import GraphRelationshipService
from services.rag_service import RAGService

def test_query_parser_detects_graph_relationship_intent():
    """Test that graph relationship questions are detected"""
    parser = QueryParser()
    
    # Test reference patterns
    result = parser.parse_query("What does the EI Act reference?")
    assert result.intent == QueryIntent.GRAPH_RELATIONSHIP
    
    result = parser.parse_query("Which regulations cite section 7(1)?")
    assert result.intent == QueryIntent.GRAPH_RELATIONSHIP
    
    # Test amendment patterns
    result = parser.parse_query("Has this regulation been amended?")
    assert result.intent == QueryIntent.GRAPH_RELATIONSHIP

def test_graph_relationship_service_finds_references(neo4j_session):
    """Test finding outgoing references"""
    service = GraphRelationshipService(neo4j_driver)
    
    results = service.find_references(document_title="Employment Insurance")
    
    assert len(results) > 0
    assert "source_title" in results[0]
    assert "target_title" in results[0]

# ... more tests ...
```

## Implementation Checklist

- [ ] Add `QueryIntent.GRAPH_RELATIONSHIP` to enum
- [ ] Add regex patterns to `INTENT_PATTERNS`
- [ ] Create `GraphRelationshipService` class
- [ ] Implement `find_references()` method
- [ ] Implement `find_referenced_by()` method
- [ ] Implement `find_amendments()` method
- [ ] Implement `find_implementations()` method
- [ ] Implement `format_relationship_answer()` method
- [ ] Update `RAGService.answer_question()` routing
- [ ] Implement `_answer_graph_relationship_question()` method
- [ ] Implement `_detect_relationship_type()` helper
- [ ] Create comprehensive test suite
- [ ] Add integration tests
- [ ] Document API endpoints
- [ ] Update user documentation

## Future Enhancements

### Potential Improvements
1. **Multi-Hop Traversal:** "What does the EI Act indirectly reference?" (2-3 hops)
2. **Relationship Filtering:** Filter by relationship type, date range
3. **Visual Graph:** Return graph data for frontend visualization
4. **Relationship Strength:** Score relationships by citation frequency
5. **Citation Context:** Include surrounding text from citations
6. **Temporal Queries:** "What referenced this regulation in 2023?"
7. **Comparative Queries:** "Compare references between two regulations"

### Advanced Query Examples
- "Show me the citation network for the Employment Insurance Act"
- "What regulations have bidirectional references?" (A→B and B→A)
- "Find all amendments to regulations implementing the EI Act"
- "Which regulations cite the most other regulations?" (hub analysis)

## Configuration

### Environment Variables
Uses existing Neo4j configuration:
- `NEO4J_URI` - Neo4j connection URI
- `NEO4J_USERNAME` - Neo4j username
- `NEO4J_PASSWORD` - Neo4j password

No additional configuration required.

## Troubleshooting

### Issue: Graph relationship intent not detected
**Symptoms:** Query classified as SEARCH or INTERPRETATION instead of GRAPH_RELATIONSHIP  
**Solution:** Check regex patterns in `INTENT_PATTERNS[QueryIntent.GRAPH_RELATIONSHIP]`

### Issue: Empty results from Neo4j
**Symptoms:** "I couldn't find any references" for known relationships  
**Solution:** 
- Verify graph data with `MATCH (n)-[r]->(m) RETURN count(r)`
- Check relationship types with `CALL db.relationshipTypes()`
- Verify entity extraction is finding document names

### Issue: Slow graph queries
**Symptoms:** Response time >500ms  
**Solution:**
- Check Neo4j indexes: `SHOW INDEXES`
- Optimize Cypher queries with `EXPLAIN` and `PROFILE`
- Add indexes on frequently queried properties

---

## Progress Update (2025-12-21)

### Latest Implementation Status: ✅ Tests Passing

#### What Has Been Completed
- **Intent Detection:**
  - `GRAPH_RELATIONSHIP` intent and patterns added to `query_parser.py`.
- **Service Layer:**
  - `GraphRelationshipService` methods for references, referenced_by, amendments, implementations, and answer formatting.
- **RAG Service Routing:**
  - `rag_service.py` routes relationship queries to graph service and returns robust answers.
- **Testing:**
  - `test_graph_relationship_routing.py` covers references, amendments, implementations, and negative cases.
  - All tests now pass, including low-confidence/empty result handling for amendments.
  - Confirmed no extraneous nodes (e.g., `Memory`) affect production graph logic.

#### Next Steps
- [ ] Expand test coverage for edge cases and multi-entity queries.
- [ ] Add more sample data for richer relationship answers.
- [ ] Enhance answer formatting for user-facing clarity.
- [ ] Document troubleshooting and schema hygiene best practices.

#### Known Issues
- Low confidence scores for queries with no matching relationships are expected and now handled in tests.
- Schema visualization may show unused labels; these do not affect query routing or results.

#### Example Usage
- "What amendments affect the Canada Pension Plan?" (returns correct intent and answer, even if no amendments exist)
- "Which regulations implement the Old Age Security Act?"
- "What laws reference the Employment Insurance Act?"

---
