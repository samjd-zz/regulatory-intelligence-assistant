# Neo4j Query Reference

Quick reference for exploring the regulatory intelligence database using the Neo4j Browser at **http://localhost:7474/browser/**

## Connection

- **URL**: http://localhost:7474/browser/
- **Username**: `neo4j`
- **Password**: `password123` (default, change in production)
- **Database**: `neo4j` (default)

---

## 📊 Database Overview

### Show Database Statistics
```cypher
// Count all nodes and relationships
MATCH (n)
RETURN count(n) AS total_nodes,
       count{MATCH ()-[r]->()} AS total_relationships
```

### Show Node Types and Counts
```cypher
// Count nodes by label
MATCH (n)
RETURN labels(n) AS node_type, count(*) AS count
ORDER BY count DESC
```

### Show Document Types (Legislation/Regulation/Policy)
```cypher
// Count regulations by node_type property
MATCH (n:Regulation)
RETURN n.node_type AS document_type, count(*) AS count
ORDER BY count DESC
```

### Show Relationship Types and Counts
```cypher
// Count relationships by type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY count DESC
```

### Show Database Schema (Visual)
```cypher
// Visualize the schema (shows virtual nodes with negative IDs)
CALL db.schema.visualization()
```

### Show Actual Data Graph
```cypher
// View real connected data (not schema)
MATCH (n)-[r]->(m)
RETURN n, r, m LIMIT 100
```

### List All Indexes
```cypher
// Show all indexes
SHOW INDEXES
```

---

## 🔍 Exploring Documents (Legislation, Regulations, Policies)

### List All Legislation (Acts/Lois)
```cypher
// Get first 25 Acts with basic info
MATCH (r:Regulation)
WHERE r.node_type = 'Legislation'
RETURN r.name, r.jurisdiction, r.effective_date, r.language
ORDER BY r.name
LIMIT 25
```

### List All Regulations (SOR/DORS)
```cypher
// Get federal regulations
MATCH (r:Regulation)
WHERE r.node_type = 'Regulation'
RETURN r.name, r.authority, r.effective_date, r.language
ORDER BY r.name
LIMIT 25
```

### List All Policies
```cypher
// Get policies, guidelines, and directives
MATCH (p:Policy)
RETURN p.name, p.jurisdiction, p.effective_date
ORDER BY p.name
```

### Find Policy Relationships
```cypher
// Find policies and the legislation they interpret
MATCH (p:Policy)-[:INTERPRETS]->(l:Regulation)
WHERE l.node_type = 'Legislation'
RETURN p.name AS policy,
       l.name AS legislation,
       l.jurisdiction
ORDER BY p.name
```

### Find Documents by Keyword
```cypher
// Search by title (case-insensitive)
MATCH (r:Regulation)
WHERE toLower(r.name) CONTAINS toLower('privacy')
RETURN r.name, r.node_type, r.jurisdiction, r.effective_date
ORDER BY r.name
```

### Legislation by Jurisdiction
```cypher
// Count Acts by jurisdiction
MATCH (r:Regulation)
WHERE r.node_type = 'Legislation'
RETURN r.jurisdiction, count(*) AS count
ORDER BY count DESC
```

### Recent Legislation
```cypher
// Find Acts by effective date
MATCH (r:Regulation)
WHERE r.node_type = 'Legislation' AND r.effective_date IS NOT NULL
RETURN r.name, r.effective_date, r.jurisdiction, r.language
ORDER BY r.effective_date DESC
LIMIT 20
```

### Find Regulations by Parent Act
```cypher
// Find regulations enacted under a specific Act
MATCH (reg:Regulation)-[:ENACTED_UNDER]->(act:Regulation)
WHERE act.name CONTAINS 'Canada Labour Code'
RETURN reg.name AS regulation,
       act.name AS parent_act
ORDER BY reg.name
```

---

## 📄 Exploring Sections

### List Sections for a Document
```cypher
// Get all sections for a specific Act
MATCH (r:Regulation)-[:HAS_SECTION]->(s:Section)
WHERE r.name CONTAINS 'Criminal Code'
RETURN s.section_number, s.title, substring(s.content, 0, 100) AS preview
ORDER BY s.section_number
LIMIT 50
```

### Search Section Content
```cypher
// Search in section content
MATCH (s:Section)
WHERE toLower(s.content) CONTAINS toLower('consent')
MATCH (r:Regulation)-[:HAS_SECTION]->(s)
RETURN r.name AS document,
       s.section_number,
       s.title,
       substring(s.content, 0, 200) + '...' AS preview
LIMIT 20
```

