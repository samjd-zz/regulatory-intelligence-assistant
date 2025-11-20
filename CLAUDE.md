# CLAUDE.md - Regulatory Intelligence Assistant

## Project Context
You are working on the **Regulatory Intelligence Assistant for Public Service**, an AI-powered platform that helps public servants and citizens navigate complex laws, policies, and regulations with consistent interpretation and reduced cognitive load.

## Project Goals
- **G7 GovAI Challenge**: Statement 2 - Navigating Complex Regulations
- **Mission**: Streamline interpretation and application of rules to increase consistency and compliance
- **Timeline**: 2-week MVP for competition (Nov 17 - Dec 1, 2025)
- **Target Impact**: 60-75% reduction in research time, 80% reduction in decision inconsistencies

## Key Architecture Components

### 1. Regulatory Knowledge Graph
- Structured representation of legislation, regulations, policies
- Semantic relationships (references, amendments, dependencies, conflicts)
- Cross-jurisdictional mapping
- Program and service connections
- Temporal versioning for changes

### 2. Legal NLP Engine
- Query parsing and entity extraction
- Intent classification (search, compliance, interpretation)
- Named entity recognition (programs, jurisdictions, person types)
- Context enrichment for better understanding
- Plain language generation

### 3. RAG System with Gemini API
- Upload regulatory documents to Gemini
- Semantic search across legal corpus
- Answer questions with source citations
- Handle ambiguous queries with clarification
- Multi-document reasoning

### 4. Semantic Search Engine
- Natural language queries
- Hybrid search (keyword + semantic + graph)
- Faceted filtering and relevance ranking
- Citation-aware results
- Similar regulation discovery

### 5. Compliance Checking Engine
- Form validation against regulations
- Requirement extraction and checking
- Real-time compliance feedback
- Gap analysis for missing information
- Confidence scoring

### 6. Guided Workflows
- Step-by-step processes for common scenarios
- Decision trees for complex regulations
- Dynamic questionnaires
- Pre-filled templates
- Escalation triggers for edge cases

## Technology Stack
- **Frontend**: React with accessible UI
- **Backend**: Python FastAPI for legal processing
- **AI**: Fine-tuned BERT/RoBERTa, Gemini API for RAG
- **Knowledge Graph**: Neo4j for relationships
- **Search**: Elasticsearch + Pinecone/Weaviate for vectors
- **Database**: PostgreSQL (metadata), Redis (caching)

## Critical Requirements

### Legal Accuracy
- All interpretations must cite authoritative sources
- Confidence scores for every recommendation
- Alternative interpretations for ambiguous cases
- Expert validation for high-stakes decisions
- Complete audit trails

### Source Authority
- Only official government legal sources
- Cryptographic verification of content
- Version tracking for all regulations
- Legislative change monitoring
- Precedent database maintenance

### Explainability
- Cite specific sections, clauses, subsections
- Show reasoning chain with legal references
- Flag regulatory conflicts
- Provide confidence levels
- Explain uncertainty clearly

### Performance
- Search response <3 seconds (p95)
- Q&A response <5 seconds (p95)
- Support 100+ concurrent users
- 99.95% uptime
- Process 500-1000 queries daily

## Development Approach

### AI-TDD Process
1. Create expert-labeled test dataset
2. Establish accuracy baselines
3. Implement with continuous validation
4. Legal expert review of outputs
5. Iterative refinement with feedback

### Legal Processing Pipeline
```
User Query → NLP Processing → Entity Extraction → 
Intent Classification → Knowledge Graph Query → 
Document Retrieval → RAG Generation → Citation Verification → 
Confidence Scoring → Response with Sources
```

### Testing Strategy
- Expert-validated test queries (20-30 scenarios)
- Precision/recall testing on legal Q&A
- Citation accuracy verification (100% requirement)
- Cross-validation with legal experts
- User acceptance testing with caseworkers

## Common Scenarios to Handle

