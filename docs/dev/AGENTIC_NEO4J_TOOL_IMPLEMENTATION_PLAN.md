# Agentic Neo4j Search Tool Implementation Plan

## Overview

This document outlines the plan to expose Neo4j graph search as a **function calling tool** that the AI can invoke intelligently during RAG conversations.

**Approach:** Agentic - The AI analyzes each query and decides whether graph-based search would provide better results than the standard 5-tier flow.

## Current State

### Existing Architecture
- **5-Tier RAG Search Flow:**
  1. Tier 1: Optimized Elasticsearch
  2. Tier 2: Relaxed Elasticsearch with query expansion
  3. Tier 3: Neo4j graph traversal (automatic fallback)
  4. Tier 4: PostgreSQL full-text search
  5. Tier 5: Metadata-only search

- **Search Orchestration:** Fully automatic - RAG service tries each tier sequentially until sufficient documents are found

- **Gemini Client:** No function calling support currently

### Why Add Agentic Tool Use?

1. **Intelligent Search Strategy Selection:** Let the AI recognize queries that benefit from graph relationships (e.g., "What regulations reference Section 7 of the Employment Insurance Act?")

2. **Avoid Unnecessary Fallback:** Don't wait for Tier 1-2 to fail before using graph search if the query clearly needs relationship traversal

3. **Explainability:** The AI can explain why it chose graph search ("I'm using the regulatory knowledge graph to find all documents that reference...")

4. **Cost Optimization:** Skip expensive sequential tier attempts when graph search is the obvious choice

## Technical Implementation Plan

### 1. Add Function Calling Support to Gemini Client

**File:** `backend/services/gemini_client.py`

**Changes:**
- Add `tools` parameter support to `generate_content()` and `generate_with_context()`
- Implement function calling loop with tool execution
- Handle tool call responses and integrate results back into generation

**New Methods:**
```python
def generate_with_tools(
    self,
    query: str,
    context: str,
    tools: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    max_tool_iterations: int = 3,
    temperature: float = 0.7
) -> Tuple[str, List[Dict[str, Any]], Optional[GeminiError]]:
    """
    Generate content with function calling support.
    
    Returns:
        Tuple of (final_answer, tool_calls_made, error)
    """
    pass

def _execute_tool_call(
    self,
    tool_name: str,
    tool_arguments: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a tool call and return results."""
    pass
```

**Gemini Function Calling API Reference:**
- Uses `genai.protos.Tool` and `genai.protos.FunctionDeclaration`
- Model returns `function_call` in response when it wants to invoke a tool
- We execute the tool, then send results back to continue generation

### 2. Define Neo4j Search Tool Schema

**File:** `backend/services/tool_schemas.py` (new)

**Purpose:** Define the function schemas that the AI can call

```python
from typing import List, Dict, Any

NEO4J_GRAPH_SEARCH_TOOL = {
    "name": "search_regulatory_knowledge_graph",
    "description": """
        Search the regulatory knowledge graph using semantic similarity and relationship traversal.
        
        Use this tool when:
        - The query asks about relationships between regulations (e.g., "What acts reference X?")
        - The query needs amendment history or legislative evolution
        - The query asks about regulatory hierarchies or dependencies
        - Standard text search may miss relationship-based information
        
        Do NOT use this tool when:
        - A simple text search would suffice
        - The query is about specific content within a single regulation
        - The query can be answered with direct text matching
    """,
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant regulations in the knowledge graph"
            },
            "search_type": {
                "type": "string",
                "enum": ["semantic", "traversal", "hybrid"],
                "description": "Type of graph search: 'semantic' for similarity-based, 'traversal' for relationship-based, 'hybrid' for both"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of documents to return (default: 10)",
                "default": 10
            },
            "language": {
                "type": "string",
                "enum": ["en", "fr"],
                "description": "Language filter for documents (default: 'en')",
                "default": "en"
            }
        },
        "required": ["query", "search_type"]
    }
}

# Future tools can be added here:
# ELASTICSEARCH_SEARCH_TOOL = {...}
# COMPLIANCE_CHECK_TOOL = {...}
# STATISTICS_QUERY_TOOL = {...}
```

### 3. Implement Tool Handler Functions

**File:** `backend/services/tool_handlers.py` (new)

**Purpose:** Execute tool calls and return formatted results

