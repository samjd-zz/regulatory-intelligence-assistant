// Neo4j Knowledge Graph Schema Initialization
// This script sets up the schema for the Regulatory Intelligence Assistant

// ============================================
// CONSTRAINTS (Unique IDs)
// ============================================

// Create unique constraint on Legislation ID
CREATE CONSTRAINT legislation_id IF NOT EXISTS
FOR (l:Legislation) REQUIRE l.id IS UNIQUE;

// Create unique constraint on Section ID
CREATE CONSTRAINT section_id IF NOT EXISTS
FOR (s:Section) REQUIRE s.id IS UNIQUE;

// Create unique constraint on Regulation ID
CREATE CONSTRAINT regulation_id IF NOT EXISTS
FOR (r:Regulation) REQUIRE r.id IS UNIQUE;

// Create unique constraint on Policy ID
CREATE CONSTRAINT policy_id IF NOT EXISTS
FOR (p:Policy) REQUIRE p.id IS UNIQUE;

// Create unique constraint on Program ID
CREATE CONSTRAINT program_id IF NOT EXISTS
FOR (prog:Program) REQUIRE prog.id IS UNIQUE;

// Create unique constraint on Situation ID
CREATE CONSTRAINT situation_id IF NOT EXISTS
FOR (sit:Situation) REQUIRE sit.id IS UNIQUE;

// ============================================
// INDEXES (Performance)
// ============================================

// Legislation indexes
CREATE INDEX legislation_title IF NOT EXISTS
FOR (l:Legislation) ON (l.title);

CREATE INDEX legislation_jurisdiction IF NOT EXISTS
FOR (l:Legislation) ON (l.jurisdiction);

CREATE INDEX legislation_effective_date IF NOT EXISTS
FOR (l:Legislation) ON (l.effective_date);

CREATE INDEX legislation_status IF NOT EXISTS
FOR (l:Legislation) ON (l.status);

// Section indexes
CREATE INDEX section_number IF NOT EXISTS
FOR (s:Section) ON (s.section_number);

CREATE INDEX section_title IF NOT EXISTS
FOR (s:Section) ON (s.title);

// Regulation indexes
CREATE INDEX regulation_title IF NOT EXISTS
FOR (r:Regulation) ON (r.title);

CREATE INDEX regulation_authority IF NOT EXISTS
FOR (r:Regulation) ON (r.authority);

// Policy indexes
CREATE INDEX policy_title IF NOT EXISTS
FOR (p:Policy) ON (p.title);

CREATE INDEX policy_department IF NOT EXISTS
FOR (p:Policy) ON (p.department);

// Program indexes
CREATE INDEX program_name IF NOT EXISTS
FOR (prog:Program) ON (prog.name);

CREATE INDEX program_department IF NOT EXISTS
FOR (prog:Program) ON (prog.department);

// Situation indexes
CREATE INDEX situation_description IF NOT EXISTS
FOR (sit:Situation) ON (sit.description);

// ============================================
// FULL-TEXT SEARCH INDEXES
// ============================================

// Full-text search on Legislation
CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
FOR (l:Legislation) ON EACH [l.title, l.full_text];

// Full-text search on Section
CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
FOR (s:Section) ON EACH [s.title, s.content];

// Full-text search on Regulation
CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS
FOR (r:Regulation) ON EACH [r.title, r.full_text];

// ============================================
// NODE TYPE DEFINITIONS (Documentation)
// ============================================

// Legislation: Primary legislative documents (Acts, Statutes)
// Properties:
//   - id: UUID (unique)
//   - title: String
//   - jurisdiction: String (federal, provincial, municipal)
//   - authority: String (issuing authority)
//   - effective_date: Date
//   - status: String (active, amended, repealed)
//   - full_text: String
//   - act_number: String
//   - metadata: Map

// Section: Individual sections and subsections
// Properties:
//   - id: UUID (unique)
//   - section_number: String (e.g., "7(1)(a)")
//   - title: String
//   - content: String
//   - level: Integer (nesting level)
//   - metadata: Map

// Regulation: Regulatory provisions and rules
// Properties:
//   - id: UUID (unique)
//   - title: String
//   - authority: String
//   - effective_date: Date
//   - status: String
//   - full_text: String
//   - metadata: Map

// Policy: Government policies and guidelines
// Properties:
//   - id: UUID (unique)
//   - title: String
//   - department: String
//   - version: String
//   - effective_date: Date
//   - metadata: Map

// Program: Government programs and services
// Properties:
//   - id: UUID (unique)
//   - name: String
//   - department: String
//   - description: String
//   - eligibility_criteria: List
//   - metadata: Map

// Situation: Applicable scenarios and use cases
// Properties:
//   - id: UUID (unique)
//   - description: String
//   - tags: List
//   - metadata: Map

// ============================================
// RELATIONSHIP TYPE DEFINITIONS
// ============================================

// HAS_SECTION: Legislation -> Section
//   Properties: order (Integer), created_at (DateTime)

// REFERENCES: Section -> Section (cross-references)
//   Properties: citation_text (String), context (String)

// AMENDED_BY: Section -> Section (amendments)
//   Properties: effective_date (Date), description (String)

// IMPLEMENTS: Regulation -> Legislation
//   Properties: description (String)

// INTERPRETS: Policy -> Legislation
//   Properties: description (String)

// APPLIES_TO: Regulation -> Program
//   Properties: description (String)

// RELEVANT_FOR: Section -> Situation
//   Properties: relevance_score (Float), description (String)

// SUPERSEDES: Legislation -> Legislation (replacements)
//   Properties: effective_date (Date), description (String)

// PART_OF: Section -> Section (parent-child hierarchy)
//   Properties: order (Integer)

// ============================================
// SCHEMA VERIFICATION QUERY
// ============================================

// Run this to verify the schema was created successfully:
// CALL db.constraints();
// CALL db.indexes();
