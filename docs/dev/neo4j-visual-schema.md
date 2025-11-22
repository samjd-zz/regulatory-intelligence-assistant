# Neo4j Knowledge Graph - Visual Schema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REGULATORY INTELLIGENCE KNOWLEDGE GRAPH                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   Legislation    │─────HAS_SECTION────▶┌──────────┐
│                  │                      │ Section  │◀─┐
│ • title          │                      │          │  │
│ • jurisdiction   │                      │ • number │  │
│ • authority      │                      │ • title  │  │ REFERENCES
│ • status         │                      │ • content│──┘
│ • act_number     │                      └──────────┘
└────────┬─────────┘                           │
         │                                     │
         │                              RELEVANT_FOR
         │                                     │
         │ IMPLEMENTS                          ▼
         │                              ┌──────────────┐
      ┌──┴──────────┐                  │  Situation   │
      │ Regulation  │                  │              │
      │             │                  │ • description│
      │ • title     │                  │ • tags       │
      │ • authority │                  └──────────────┘
      │ • status    │
      └──────┬──────┘
             │
             │ APPLIES_TO
             │
             ▼
      ┌─────────────┐
      │  Program    │
      │             │
      │ • name      │
      │ • department│
      │ • criteria  │
      └─────────────┘
```

## Detailed Relationship Diagram

```
                          ┌─────────────────────────────────┐
                          │       Legislation Node          │
                          │  (Employment Insurance Act)     │
                          │                                 │
                          │  id: uuid-123                   │
                          │  title: "Employment Insurance   │
                          │         Act"                    │
                          │  jurisdiction: "federal"        │
                          │  status: "active"               │
                          │  act_number: "S.C. 1996, c. 23" │
                          └────────┬───────────────┬────────┘
                                   │               │
                    HAS_SECTION    │               │    IMPLEMENTS
                    (order: 0)     │               │    ◀──────────
                                   │               │
                          ┌────────▼────────┐     │
                          │  Section Node   │     │
                          │   (Section 7)   │     │
                          │                 │     │
                          │  id: uuid-456   │     │
                          │  section_number │     │
                          │  : "7(1)"       │     │
                          │  title: "Elig..." │   │
                          │  content: "..." │     │
                          └────┬──────┬─────┘     │
                               │      │           │
                    REFERENCES │      │           │
                         ◀─────┘      │           │
                                      │           │
                            RELEVANT_ │           │
                               FOR    │           │
                          (relevance: │           │
                            0.95)     │           │
                                      │           │
                          ┌───────────▼─────┐    │
                          │ Situation Node  │    │
                          │                 │    │
                          │  id: uuid-789   │    │
                          │  description:   │    │
                          │   "Temp worker  │    │
                          │    seeking EI"  │    │
                          │  tags: ["temp", │    │
                          │    "ei", "work"]│    │
                          └─────────────────┘    │
                                                  │
                          ┌─────────────────┐    │
                          │ Regulation Node │────┘
                          │                 │
                          │  id: uuid-abc   │
                          │  title: "EI     │
                          │   Regulations"  │
                          │  authority:     │
                          │   "Governor in  │
                          │    Council"     │
                          └────────┬────────┘
                                   │
                                   │ APPLIES_TO
                                   │
                          ┌────────▼────────┐
                          │  Program Node   │
                          │                 │
                          │  id: uuid-def   │
                          │  name: "EI      │
                          │   Regular       │
                          │   Benefits"     │
                          │  department:    │
                          │   "ESDC"        │
                          └─────────────────┘
```

## Graph Traversal Examples

### Example 1: Find All Programs Related to a Legislation

```
User Query: "What programs are available under Employment Insurance Act?"

Graph Path:
┌─────────────┐       ┌────────────┐       ┌──────────┐
│ Legislation │◀──────│ Regulation │──────▶│ Program  │
│  (EI Act)   │IMPL   │ (EI Regs)  │APPL   │(EI Bene) │
└─────────────┘EMENTS └────────────┘IES_TO └──────────┘

Cypher Query:
MATCH (l:Legislation {title: "Employment Insurance Act"})
      <-[:IMPLEMENTS]-(r:Regulation)
      -[:APPLIES_TO]->(p:Program)
RETURN p
```

### Example 2: Find Relevant Sections for a Situation

```
User Query: "I'm a temporary worker. What regulations apply to me?"