```python
from typing import Dict, Any, List
from services.graph_service import GraphService

class ToolHandler:
    """Handles execution of function calling tools."""
    
    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service
        
    def handle_neo4j_search(
        self,
        query: str,
        search_type: str,
        max_results: int = 10,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Execute Neo4j graph search and return formatted results.
        
        Returns:
            {
                "success": bool,
                "documents": List[Dict],
                "count": int,
                "search_metadata": Dict
            }
        """
        try:
            if search_type == "semantic":
                results = self.graph_service.semantic_search_for_rag(
                    query=query,
                    limit=max_results,
                    language=language
                )
            elif search_type == "traversal":
                results = self.graph_service.find_related_documents_by_traversal(
                    seed_query=query,
                    max_depth=2,
                    limit=max_results
                )
            elif search_type == "hybrid":
                semantic = self.graph_service.semantic_search_for_rag(
                    query=query,
                    limit=max_results // 2,
                    language=language
                )
                traversal = self.graph_service.find_related_documents_by_traversal(
                    seed_query=query,
                    max_depth=2,
                    limit=max_results // 2
                )
                # Combine and deduplicate
                seen_ids = set()
                results = []
                for doc in semantic + traversal:
                    if doc['id'] not in seen_ids:
                        seen_ids.add(doc['id'])
                        results.append(doc)
            
            return {
                "success": True,
                "documents": results,
                "count": len(results),
                "search_metadata": {
                    "search_type": search_type,
                    "query": query,
                    "language": language
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "count": 0
            }
    
    def execute_tool(
        self,
        tool_name: str,
        tool_arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Route tool calls to appropriate handlers."""
        if tool_name == "search_regulatory_knowledge_graph":
            return self.handle_neo4j_search(**tool_arguments)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
```

### 4. Update RAG Service for Agentic Flow

**File:** `backend/services/rag_service.py`

**Changes:**

1. **Add new method:** `answer_question_with_tools()` - agentic version
2. **Keep existing method:** `answer_question()` - automatic 5-tier flow (for backward compatibility)
3. **Add configuration:** Environment variable to enable/disable agentic mode

```python
def answer_question_with_tools(
    self,
    question: str,
    filters: Optional[Dict] = None,
    use_cache: bool = True,
    temperature: float = 0.3,
    max_tokens: int = 8192
) -> RAGAnswer:
    """
    Answer a question using agentic tool calling approach.
    
    The AI can choose to:
    1. Use standard retrieval (5-tier flow)
    2. Invoke Neo4j graph search tool
    3. Request additional information
    
    This provides more intelligent search strategy selection.
    """
    start_time = datetime.now()
    
    # Check cache
    if use_cache:
        cached_answer = self._get_cached_answer(question)
        if cached_answer:
            return cached_answer
    
    # Detect language
    detected_lang = self._detect_language(question)
    combined_filters = filters or {}
    combined_filters['language'] = detected_lang
    
    # Define available tools
    tools = [NEO4J_GRAPH_SEARCH_TOOL]
    
    # Enhanced system prompt with tool usage guidance
    tool_enhanced_prompt = self.LEGAL_SYSTEM_PROMPT + """
    
    ## AVAILABLE TOOLS
    
    You have access to specialized search tools:
    
    1. **search_regulatory_knowledge_graph**: Use the regulatory knowledge graph
       - Best for: Queries about relationships, references, amendments, hierarchies
       - Example: "What regulations implement the Employment Insurance Act?"
       - Example: "Show me all acts that reference Section 7"
       
    ## TOOL USAGE GUIDELINES
    
    - Analyze the query to determine if graph search would provide better results
    - If the query is about relationships or cross-references, use the graph tool
    - If standard text search would suffice, I'll use the default retrieval
    - You can invoke tools multiple times if needed for comprehensive answers
    - Always cite sources regardless of search method used
    """
    
    # Initial context (empty for agentic approach - let AI decide what to search)
    initial_context = ""
    
    # Generate with tools
    answer_text, tool_calls, error = self.gemini_client.generate_with_tools(
        query=question,
        context=initial_context,
        tools=tools,
        system_prompt=tool_enhanced_prompt,
        max_tool_iterations=3,
        temperature=temperature
    )
    
    # Handle errors
    if error:
        return self._build_error_answer(question, error, start_time)
    
    # Extract citations and calculate confidence
    # ... (rest of existing logic)
    
    # Build RAG answer with tool metadata
    rag_answer = RAGAnswer(
        question=question,
        answer=answer_text,
        citations=citations,
        confidence_score=confidence,
        source_documents=context_docs,
        intent=intent,
        processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
        metadata={
            "agentic_mode": True,
            "tool_calls": [
                {
                    "tool": call["tool_name"],
                    "arguments": call["arguments"],
                    "result_count": call.get("result_count", 0)
                }
                for call in tool_calls
            ],
            "tools_available": [tool["name"] for tool in tools]
        }
    )
    
    return rag_answer
```