### Find Cross-References Between Sections
```cypher
// Find sections that reference other sections
MATCH (s1:Section)-[r:REFERENCES]->(s2:Section)
MATCH (doc1:Regulation)-[:HAS_SECTION]->(s1)
MATCH (doc2:Regulation)-[:HAS_SECTION]->(s2)
RETURN doc1.name AS from_document,
       s1.section_number AS from_section,
       doc2.name AS to_document,
       s2.section_number AS to_section
LIMIT 50
```

### Most Referenced Sections
```cypher
// Find sections with most incoming references
MATCH (s:Section)<-[r:REFERENCES]-()
WITH s, count(r) AS ref_count
WHERE ref_count > 5
MATCH (doc:Regulation)-[:HAS_SECTION]->(s)
RETURN doc.name,
       s.section_number,
       s.title,
       ref_count
ORDER BY ref_count DESC
LIMIT 20
```

---

## 🏛️ Programs and Situations

### List All Programs
```cypher
// Find all government programs
MATCH (p:Program)
RETURN p.name, p.department, p.description
ORDER BY p.department, p.name
```

### Find Programs and Their Regulations
```cypher
// Find which regulations/Acts apply to specific programs
MATCH (doc:Regulation)-[:APPLIES_TO]->(p:Program)
RETURN p.name AS program,
       p.department,
       collect(doc.name) AS applicable_regulations
ORDER BY p.department, p.name
```

### List All Situations
```cypher
// Find all legal situations extracted from regulations
MATCH (s:Situation)
RETURN s.description, s.tags
ORDER BY s.description
LIMIT 50
```

### Find Sections Relevant to a Situation
```cypher
// Find sections that address specific situations
MATCH (sec:Section)-[:RELEVANT_FOR]->(sit:Situation)
MATCH (doc:Regulation)-[:HAS_SECTION]->(sec)
WHERE toLower(sit.description) CONTAINS 'employment'
RETURN doc.name AS document,
       sec.section_number,
       sit.description AS situation
LIMIT 25
```

---

## 🔗 Relationship Exploration

### Visualize Complete Document Structure
```cypher
// See document with sections and programs
MATCH path = (doc:Regulation)-[r]->(target)
WHERE doc.name CONTAINS 'Criminal Code'
  AND type(r) IN ['HAS_SECTION', 'APPLIES_TO']
RETURN path
LIMIT 50
```

### View Policy Interpretation Structure
```cypher
// See policies and the legislation they interpret
MATCH path = (p:Policy)-[:INTERPRETS]->(l:Regulation)
RETURN path
```

### Count Sections per Document
```cypher
// How many sections does each document have?
MATCH (r:Regulation)-[:HAS_SECTION]->(s:Section)
RETURN r.name,
       r.node_type,
       count(s) AS section_count
ORDER BY section_count DESC
LIMIT 30
```

### Find All Relationship Types for a Document
```cypher
// See all relationships connected to a specific document
MATCH (doc:Regulation)-[r]-(other)
WHERE doc.name CONTAINS 'Criminal Code'
RETURN type(r) AS relationship_type,
       labels(other)[0] AS connected_to_type,
       count(*) AS count
ORDER BY count DESC
```

### Explore Document Hierarchy
```cypher
// Find regulations and their parent Acts (if ENACTED_UNDER exists)
MATCH (reg:Regulation)-[:ENACTED_UNDER]->(act:Regulation)
WHERE act.node_type = 'Legislation'
RETURN act.name AS parent_act,
       reg.name AS child_regulation
ORDER BY parent_act
LIMIT 20
```

### Find Policy Interpretation Chain
```cypher
// Trace from Policy to Legislation
MATCH (p:Policy)-[:INTERPRETS]->(l:Regulation)
WHERE l.node_type = 'Legislation'
RETURN p.name AS policy,
       l.name AS interprets_legislation
```

---

## 🔎 Advanced Analysis Queries

### Language Distribution
```cypher
// Count documents by language
MATCH (r:Regulation)
RETURN r.language, r.node_type, count(*) AS count
ORDER BY r.node_type, r.language
```

### Find Bilingual Document Pairs
```cypher
// Find English/French versions of same document
MATCH (en:Regulation), (fr:Regulation)
WHERE en.language = 'en' 
  AND fr.language = 'fr'
  AND replace(toLower(en.name), 'act', 'loi') = toLower(fr.name)
RETURN en.name AS english_title,
       fr.name AS french_title
LIMIT 20
```

### Documents with Most Programs
```cypher
// Find which documents govern the most programs
MATCH (doc:Regulation)-[:APPLIES_TO]->(p:Program)
WITH doc, count(p) AS program_count
WHERE program_count > 1
RETURN doc.name,
       doc.node_type,
       program_count
ORDER BY program_count DESC
```