Graph Path:
┌──────────┐       ┌─────────────┐       ┌─────────────┐
│ Section  │──────▶│  Situation  │       │ Legislation │
│  7(1)    │RELEV  │  (Temp      │       │  (EI Act)   │
│  7(2)    │ANT_   │   Worker)   │       └──────▲──────┘
└────▲─────┘FOR    └─────────────┘              │
     │                                           │
     └───────────────HAS_SECTION─────────────────┘

Cypher Query:
MATCH (sit:Situation {description: "Temporary foreign worker..."})
      <-[:RELEVANT_FOR]-(s:Section)
      <-[:HAS_SECTION]-(l:Legislation)
RETURN l, s
ORDER BY relevance_score DESC
```

### Example 3: Find Cross-Referenced Sections

```
Section 7(1) References Section 7(2):

┌──────────────┐                    ┌──────────────┐
│ Section 7(1) │────REFERENCES─────▶│ Section 7(2) │
│              │                     │              │
│ "Eligibility"│  citation_text:    │ "Qualif..."  │
│              │  "See 7(2)..."     │              │
└──────────────┘                    └──────────────┘
         │                                  │
         │                                  │
         └──────────HAS_SECTION─────────────┘
                         │
                ┌────────▼────────┐
                │   Legislation   │
                │   (EI Act)      │
                └─────────────────┘

Cypher Query:
MATCH (s1:Section {section_number: "7(1)"})
      -[r:REFERENCES]->(s2:Section)
RETURN s1, r, s2
```

## Data Flow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION FLOW                          │
└─────────────────────────────────────────────────────────────────┘

1. Legislation Created
   ┌─────────────────┐
   │   Input Data    │
   │  - Title        │
   │  - Jurisdiction │
   │  - Authority    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ graph_service.  │
   │ create_         │
   │ legislation()   │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Neo4j Client   │
   │  create_node()  │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │   Neo4j DB      │
   │ (Legislation    │
   │     Node)       │
   └─────────────────┘

2. Sections Added & Linked
   ┌─────────────────┐
   │ Section Data    │
   │  - Number       │
   │  - Title        │
   │  - Content      │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ create_section()│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ link_section_   │
   │ to_legislation()│
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  HAS_SECTION    │
   │  Relationship   │
   └─────────────────┘

3. Situations Mapped
   ┌─────────────────┐
   │Situation Data   │
   │  - Description  │
   │  - Tags         │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ link_section_to_│
   │ situation()     │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │ RELEVANT_FOR    │
   │ Relationship    │
   │ (with score)    │
   └─────────────────┘
```

## Query Performance Path

```
┌──────────────────────────────────────────────────────────────┐
│                 QUERY EXECUTION PATH                         │
└──────────────────────────────────────────────────────────────┘

User Query: "Find employment benefits for temporary workers"

     ┌────────────────┐
     │ FastAPI        │
     │ Endpoint       │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │ Graph Service  │
     │ search_...()   │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │ Neo4j Client   │
     │ execute_query()│
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │ Cypher Query   │──────────┐
     │ Optimization   │          │
     └───────┬────────┘          │
             │                   │
             ▼                   │
     ┌────────────────┐          │
     │ Index Lookup   │◀─────────┘
     │ (Fast!)        │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │ Graph          │
     │ Traversal      │
     └───────┬────────┘
             │
             ▼
     ┌────────────────┐
     │ Results        │
     │ Returned       │
     └────────────────┘
```

## Node Relationships Matrix

```
                  Legislation  Section  Regulation  Policy  Program  Situation
Legislation            -         →          ←         ←       -         -
Section                ←         ↔          -         -       -         →
Regulation             →         -          -         -       →         -
Policy                 →         -          -         -       -         -
Program                -         -          ←         -       -         -
Situation              -         ←          -         -       -         -

Legend:
→  Outgoing relationship
←  Incoming relationship
↔  Bidirectional
-  No direct relationship
```

## Graph Statistics (After Seeding)

```
╔════════════════════════════════════════════════════════════╗
║              KNOWLEDGE GRAPH STATISTICS                     ║
╠════════════════════════════════════════════════════════════╣
║  Total Nodes:              39                               ║
║  ├─ Legislation:          15                               ║
║  ├─ Section:              12                               ║
║  ├─ Regulation:            2                               ║
║  ├─ Program:               5                               ║
║  └─ Situation:             5                               ║
║                                                             ║
║  Total Relationships:     25+                              ║
║  ├─ HAS_SECTION:          12                               ║
║  ├─ IMPLEMENTS:            2                               ║
║  ├─ APPLIES_TO:            2                               ║
║  ├─ RELEVANT_FOR:          5+                              ║
║  └─ REFERENCES:            2+                              ║
╚════════════════════════════════════════════════════════════╝
```