### 5. Update System Prompt

**File:** `backend/prompts/CANADIAN_LEGAL_RAG_AGENT_STRICT_RAG_ENFORCEMENT_GEMINI.md`

**Add Section:**

```markdown
## TOOL USAGE (AGENTIC MODE)

When tools are available, you may invoke them to retrieve information:

### Available Tools

1. **search_regulatory_knowledge_graph**
   - Searches the regulatory knowledge graph using relationships
   - Use when the query involves cross-references, amendments, or regulatory hierarchies
   - Provides relationship-based discovery beyond text matching

### When to Use Tools

**Use graph search when:**
- Query asks "what references X?" or "what implements Y?"
- Query needs amendment history or legislative evolution
- Query involves regulatory dependencies or hierarchies

**Use standard retrieval when:**
- Query is about specific content within a regulation
- Simple text search would suffice
- Query is straightforward eligibility or definition question

### Tool Usage Rules

1. You may invoke tools multiple times
2. All tool results must be cited like any other source
3. Maintain strict RAG enforcement regardless of search method
4. Explain which tool you used and why (briefly)
5. If tools return no results, state this clearly
```

### 6. Add API Endpoint

**File:** `backend/routes/rag.py`

**Add New Endpoint:**

```python
@router.post("/ask/agentic")
async def ask_question_agentic(
    question: str = Body(...),
    filters: Optional[Dict[str, Any]] = Body(None),
    use_cache: bool = Body(True)
):
    """
    Answer a question using agentic RAG with function calling.
    
    The AI can choose to invoke specialized search tools like
    Neo4j graph search when beneficial.
    """
    try:
        rag_service = RAGService()
        
        # Use agentic version
        answer = rag_service.answer_question_with_tools(
            question=question,
            filters=filters,
            use_cache=use_cache
        )
        
        return {
            "success": True,
            "answer": answer.to_dict()
        }
    except Exception as e:
        logger.error(f"Agentic Q&A failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 7. Add Logging and Monitoring

**File:** `backend/services/rag_service.py`

**Add Tool Usage Tracking:**

```python
# In __init__:
self.tool_usage_stats = {
    "search_regulatory_knowledge_graph": {
        "total_calls": 0,
        "successful_calls": 0,
        "avg_results": 0,
        "by_search_type": {
            "semantic": 0,
            "traversal": 0,
            "hybrid": 0
        }
    }
}

def _log_tool_usage(self, tool_call: Dict[str, Any], result: Dict[str, Any]):
    """Track tool usage metrics for monitoring."""
    tool_name = tool_call["tool_name"]
    
    if tool_name == "search_regulatory_knowledge_graph":
        self.tool_usage_stats[tool_name]["total_calls"] += 1
        
        if result.get("success"):
            self.tool_usage_stats[tool_name]["successful_calls"] += 1
            
        search_type = tool_call["arguments"].get("search_type")
        if search_type:
            self.tool_usage_stats[tool_name]["by_search_type"][search_type] += 1
        
        logger.info(
            f"🔧 Tool Call: {tool_name} | "
            f"Type: {search_type} | "
            f"Results: {result.get('count', 0)} | "
            f"Success: {result.get('success', False)}"
        )