### Cross-Reference Network Analysis
```cypher
// Find documents with most internal cross-references
MATCH (doc:Regulation)-[:HAS_SECTION]->(s1:Section)
MATCH (s1)-[:REFERENCES]->(s2:Section)
MATCH (doc)-[:HAS_SECTION]->(s2)
WITH doc, count(DISTINCT s1) AS referencing_sections
WHERE referencing_sections > 10
RETURN doc.name,
       doc.node_type,
       referencing_sections
ORDER BY referencing_sections DESC
LIMIT 20
```

### Content Completeness Check
```cypher
// Find sections without content
MATCH (doc:Regulation)-[:HAS_SECTION]->(s:Section)
WHERE s.content IS NULL OR s.content = ''
RETURN doc.name,
       doc.node_type,
       count(s) AS empty_sections
ORDER BY empty_sections DESC
```

### Find Orphaned Nodes
```cypher
// Find any disconnected nodes (should be 0)
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n) AS node_type, count(n) AS disconnected_count
```

---

## 📈 Analytics and Statistics

### Node Type Distribution
```cypher
// Complete breakdown of all node types
MATCH (n)
RETURN labels(n)[0] AS node_label,
       CASE 
         WHEN 'Regulation' IN labels(n) THEN n.node_type
         ELSE NULL
       END AS node_type_property,
       count(*) AS count
ORDER BY count DESC
```

### Relationship Statistics
```cypher
// Detailed relationship analysis
MATCH (source)-[r]->(target)
RETURN labels(source)[0] AS from_type,
       type(r) AS relationship,
       labels(target)[0] AS to_type,
       count(*) AS count
ORDER BY count DESC
```

### Document Size Analysis
```cypher
// Analyze document sizes by section count
MATCH (doc:Regulation)-[:HAS_SECTION]->(s:Section)
WITH doc, count(s) AS section_count
RETURN doc.node_type AS document_type,
       min(section_count) AS min_sections,
       max(section_count) AS max_sections,
       round(avg(section_count)) AS avg_sections,
       count(doc) AS document_count
ORDER BY document_type
```

### Program Coverage by Department
```cypher
// See which departments have most programs
MATCH (p:Program)
RETURN p.department,
       count(p) AS program_count
ORDER BY program_count DESC
```

### Graph Connectivity Health Check
```cypher
// Verify all major nodes are connected
MATCH (n)
WITH labels(n)[0] AS node_type,
     count(n) AS total,
     count{(n)-[]-()) AS connected
RETURN node_type,
       total,
       connected,
       total - connected AS disconnected,
       round(100.0 * connected / total, 2) AS connectivity_pct
ORDER BY total DESC
```

---

## 🛠️ Maintenance and Cleanup

### Clear Entire Database (USE WITH CAUTION!)
```cypher
// ⚠️ WARNING: Deletes ALL data!
MATCH (n)
DETACH DELETE n
RETURN 'Database cleared' AS status
```

### Delete Specific Document and Its Sections
```cypher
// Delete a document and all its sections
MATCH (doc:Regulation)
WHERE doc.name CONTAINS 'TEST'
OPTIONAL MATCH (doc)-[r:HAS_SECTION]->(s:Section)
DETACH DELETE doc, s
RETURN 'Document deleted' AS status
```

### Update Document Properties
```cypher
// Update metadata for a document
MATCH (doc:Regulation)
WHERE doc.name CONTAINS 'Privacy Act'
SET doc.last_updated = datetime(),
    doc.notes = 'Updated metadata'
RETURN doc.name, doc.last_updated
```

### Find and Fix Missing Names
```cypher
// Find documents without name property
MATCH (r:Regulation)
WHERE r.name IS NULL OR r.name = ''
RETURN r.title, labels(r)
LIMIT 10
```

### Verify Data Integrity
```cypher
// Check for sections without parent documents
MATCH (s:Section)
WHERE NOT EXISTS {
  MATCH (doc)-[:HAS_SECTION]->(s)
}
RETURN count(s) AS orphaned_sections
```

---

## 🎯 Common Use Cases

### Find All Privacy-Related Content
```cypher
// Search for privacy across all documents
MATCH (doc:Regulation)-[:HAS_SECTION]->(s:Section)
WHERE toLower(s.content) CONTAINS 'privacy'
   OR toLower(s.content) CONTAINS 'personal information'
   OR toLower(doc.name) CONTAINS 'privacy'
RETURN doc.name,
       doc.node_type,
       s.section_number,
       s.title
LIMIT 50
```

### Compliance Check: Employment Standards
```cypher
// Find all employment-related regulations
MATCH (doc:Regulation)
WHERE toLower(doc.name) CONTAINS 'employment'
   OR toLower(doc.name) CONTAINS 'labour'
   OR toLower(doc.name) CONTAINS 'labor'
OPTIONAL MATCH (doc)-[:HAS_SECTION]->(s:Section)
RETURN doc.name,
       doc.node_type,
       count(s) AS section_count
ORDER BY doc.name
```

