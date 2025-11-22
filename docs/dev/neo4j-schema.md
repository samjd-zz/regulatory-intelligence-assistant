# Neo4j Knowledge Graph Schema

This document defines the node types, relationship types, and properties used in the Regulatory Intelligence Assistant knowledge graph.

## Node Types

### 1. Legislation
Primary legislative documents (Acts, Statutes)

**Properties:**
- `id` (String, UUID): Unique identifier
- `title` (String): Legislation title
- `jurisdiction` (String): federal, provincial, or municipal
- `authority` (String): Issuing authority (e.g., "Parliament of Canada")
- `effective_date` (Date): When legislation became effective
- `status` (String): active, amended, or repealed
- `full_text` (String, optional): Full text of legislation
- `act_number` (String, optional): Official act number (e.g., "S.C. 1996, c. 23")
- `metadata` (JSON, optional): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Example:**
```cypher
CREATE (l:Legislation {
  id: "uuid-123",
  title: "Employment Insurance Act",
  jurisdiction: "federal",
  authority: "Parliament of Canada",
  effective_date: "1996-06-30",
  status: "active",
  act_number: "S.C. 1996, c. 23"
})
```

### 2. Section
Individual sections and subsections of legislation

**Properties:**
- `id` (String, UUID): Unique identifier
- `section_number` (String): Section identifier (e.g., "7(1)(a)")
- `title` (String): Section title
- `content` (String): Section content/text
- `level` (Integer): Nesting level (0 for top level)
- `metadata` (JSON, optional): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Example:**
```cypher
CREATE (s:Section {
  id: "uuid-456",
  section_number: "7(1)",
  title: "Eligibility for benefits",
  content: "Subject to this Part, benefits are payable...",
  level: 0
})
```

### 3. Regulation
Regulatory provisions and implementing rules

**Properties:**
- `id` (String, UUID): Unique identifier
- `title` (String): Regulation title
- `authority` (String): Issuing authority
- `effective_date` (Date): When regulation became effective
- `status` (String): active, amended, or repealed
- `full_text` (String, optional): Full text of regulation
- `metadata` (JSON, optional): Additional metadata (e.g., regulation number)
- `created_at` (DateTime): Node creation timestamp

**Example:**
```cypher
CREATE (r:Regulation {
  id: "uuid-789",
  title: "Employment Insurance Regulations",
  authority: "Governor in Council",
  effective_date: "1996-07-30",
  status: "active"
})
```

### 4. Policy
Government policies and guidelines

**Properties:**
- `id` (String, UUID): Unique identifier
- `title` (String): Policy title
- `department` (String): Responsible department
- `version` (String): Policy version
- `effective_date` (Date): When policy became effective
- `metadata` (JSON, optional): Additional metadata
- `created_at` (DateTime): Node creation timestamp

### 5. Program
Government programs and services

**Properties:**
- `id` (String, UUID): Unique identifier
- `name` (String): Program name
- `department` (String): Administering department
- `description` (String): Program description
- `eligibility_criteria` (List of Strings, optional): Eligibility requirements
- `metadata` (JSON, optional): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Example:**
```cypher
CREATE (p:Program {
  id: "uuid-abc",
  name: "Employment Insurance Regular Benefits",
  department: "Employment and Social Development Canada",
  description: "Provides temporary financial assistance to unemployed Canadians",
  eligibility_criteria: ["Lost job through no fault of own", "Available and able to work"]
})
```

### 6. Situation
Applicable scenarios and use cases

**Properties:**
- `id` (String, UUID): Unique identifier
- `description` (String): Situation description
- `tags` (List of Strings, optional): Situation tags for categorization
- `metadata` (JSON, optional): Additional metadata
- `created_at` (DateTime): Node creation timestamp

**Example:**
```cypher
CREATE (sit:Situation {
  id: "uuid-def",
  description: "Temporary foreign worker seeking employment benefits",
  tags: ["temporary_worker", "employment_insurance", "work_permit"]
})
```

## Relationship Types

### 1. HAS_SECTION
Connects Legislation to its Sections

**Direction:** Legislation → Section

**Properties:**
- `order` (Integer): Section order within legislation
- `created_at` (DateTime): Relationship creation timestamp

**Example:**
```cypher
MATCH (l:Legislation {id: "leg-123"})
MATCH (s:Section {id: "sec-456"})
CREATE (l)-[:HAS_SECTION {order: 0}]->(s)
```

### 2. REFERENCES
Cross-references between Sections

**Direction:** Section → Section

**Properties:**
- `citation_text` (String): Citation text
- `context` (String, optional): Context of reference
- `created_at` (DateTime): Relationship creation timestamp

**Example:**
```cypher
MATCH (s1:Section {id: "sec-1"})
MATCH (s2:Section {id: "sec-2"})
CREATE (s1)-[:REFERENCES {
  citation_text: "See Section 7(2) for details",
  context: "Eligibility determination"
}]->(s2)
```