```

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
- [ ] Implement function calling support in Gemini client
- [ ] Create tool schema definitions
- [ ] Implement tool handler for Neo4j search
- [ ] Add comprehensive unit tests

### Phase 2: RAG Integration (Day 3)
- [ ] Add `answer_question_with_tools()` to RAG service
- [ ] Update system prompt with tool usage guidelines
- [ ] Add API endpoint for agentic Q&A
- [ ] Add logging and monitoring

### Phase 3: Testing and Validation (Day 4)
- [ ] Test with relationship-heavy queries
- [ ] Compare agentic vs automatic approaches
- [ ] Validate citation accuracy with tool results
- [ ] Load testing with concurrent tool calls

### Phase 4: Frontend Integration (Day 5)
- [ ] Add toggle for agentic mode in UI
- [ ] Display tool usage in answer metadata
- [ ] Show "Used graph search because..." explanations
- [ ] Update documentation

## Example Query Flows

### Scenario 1: Relationship Query (Tool Use Expected)

**Query:** "What regulations implement Section 7 of the Employment Insurance Act?"

**AI Analysis:**
- Recognizes this needs relationship traversal
- Invokes: `search_regulatory_knowledge_graph(query="Section 7 Employment Insurance Act", search_type="traversal")`
- Receives: 15 regulations that reference this section
- Generates answer with full citations

**Response Time:** ~2-3 seconds (single graph query, no multi-tier fallback)

### Scenario 2: Content Query (No Tool Use)

**Query:** "What are the eligibility requirements for Employment Insurance?"

**AI Analysis:**
- Recognizes this is a content question
- Uses standard retrieval (5-tier flow)
- No tools invoked
- Generates answer from retrieved context

**Response Time:** ~3-4 seconds (standard multi-tier)

### Scenario 3: Complex Query (Multiple Tool Calls)

**Query:** "What are the recent amendments to the Privacy Act and what other acts do they affect?"

**AI Analysis:**
- First call: `search_regulatory_knowledge_graph(query="Privacy Act amendments", search_type="semantic")`
- Second call: `search_regulatory_knowledge_graph(query="Privacy Act references", search_type="traversal")`
- Synthesizes results from both calls
- Generates comprehensive answer

**Response Time:** ~4-5 seconds (two graph queries)

## Success Metrics

### Tool Usage Effectiveness
- **Tool Call Rate:** % of queries that invoke tools (target: 15-25% for relationship queries)
- **Tool Success Rate:** % of tool calls that return useful results (target: >90%)
- **Search Type Distribution:** Track semantic vs traversal vs hybrid usage

### Performance
- **Response Time (Agentic):** p95 < 5 seconds
- **Tool Execution Time:** Graph search < 1 second
- **Accuracy:** Citation accuracy maintained at 100%

### User Experience
- **Confidence Scores:** Tool-based answers should maintain high confidence (>0.8)
- **Result Relevance:** A/B test agentic vs automatic for relationship queries
- **Explainability:** Users understand why graph search was used

## Rollout Strategy

### Stage 1: Limited Beta (Week 1)
- Enable agentic mode for internal testing only
- Use separate `/ask/agentic` endpoint
- Monitor tool usage patterns
- Gather feedback on answer quality

### Stage 2: Opt-In (Week 2)
- Add UI toggle for "Advanced Search Mode"
- Allow power users to opt-in
- Continue monitoring metrics
- Refine tool usage guidelines based on data

### Stage 3: Gradual Rollout (Week 3)
- Enable agentic mode for 25% of users
- Compare metrics vs control group
- Adjust based on performance data

### Stage 4: General Availability (Week 4)
- Make agentic mode the default
- Keep automatic mode as fallback
- Full production monitoring

## Future Enhancements

1. **Additional Tools:**
   - `search_elasticsearch`: Direct Elasticsearch queries
   - `check_compliance`: Validate against regulations
   - `get_statistics`: Database queries for counts/stats
   - `search_by_citation`: Find document by official citation

2. **Multi-Modal Tools:**
   - `analyze_pdf`: Extract info from uploaded PDFs
   - `compare_regulations`: Side-by-side comparison

3. **Agentic Workflows:**
   - Multi-step reasoning with tool chaining
   - "I'll first search the graph, then verify with text search"

4. **Self-Improving:**
   - Track which tool choices led to high confidence answers
   - Train routing model to predict best tool for query type

## Risk Mitigation

### Risk 1: Increased Latency
- **Mitigation:** Tool execution timeouts, parallel tool calls where possible
- **Fallback:** If tool fails, use automatic 5-tier flow

### Risk 2: Tool Overuse
- **Mitigation:** Cost monitoring, rate limits per user
- **Fallback:** Disable agentic mode if costs spike

### Risk 3: Citation Accuracy
- **Mitigation:** Maintain strict RAG enforcement regardless of search method
- **Validation:** Automated tests for citation verification

### Risk 4: Reduced Explainability
- **Mitigation:** Log every tool call, show reasoning in metadata
- **UI:** Display "I used graph search to find related regulations" in answer

## Conclusion

This implementation will make the RAG system more intelligent by allowing the AI to choose the most effective search strategy for each query type. The agentic approach should:

1. **Improve Response Quality:** Graph search for relationship queries, text search for content
2. **Reduce Latency:** Skip unnecessary fallback tiers when AI knows the best approach
3. **Increase Transparency:** Explicit tool usage shows reasoning
4. **Enable Scaling:** Foundation for adding more specialized tools

**Next Steps:** Review this plan and decide on Phase 1 implementation priorities.