### Find Programs for a Department
```cypher
// Get all programs administered by a department
MATCH (p:Program)
WHERE toLower(p.department) CONTAINS 'employment'
OPTIONAL MATCH (doc:Regulation)-[:APPLIES_TO]->(p)
RETURN p.name AS program,
       p.description,
       collect(doc.name) AS governing_regulations
ORDER BY p.name
```

### Cross-Jurisdiction Analysis
```cypher
// Compare similar legislation across jurisdictions
MATCH (doc:Regulation)
WHERE doc.node_type = 'Legislation'
  AND toLower(doc.name) CONTAINS 'human rights'
RETURN doc.jurisdiction,
       doc.name,
       doc.language
ORDER BY doc.jurisdiction, doc.language
```

### Find Sections Citing Specific Terms
```cypher
// Find all sections mentioning specific legal terms
MATCH (doc:Regulation)-[:HAS_SECTION]->(s:Section)
WHERE toLower(s.content) CONTAINS 'reasonable person'
   OR toLower(s.content) CONTAINS 'due diligence'
   OR toLower(s.content) CONTAINS 'good faith'
RETURN doc.name,
       s.section_number,
       s.title,
       substring(s.content, 0, 150) + '...' AS snippet
LIMIT 30
```

---

## 💡 Tips for Neo4j Browser

### Best Practices
- **Limit results**: Always add `LIMIT 25-100` to avoid overwhelming visualizations
- **Use properties**: Access `r.name` instead of relying on visual labels
- **Filter early**: Add `WHERE` clauses before collecting or aggregating
- **Real data vs schema**: `db.schema.visualization()` shows schema (negative IDs), use `MATCH (n)-[r]->(m) RETURN * LIMIT 100` for real data

### Visualization Controls
- **Style nodes**: Click node labels in bottom panel to customize colors and sizes
- **Expand nodes**: Double-click nodes to show their connections
- **Pan/Zoom**: Mouse wheel to zoom, drag to pan
- **Node labels**: Configure which property shows as label (use `name` property)

### Query Performance
- **Use node labels**: `MATCH (r:Regulation)` is faster than `MATCH (r)`
- **Add WHERE early**: Filter before traversing relationships
- **Profile queries**: Add `PROFILE` to see execution plan
- **Explain queries**: Add `EXPLAIN` to see query plan without executing

### Example: Profile a Query
```cypher
PROFILE
MATCH (doc:Regulation)-[:HAS_SECTION]->(s:Section)
WHERE doc.node_type = 'Legislation'
RETURN doc.name, count(s) AS section_count
ORDER BY section_count DESC
LIMIT 20
```

### Save and Export
- **Favorites**: Click star icon ⭐ to save frequently used queries
- **Export**: Use download icon to export as CSV or JSON
- **History**: Access recent queries from history tab
- **Frames**: Pin result frames to keep them visible

---

## 📚 Additional Resources

- **Neo4j Cypher Manual**: https://neo4j.com/docs/cypher-manual/current/
- **Cypher Cheat Sheet**: https://neo4j.com/docs/cypher-refcard/current/
- **Graph Data Science**: https://neo4j.com/docs/graph-data-science/current/
- **Neo4j Python Driver**: https://neo4j.com/docs/api/python-driver/current/

---

## 🏗️ Knowledge Graph Architecture

### Node Types
- **Regulation** (with node_type property):
  - `Legislation`: Acts/Lois (1,815 nodes)
  - `Regulation`: SOR/DORS (254 nodes)
  - `Policy`: Guidelines, Directives (2 nodes)
- **Section**: Individual sections within documents (300,331 nodes)
- **Program**: Government programs (94 nodes)
- **Situation**: Legal situations/scenarios (931 nodes)

### Relationships
- **HAS_SECTION**: Document → Section (300,331)
- **REFERENCES**: Section → Section cross-references (30,171)
- **RELEVANT_FOR**: Section → Situation (931)
- **APPLIES_TO**: Document/Program → Program/Document (94)
- **ENACTED_UNDER**: Regulation → Parent Act (7)
- **INTERPRETS**: Policy → Legislation (7)

---

## 🔒 Security Notes

- Never run `DETACH DELETE` queries without `WHERE` clauses
- Always test on small dataset first using `LIMIT`
- Back up data before running maintenance queries
- Use read-only credentials for exploration in production
- Schema visualization shows virtual nodes (negative IDs) - not real data

---

**Last Updated**: December 20, 2025 - v2.0  
**Graph Stats**: 303,427 nodes | 331,534 relationships | 2,071 documents