### 3. AMENDED_BY
Indicates amendments between Sections

**Direction:** Section → Section

**Properties:**
- `effective_date` (Date): When amendment became effective
- `description` (String): Amendment description
- `created_at` (DateTime): Relationship creation timestamp

### 4. IMPLEMENTS
Regulation implements Legislation

**Direction:** Regulation → Legislation

**Properties:**
- `description` (String, optional): Implementation description
- `created_at` (DateTime): Relationship creation timestamp

**Example:**
```cypher
MATCH (r:Regulation {id: "reg-123"})
MATCH (l:Legislation {id: "leg-456"})
CREATE (r)-[:IMPLEMENTS {
  description: "Implements EI Act provisions"
}]->(l)
```

### 5. INTERPRETS
Policy interprets Legislation

**Direction:** Policy → Legislation

**Properties:**
- `description` (String, optional): Interpretation description
- `created_at` (DateTime): Relationship creation timestamp

### 6. APPLIES_TO
Regulation applies to Program

**Direction:** Regulation → Program

**Properties:**
- `description` (String, optional): Application description
- `created_at` (DateTime): Relationship creation timestamp

**Example:**
```cypher
MATCH (r:Regulation {id: "reg-123"})
MATCH (p:Program {id: "prog-456"})
CREATE (r)-[:APPLIES_TO {
  description: "EI program requirements"
}]->(p)
```

### 7. RELEVANT_FOR
Section is relevant for Situation

**Direction:** Section → Situation

**Properties:**
- `relevance_score` (Float): Relevance score (0.0-1.0)
- `description` (String, optional): Relevance description
- `created_at` (DateTime): Relationship creation timestamp

**Example:**
```cypher
MATCH (s:Section {id: "sec-123"})
MATCH (sit:Situation {id: "sit-456"})
CREATE (s)-[:RELEVANT_FOR {
  relevance_score: 0.95,
  description: "Eligibility requirements for temporary workers"
}]->(sit)
```

### 8. SUPERSEDES
One Legislation supersedes another

**Direction:** Legislation → Legislation

**Properties:**
- `effective_date` (Date): When supersession became effective
- `description` (String, optional): Supersession description
- `created_at` (DateTime): Relationship creation timestamp

### 9. PART_OF
Parent-child hierarchy for Sections

**Direction:** Section → Section (child → parent)

**Properties:**
- `order` (Integer): Order within parent
- `created_at` (DateTime): Relationship creation timestamp

## Constraints

The following unique constraints ensure data integrity:

```cypher
CREATE CONSTRAINT legislation_id IF NOT EXISTS
FOR (l:Legislation) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT section_id IF NOT EXISTS
FOR (s:Section) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT regulation_id IF NOT EXISTS
FOR (r:Regulation) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT policy_id IF NOT EXISTS
FOR (p:Policy) REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT program_id IF NOT EXISTS
FOR (prog:Program) REQUIRE prog.id IS UNIQUE;

CREATE CONSTRAINT situation_id IF NOT EXISTS
FOR (sit:Situation) REQUIRE sit.id IS UNIQUE;
```

## Indexes

Performance indexes for common queries:

```cypher
// Legislation indexes
CREATE INDEX legislation_title IF NOT EXISTS
FOR (l:Legislation) ON (l.title);

CREATE INDEX legislation_jurisdiction IF NOT EXISTS
FOR (l:Legislation) ON (l.jurisdiction);

CREATE INDEX legislation_status IF NOT EXISTS
FOR (l:Legislation) ON (l.status);

// Section indexes
CREATE INDEX section_number IF NOT EXISTS
FOR (s:Section) ON (s.section_number);

// Full-text search indexes
CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
FOR (l:Legislation) ON EACH [l.title, l.full_text];

CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
FOR (s:Section) ON EACH [s.title, s.content];
```

## Common Query Patterns

### Find Legislation with Sections
```cypher
MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
WHERE l.title CONTAINS 'Employment'
RETURN l, s
ORDER BY s.order
```

### Find Related Regulations
```cypher
MATCH (l:Legislation {id: $legislation_id})<-[:IMPLEMENTS]-(r:Regulation)
RETURN r
```

### Find Cross-References
```cypher
MATCH (s:Section {id: $section_id})-[:REFERENCES*1..2]-(related:Section)
RETURN related
```

### Search by Situation
```cypher
MATCH (s:Section)-[r:RELEVANT_FOR]->(sit:Situation)
WHERE sit.description CONTAINS 'retirement'
RETURN s, r.relevance_score
ORDER BY r.relevance_score DESC
```

### Full-Text Search
```cypher
CALL db.index.fulltext.queryNodes('legislation_fulltext', 'employment insurance')
YIELD node, score
RETURN node, score
ORDER BY score DESC
LIMIT 10
```
