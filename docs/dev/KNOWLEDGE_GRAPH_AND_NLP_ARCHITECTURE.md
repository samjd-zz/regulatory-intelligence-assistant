# Knowledge Graph & NLP Architecture

**Regulatory Intelligence Assistant - Graph Builder & NLP Integration**

This document provides comprehensive visual diagrams showing how our knowledge graph is created and where Natural Language Processing (NLP) is integrated throughout the system.

**✅ Implementation Status (Updated Dec 2024):**
- **Node Types**: Legislation (Acts/Lois) and Regulation nodes are now distinguished by title parsing
- **Relationships**: HAS_SECTION, REFERENCES, APPLIES_TO, RELEVANT_FOR implemented; IMPLEMENTS partially implemented
- **Entity Extraction**: Program and Situation extraction code exists (needs testing with real data)
- **Inter-Document**: Links regulations to legislation based on title mentions
- **NOT YET**: Policy nodes, INTERPRETS, SUPERSEDES relationships

---

## Table of Contents

1. [Overall Data Processing Pipeline](#1-overall-data-processing-pipeline)
2. [Knowledge Graph Creation Flow](#2-knowledge-graph-creation-flow)
3. [NLP Integration Points](#3-nlp-integration-points)
4. [Graph Entity Relationships](#4-graph-entity-relationships)
5. [Query Processing with NLP](#5-query-processing-with-nlp)
6. [Entity Extraction Pipeline](#6-entity-extraction-pipeline)
7. [Graph Builder Internal Flow](#7-graph-builder-internal-flow)
8. [Compliance Checking with Graph & NLP](#8-compliance-checking-with-graph--nlp)

---

## 1. Overall Data Processing Pipeline

This diagram shows the complete data ingestion pipeline from raw XML files to all storage systems, highlighting where NLP is applied.

```mermaid
flowchart TB
    XML["XML Files (Canadian Laws)"] --> Parser["XML Parser"]
    Parser --> ParsedData["Parsed Regulation"]
    
    ParsedData --> ProgramDetector{"Program Detector (NLP)"}
    ProgramDetector --> EnrichedData["Enriched Data"]
    
    EnrichedData --> Pipeline["Data Pipeline"]
    
    Pipeline --> PostgreSQL[("PostgreSQL")]
    Pipeline --> Neo4j[("Neo4j")]
    Pipeline --> Elasticsearch[("Elasticsearch")]
    
    PostgreSQL --> GraphBuilder["Graph Builder (Uses NLP)"]
    GraphBuilder --> NLPExtractor["Legal NLP"]
    NLPExtractor --> Neo4j
    
    UserQuery["User Query"] --> QueryParser["Query Parser (NLP Engine)"]
    QueryParser --> ProcessedQuery["Parsed Query"]
    ProcessedQuery --> SearchEngine["Search Service"]
    ProcessedQuery --> GraphService["Graph Service"]
    
    style ProgramDetector fill:#ff9,stroke:#333,stroke-width:3px
    style NLPExtractor fill:#ff9,stroke:#333,stroke-width:3px
    style QueryParser fill:#ff9,stroke:#333,stroke-width:3px
```

**Key NLP Integration Points:**
1. **Program Detection**: Identifies government programs from text
2. **Entity Extraction**: Extracts legal entities during graph building
3. **Query Understanding**: Parses user queries for intent and entities

---

## 2. Knowledge Graph Creation Flow

This diagram shows the step-by-step process of how the knowledge graph is built from parsed documents.

**✅ = Implemented | ⚠️ = Partially Implemented | ❌ = Not Implemented**

```mermaid
flowchart TD
    Start([Start: Document Ingested]) --> FetchDoc["✅ Fetch Regulation from PostgreSQL"]
    
    FetchDoc --> DetermineType["✅ Determine Node Type (Act/Loi = Legislation)"]
    DetermineType --> CreateDocNode["✅ Create Legislation or Regulation Node"]
    CreateDocNode --> DocNode[("✅ Legislation/Regulation Node in Neo4j")]
    
    DocNode --> CreateSections["✅ Create Section Nodes"]
    CreateSections --> SectionLoop{For Each Section}
    
    SectionLoop -->|Next Section| CreateSectionNode["✅ Create Section Node"]
    CreateSectionNode --> LinkSection["✅ Create HAS_SECTION Relationship"]
    LinkSection --> SectionLoop
    
    SectionLoop -->|All Sections Done| CreateRefs["✅ Create Cross-References (REFERENCES)"]
    CreateRefs --> RefsComplete["✅ Citations Mapped"]
    
    RefsComplete --> ExtractEntities{"⚠️ Extract Entities (NLP Processing)"}
    
    ExtractEntities -->|Extract Programs| ExtractPrograms["⚠️ Extract Program Mentions (code exists)"]
    ExtractPrograms --> CreatePrograms["⚠️ Create Program Nodes"]
    CreatePrograms --> LinkPrograms["⚠️ Link Documents APPLIES_TO Programs"]
    
    ExtractEntities -->|Extract Situations| ExtractSituations["⚠️ Extract Applicable Situations (code exists)"]
    ExtractSituations --> CreateSituations["⚠️ Create Situation Nodes"]
    CreateSituations --> LinkSituations["⚠️ Link Sections RELEVANT_FOR Situations"]
    
    LinkPrograms --> InterDoc["⚠️ Create Inter-Document Relationships"]
    LinkSituations --> InterDoc
    
    InterDoc --> LinkRegs["⚠️ Link Regulations IMPLEMENTS Legislation (title matching)"]
    InterDoc --> LinkPolicies["❌ Link Policies INTERPRETS Legislation (no policies yet)"]
    InterDoc --> LinkSupersedes["❌ Link Updates SUPERSEDES older versions (not implemented)"]
    
    LinkRegs --> Complete([Graph Building Complete])
    LinkPolicies --> Complete
    LinkSupersedes --> Complete
    
    style DetermineType fill:#9f9,stroke:#333,stroke-width:2px
    style ExtractEntities fill:#ff9,stroke:#333,stroke-width:3px
    style ExtractPrograms fill:#ffc,stroke:#333,stroke-width:2px
    style ExtractSituations fill:#ffc,stroke:#333,stroke-width:2px
```

**Graph Building Steps:**
1. **✅ Document Node Creation**: Creates Legislation node (for Acts/Lois) or Regulation node based on title
2. **✅ Section Nodes**: All sections with content and metadata
3. **❌ Hierarchy Creation**: PART_OF relationships removed (parent_section_id doesn't exist)
4. **✅ Cross-References**: Citation links via REFERENCES relationships
5. **⚠️ Entity Extraction (NLP)**: Code exists for Programs and Situations (needs data to trigger)
6. **⚠️ Inter-Document Links**: IMPLEMENTS implemented for Regulations→Legislation; INTERPRETS/SUPERSEDES not yet

---

## 3. NLP Integration Points

This diagram highlights all the places where NLP is used throughout the system.

```mermaid
flowchart TB
    XML["Raw XML/Text"] --> PD["Program Detector"]
    PD --> Programs["Program Tags"]
    
    PD --> JD["Jurisdiction Detector"]
    JD --> Jurisdiction["Jurisdiction Tags"]
    
    Document["Document Text"] --> GB["Graph Builder"]
    GB --> PE["Program Extractor (regex)"]
    GB --> SE["Situation Extractor (patterns)"]
    
    PE --> ProgramNodes[("Program Nodes")]
    SE --> SituationNodes[("Situation Nodes")]
    
    UserQuery["User Query"] --> QP["Query Parser (Main NLP Engine)"]
    
    QP --> IC["Intent Classifier"]
    IC --> Intent["Query Intent"]
    
    QP --> EE["Entity Extractor (legal_nlp.py)"]
    EE --> LExt["LegalEntityExtractor"]
    
    LExt --> PersonTypes["Person Types"]
    LExt --> Programs2["Programs"]
    LExt --> Jurisdictions["Jurisdictions"]
    LExt --> Requirements["Requirements"]
    LExt --> Dates["Dates"]
    LExt --> Money["Monetary Amounts"]
    LExt --> Legislation["Legislation Names"]
    
    QP --> KE["Keyword Extractor"]
    KE --> Keywords["Important Keywords"]
    
    QP --> FE["Filter Extractor"]
    FE --> Filters["Search Filters"]
    
    Keywords --> QE["Query Expander"]
    QE --> ExpandedQueries["Multiple Query Variations"]
    
    FormData["Form Data"] --> CC["Compliance Checker"]
    CC --> NLPRules["NLP-Enhanced Rules"]
    NLPRules --> ValidationResults["Validation Results"]
    
    style QP fill:#ff9,stroke:#333,stroke-width:4px
    style EE fill:#ff9,stroke:#333,stroke-width:4px
    style LExt fill:#ff6,stroke:#333,stroke-width:4px
    style PD fill:#cfc,stroke:#333,stroke-width:2px
    style GB fill:#cfc,stroke:#333,stroke-width:2px
```

**NLP Components:**

1. **Program Detector**: Identifies government programs from text
2. **Entity Extractor**: Extracts legal entities (programs, person types, jurisdictions)
3. **Query Parser**: Main NLP engine for query understanding
4. **Intent Classifier**: Determines user intent (search, compliance, eligibility)
5. **Query Expander**: Generates synonym variations for better search

---

## 4. Graph Entity Relationships

This diagram shows all the node types and relationship types in the knowledge graph.

**CURRENT IMPLEMENTATION STATUS:**

✅ **Implemented and Active:**
- Node Types: `Regulation`, `Section`
- Relationships: `HAS_SECTION`, `PART_OF`, `REFERENCES`

⚠️ **Code Exists But Not Creating Data:**
- Node Types: `Program`, `Situation`
- Relationships: `APPLIES_TO`, `RELEVANT_FOR`, `IMPLEMENTS`, `INTERPRETS`, `SUPERSEDES`

```mermaid
flowchart LR
    R["Regulation (✅ 1,827 nodes)"]
    S["Section (✅ 277,031 nodes)"]
    PR["Program (⚠️ Planned)"]
    SI["Situation (⚠️ Planned)"]
    
    R -->|HAS_SECTION ✅| S
    S -->|PART_OF ✅| S
    S -->|REFERENCES ✅| S
    R -.->|APPLIES_TO ⚠️| PR
    S -.->|RELEVANT_FOR ⚠️| SI
    R -.->|IMPLEMENTS ⚠️| R
    
    style R fill:#4CAF50,stroke:#333,stroke-width:3px
    style S fill:#4CAF50,stroke:#333,stroke-width:3px
    style PR fill:#FFC107,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
    style SI fill:#FFC107,stroke:#333,stroke-width:2px,stroke-dasharray: 5 5
```

**Node Types:**

| Node | Description | Status | Count | Database Table |
|------|-------------|--------|-------|----------------|
| **Regulation** | Acts, laws, regulations | ✅ Active | 1,827 | `regulations` |
| **Section** | Content segments | ✅ Active | 277,031 | `sections` |
| **Program** | Government programs | ⚠️ Planned | 0 | N/A |
| **Situation** | Applicable scenarios | ⚠️ Planned | 0 | N/A |

**Relationship Types:**

| Relationship | From → To | Description | Status | Count |
|--------------|-----------|-------------|--------|-------|
| **HAS_SECTION** | Regulation → Section | Document structure | ✅ Active | 277,027 |
| **PART_OF** | Section → Section | Hierarchy | ✅ Active | 164,722 |
| **REFERENCES** | Section → Section | Citations | ✅ Active | 28,604 |
| **IMPLEMENTS** | Regulation → Regulation | Implementing relationship | ⚠️ Planned | 0 |
| **APPLIES_TO** | Regulation → Program | Program applicability | ⚠️ Planned | 0 |
| **RELEVANT_FOR** | Section → Situation | Scenario relevance | ⚠️ Planned | 0 |
| **INTERPRETS** | Regulation → Regulation | Interpretation | ⚠️ Planned | 0 |
| **SUPERSEDES** | Regulation → Regulation | Version updates | ⚠️ Planned | 0 |

**Note:** The system currently uses a single `Regulation` node type for all regulatory documents (legislation, regulations, policies). The original design had separate node types (`Legislation`, `Policy`) but the implementation consolidated them.

---

## 5. Query Processing with NLP

This diagram shows how user queries are processed using NLP to extract structured information.

```mermaid
flowchart TD
    Query["User Query: Can a temporary resident apply for EI?"] --> QP["Query Parser"]
    
    QP --> Normalize["Normalize Query"]
    
    Normalize --> Parallel{Parallel Processing}
    
    Parallel --> IC["Intent Classification (Pattern Matching)"]
    IC --> IntentResult["Intent: ELIGIBILITY, Confidence: 0.85"]
    
    Parallel --> EE["Entity Extraction (legal_nlp.py)"]
    EE --> LExt["LegalEntityExtractor"]
    LExt --> Entities["Entities: temporary resident, employment insurance"]
    
    Parallel --> KE["Keyword Extraction"]
    KE --> Keywords["Keywords: temporary, resident, apply"]
    
    Parallel --> QT["Question Type Detection"]
    QT --> QType["Type: Can (modal question)"]
    
    IntentResult --> Merge["Merge Results"]
    Entities --> Merge
    Keywords --> Merge
    QType --> Merge
    
    Merge --> FE["Filter Extraction"]
    FE --> Filters["Filters: person_type, program"]
    
    Filters --> ParsedQuery["Parsed Query Object"]
    
    ParsedQuery --> QE["Query Expansion (Synonym generation)"]
    QE --> Expanded["Expanded Queries"]
    
    Expanded --> Search["Search & Retrieval"]
    
    style IC fill:#ff9,stroke:#333,stroke-width:3px
    style EE fill:#ff9,stroke:#333,stroke-width:3px
    style LExt fill:#ff6,stroke:#333,stroke-width:3px
    style QE fill:#ff9,stroke:#333,stroke-width:3px
```

**Query Processing Steps:**

1. **Normalization**: Clean and standardize text
2. **Intent Classification**: Determine what user wants (search, compliance, eligibility)
3. **Entity Extraction**: Find legal entities using patterns and NLP
4. **Keyword Extraction**: Extract important terms
5. **Filter Extraction**: Convert entities to search filters
6. **Query Expansion**: Generate synonyms for better recall

---

## 6. Entity Extraction Pipeline

This diagram shows the detailed NLP process for extracting legal entities from text.

```mermaid
flowchart TD
    Input["Legal Text Input"] --> LEE["LegalEntityExtractor"]
    
    LEE --> Stage1["Stage 1: Pattern-Based Extraction"]
    Stage1 --> Patterns["Compile Regex from Terminology Database"]
    Patterns --> Match["Match Against Text"]
    Match --> Entities1["Pattern-Based Entities"]
    
    LEE --> Stage2["Stage 2: Structured Data Extraction"]
    Stage2 --> DateReg["Date Patterns"]
    Stage2 --> MoneyReg["Money Patterns"]
    Stage2 --> LegReg["Legislation Patterns"]
    DateReg --> Entities2["Structured Entities"]
    MoneyReg --> Entities2
    LegReg --> Entities2
    
    LEE --> Stage3["Stage 3: spaCy NER (Optional)"]
    Stage3 --> SpaCyModel["en_core_web_sm"]
    SpaCyModel --> Entities3["ML-Based Entities"]
    
    Entities1 --> Merge["Merge All Results"]
    Entities2 --> Merge
    Entities3 --> Merge
    
    Merge --> Dedup["Deduplicate by Position"]
    Dedup --> Canon["Normalize to Canonical Forms"]
    Canon --> Conf["Calculate Confidence Scores"]
    Conf --> Ctx["Extract Context (±50 chars)"]
    Ctx --> Output["ExtractedEntity Objects"]
    
    style Stage1 fill:#ff9,stroke:#333,stroke-width:3px
    style Stage2 fill:#9cf,stroke:#333,stroke-width:2px
    style Stage3 fill:#cfc,stroke:#333,stroke-width:2px
```

**Entity Extraction Methods:**

1. **Pattern-Based**: Regex patterns from legal terminology database (highest confidence)
2. **Structured Data**: Specialized regex for dates, money, legislation names
3. **spaCy NER**: Machine learning model for additional entity types (optional)
4. **Canonicalization**: Normalize to standard forms (e.g., "EI" → "employment_insurance")
5. **Confidence Scoring**: Based on match quality and method

**Confidence Scores:**
- Exact canonical match: **0.95**
- Known synonym: **0.85**
- Pattern match: **0.75**
- spaCy entity: **0.80**
- Structured data (date/money): **0.90-0.95**

---

## 7. Graph Builder Internal Flow

This diagram shows the internal methods and data flow within the GraphBuilder service.

```mermaid
flowchart TD
    Start([build_document_graph called]) --> Fetch["Fetch Document from PostgreSQL"]
    
    Fetch --> GetNodeType["Get Node Type (map DocumentType to Neo4j label)"]
    
    GetNodeType --> CreateDoc["Create Document Node"]
    CreateDoc --> DocProps["Set Properties: id, title, jurisdiction, authority, status, metadata"]
    
    DocProps --> CreateSec["Create Section Nodes (loop)"]
    CreateSec --> SecLoop{For Each Section}
    
    SecLoop -->|Create| SecNode["Create Section Node with content"]
    SecNode --> HasSec["Create HAS_SECTION relationship with order"]
    HasSec --> SecLoop
    
    SecLoop -->|Done| CreateHier["Create Hierarchy Relationships (PART_OF)"]
    CreateHier --> PartOf["Create PART_OF relationships"]
    
    PartOf --> CreateXRef["Create Cross-Reference Relationships"]
    CreateXRef --> RefRel["Create REFERENCES relationships"]
    
    RefRel --> ExtractEnt{"Extract and Create Entities (NLP Processing)"}
    
    ExtractEnt --> ExtProg["Extract Programs (Regex patterns)"]
    ExtractEnt --> ExtSit["Extract Situations (Conditional patterns)"]
    
    ExtProg --> ProgPatterns["Program Patterns: employment insurance, CPP, OAS, etc."]
    
    ProgPatterns --> ProgMatch["Regex Search in full_text"]
    ProgMatch --> ProgData["Program Data: name, department, description"]
    
    ProgData --> CreateProg["Create Program Node + APPLIES_TO"]
    
    ExtSit --> SitPatterns["Situation Patterns: if, where, when, in the case of"]
    
    SitPatterns --> SitMatch["Regex Search in section content"]
    SitMatch --> ExtTags["Extract Tags: employment, disability, retirement, etc."]
    
    ExtTags --> SitData["Situation Data: description, tags, source_section"]
    
    SitData --> CreateSit["Create Situation Node + RELEVANT_FOR"]
    
    CreateProg --> Stats["Update Statistics"]
    CreateSit --> Stats
    
    Stats --> Return([Return Stats: nodes_created, relationships_created, errors])
    
    style ExtractEnt fill:#ff9,stroke:#333,stroke-width:4px
    style ExtProg fill:#ffc,stroke:#333,stroke-width:3px
    style ExtSit fill:#ffc,stroke:#333,stroke-width:3px
    style ProgMatch fill:#cfc,stroke:#333,stroke-width:2px
    style SitMatch fill:#cfc,stroke:#333,stroke-width:2px
```

**Key Methods:**

| Method | Purpose | NLP Used |
|--------|---------|----------|
| `build_document_graph` | Main entry point | Orchestrates |
| `_create_document_node` | Create top-level node | ❌ |
| `_create_section_nodes` | Create all sections | ❌ |
| `_create_hierarchy_relationships` | PART_OF links | ❌ |
| `_create_cross_reference_relationships` | REFERENCES links | ❌ |
| `_extract_programs` | Find program mentions | ✅ Regex patterns |
| `_extract_situations` | Find applicable scenarios | ✅ Conditional patterns |
| `_extract_tags` | Categorize situations | ✅ Keyword matching |
| `_create_program_node` | Create Program node | ❌ |
| `_create_situation_node` | Create Situation node | ❌ |

**Program Extraction Patterns:**
```regex
(?i)(employment\s+insurance)\s+(program|benefits?)
(?i)(old\s+age\s+security)\s+(program|benefits?)
(?i)(canada\s+pension\s+plan)\s+(benefits?|program)?
(?i)(workers['']?\s+compensation)\s+(program|benefits?)
```

**Situation Extraction Patterns:**
```regex
(?i)if\s+(?:you|a\s+person|an\s+individual)\s+(?:is|are|has|have)\s+([^.]{10,100})
(?i)where\s+(?:a|an|the)\s+([^.]{10,100})
(?i)in\s+the\s+case\s+of\s+([^.]{10,100})
(?i)when\s+(?:a|an|the)\s+([^.]{10,100})
```

---

## 8. Compliance Checking with Graph & NLP

This diagram shows how compliance checking leverages both the knowledge graph and NLP.

```mermaid
flowchart TB
    FormData["Form Submission (Field: Value pairs)"] --> CC["Compliance Checker"]
    
    CC --> LoadRules["Load Compliance Rules from config"]
    LoadRules --> Rules[("Compliance Rules per program")]
    
    Rules --> ValidateFields{Validate Each Field}
    
    ValidateFields -->|Extract entities| NLP["Entity Extraction (legal_nlp.py)"]
    NLP --> Entities["Extracted Entities"]
    
    ValidateFields -->|Check graph| Graph["Query Knowledge Graph (graph_service.py)"]
    Graph --> RegNodes["Related Regulations & Sections"]
    
    Entities --> MergeContext["Merge Context"]
    RegNodes --> MergeContext
    Rules --> MergeContext
    
    MergeContext --> ApplyRules["Apply Validation Rules with NLP context"]
    
    ApplyRules --> CheckRequired["Check Required Fields"]
    ApplyRules --> CheckFormat["Check Format Rules"]
    ApplyRules --> CheckEligibility["Check Eligibility based on person type"]
    ApplyRules --> CheckDates["Check Date Rules"]
    
    CheckRequired --> Issues{Any Issues?}
    CheckFormat --> Issues
    CheckEligibility --> Issues
    CheckDates --> Issues
    
    Issues -->|Yes| GenerateErrors["Generate Error Messages with citations"]
    Issues -->|No| GenerateSuccess["Generate Success with supporting regulations"]
    
    GenerateErrors --> Report["Compliance Report: is_compliant=false, issues, recommendations"]
    
    GenerateSuccess --> Report2["Compliance Report: is_compliant=true, regulations, confidence"]
    
    Report --> Output["Return to User"]
    Report2 --> Output
    
    style NLP fill:#ff9,stroke:#333,stroke-width:3px
    style Graph fill:#9cf,stroke:#333,stroke-width:3px
    style ApplyRules fill:#cfc,stroke:#333,stroke-width:2px
```

**Compliance Checking Process:**

1. **Load Rules**: Program-specific validation rules
2. **Extract Entities**: Use NLP to identify person types, requirements, programs
3. **Query Graph**: Find relevant regulations and sections
4. **Merge Context**: Combine rules, entities, and graph data
5. **Apply Validations**: Check required fields, formats, eligibility, dates
6. **Generate Report**: Create detailed compliance report with citations

**Example Flow:**

```
User Query: "Check EI application for temporary resident"
↓
NLP Extraction:
  - person_type: "temporary_resident"
  - program: "employment_insurance"
↓
Graph Query:
  - Find EI regulations
  - Find sections about eligibility
  - Find temporary resident requirements
↓
Validation:
  - Required fields present?
  - Valid SIN format?
  - Is temporary resident eligible for EI? (Check graph)
↓
Result:
  ✓ Valid SIN format
  ✓ All required fields present
  ✗ Temporary residents not eligible for EI
     Citation: EI Act Section 7(1)(a) - must be "insured person"
```

---

## Summary: Where NLP is Used

| Component | NLP Technology | Purpose |
|-----------|---------------|---------|
| **Program Detector** | Regex + Keywords | Detect government programs from text |
| **Graph Builder** | Regex patterns | Extract programs and situations during graph creation |
| **Legal Entity Extractor** | Regex + spaCy (optional) | Extract person types, programs, jurisdictions, requirements |
| **Query Parser** | Pattern matching + Entity extraction | Understand user intent and extract entities |
| **Intent Classifier** | Pattern matching | Classify query intent (search, compliance, eligibility) |
| **Query Expander** | Synonym generation | Create query variations for better search |
| **Compliance Checker** | Entity extraction | Extract entities from form data for validation |

---

## Technology Stack

### NLP Components
- **Pattern-Based**: Regex patterns for legal terminology (primary method)
- **spaCy**: Optional ML-based NER (for organizations, dates, money)
- **Custom Extractors**: Specialized for legal/regulatory text

### Knowledge Graph
- **Neo4j**: Graph database for storing entities and relationships
- **Cypher**: Query language for graph traversal

### Search
- **Elasticsearch**: Full-text search with metadata filtering
- **Hybrid Search**: Keyword + semantic search

### Embeddings & RAG
- **Gemini API**: Vector embeddings for semantic search
- **Retrieval-Augmented Generation**: Context-aware answers

---

## Key Design Principles

1. **Legal Accuracy**: All NLP must preserve legal meaning and context
2. **Verifiable Citations**: Every extracted entity linked to source text
3. **Confidence Scoring**: All NLP outputs include confidence scores
4. **Human Review**: High-stakes decisions require expert validation
5. **Explainability**: Clear reasoning for all NLP decisions
6. **Multi-System**: Graph, search, and relational DB work together
7. **Incremental Processing**: Build graph as documents are ingested

---

## Performance Characteristics

| Operation | Time | NLP Overhead |
|-----------|------|--------------|
| **Graph Build** (per document) | 1-5 seconds | ~20% (entity extraction) |
| **Entity Extraction** | 50-200ms | 100% (NLP operation) |
| **Query Parsing** | 10-50ms | 100% (NLP operation) |
| **Graph Traversal** | <100ms | 0% (pure graph query) |
| **Compliance Check** | 100-500ms | ~30% (entity extraction) |

---

## Future Enhancements

1. **Fine-tuned Legal LLM**: Domain-specific language model for Canadian law
2. **Graph Neural Networks**: ML on knowledge graph for better recommendations
3. **Active Learning**: Improve entity extraction from user feedback
4. **Cross-Reference Resolution**: Better linking between documents
5. **Multi-Lingual NLP**: Enhanced French language support
6. **Semantic Similarity**: Vector-based section similarity
7. **Temporal Reasoning**: Track regulatory changes over time

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-11  
**Authors**: Regulatory Intelligence Team