### Regulatory Search Query
```
User: "Can a temporary resident apply for employment insurance?"
- Extract entities: person type (temporary resident), program (EI)
- Identify intent: eligibility question
- Search knowledge graph for relevant regulations
- Retrieve EI Act sections on residency requirements
- Generate answer with specific section citations
- Provide confidence score
```

### Compliance Checking
```
Input: Application form for program
- Extract program requirements from regulations
- Parse form data for completeness
- Check each requirement against form data
- Flag missing information or errors
- Suggest corrections with legal basis
- Generate compliance report
```

### Regulatory Change Impact
```
Event: Amendment to legislation
- Identify affected regulations and programs
- Analyze impact on existing processes
- Generate notifications for subscribers
- Update knowledge graph relationships
- Flag conflicting regulations
```

## Available Documentation
- `idea.md`: Complete feature proposal and architecture
- `prd.md`: Product requirements and specifications
- `design.md`: Technical design details
- `plan.md`: Implementation roadmap
- `README.md`: Project overview

## Key Metrics to Track
- Search precision/recall (target: >75%)
- Response time (target: <3s for 95% of queries)
- Citation accuracy (target: 100% verifiable)
- User confidence scores (target: 80% increased)
- Decision consistency (target: 80% reduction in variance)
- Time savings (target: 60-75% reduction)
- Query volume and patterns
- Expert validation rate

## What Makes This Project Unique
- **Legal Intelligence**: Specialized for government regulations
- **Graph-Based Reasoning**: Relationships between laws, not just text
- **Explainable AI**: Every answer backed by legal citations
- **Continuous Learning**: Improves from expert feedback
- **Bilingual Support**: English and French for Canadian government

## When Coding

### Always Consider
- Is this citing authoritative sources?
- What's the confidence level?
- Are there alternative interpretations?
- Is this explanation clear for non-lawyers?
- Are we handling regulatory conflicts?
- Is there an audit trail?

### Never Do
- Provide legal advice without citations
- Claim certainty when regulations are ambiguous
- Skip version control for regulations
- Ignore conflicts between laws
- Deploy without legal expert review
- Mix AI interpretations with official sources without clear distinction

## Gemini API Integration
This project uses Gemini API's file search for regulatory RAG:
- Upload federal legislation and regulations
- Automatic semantic indexing
- Context-aware legal Q&A
- Multi-document reasoning for complex queries
- Citation extraction and verification
- See: https://ai.google.dev/gemini-api/docs/file-search

## Legal NLP Best Practices
1. **Preserve Legal Language**: Don't oversimplify technical terms
2. **Citation Format**: Use official format (e.g., "S.C. 1996, c. 23, s. 7(1)")
3. **Temporal Awareness**: Track effective dates and amendments
4. **Cross-References**: Follow and resolve internal references
5. **Hierarchy**: Respect legal document structure and authority
6. **Plain Language Bridge**: Explain legal concepts accessibly without losing accuracy

## Knowledge Graph Design
- **Nodes**: Legislation, sections, regulations, policies, programs
- **Edges**: references, amends, implements, conflicts_with, applies_to
- **Properties**: effective_date, jurisdiction, authority, version
- **Queries**: Find applicable laws, trace amendments, detect conflicts

## Questions to Ask
When implementing features, ask:
1. Is this citing the correct authoritative source?
2. What happens if the regulation is ambiguous?
3. How do we handle conflicting regulations?
4. Can a caseworker understand the reasoning?
5. What's our confidence in this interpretation?
6. Is the citation format correct?
7. Are we tracking all regulatory changes?

## Success Looks Like
A system where public servants can:
- Find relevant regulations in seconds, not hours
- Get consistent interpretations across employees
- Understand complex legal concepts in plain language
- Check compliance automatically during form completion
- Track regulatory changes affecting their programs
- Reduce cognitive load and job stress
- Make confident, compliant decisions
- Spend 60-75% less time on regulatory research
