# Neo4j Query Reference

Quick reference for exploring the regulatory intelligence database using the Neo4j Browser at **http://localhost:7474/browser/**

## Connection

- **URL**: http://localhost:7474/browser/
- **Username**: `neo4j`
- **Password**: `your_neo4j_password` (from docker-compose.yml or .env)
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

### Show Relationship Types and Counts
```cypher
// Count relationships by type
MATCH ()-[r]->()
RETURN type(r) AS relationship_type, count(*) AS count
ORDER BY count DESC
```

### Show Database Schema
```cypher
// Visualize the schema
CALL db.schema.visualization()
```

### List All Indexes
```cypher
// Show all indexes
SHOW INDEXES
```

---

## 🔍 Exploring Regulations

### List All Regulations
```cypher
// Get first 25 regulations with basic info
MATCH (r:Regulation)
RETURN r.regulation_id, r.title, r.effective_date, r.jurisdiction
ORDER BY r.title
LIMIT 25
```

### Find Regulations by Keyword
```cypher
// Search regulations by title (case-insensitive)
MATCH (r:Regulation)
WHERE toLower(r.title) CONTAINS toLower('privacy')
RETURN r.regulation_id, r.title, r.jurisdiction, r.effective_date
ORDER BY r.title
```

### Get Regulation Details
```cypher
// Get full details for a specific regulation
MATCH (r:Regulation {regulation_id: 'PIPEDA'})
RETURN r
```

### Regulations by Jurisdiction
```cypher
// Count regulations by jurisdiction
MATCH (r:Regulation)
RETURN r.jurisdiction, count(*) AS count
ORDER BY count DESC
```

### Recent Regulations
```cypher
// Find regulations by effective date
MATCH (r:Regulation)
WHERE r.effective_date IS NOT NULL
RETURN r.regulation_id, r.title, r.effective_date, r.jurisdiction
ORDER BY r.effective_date DESC
LIMIT 20
```

---

## 📄 Exploring Sections

### List Sections for a Regulation
```cypher
// Get all sections for a specific regulation
MATCH (r:Regulation {regulation_id: 'PIPEDA'})-[:HAS_SECTION]->(s:Section)
RETURN s.section_number, s.title, s.citation
ORDER BY s.section_number
LIMIT 50
```

### Search Section Content
```cypher
// Full-text search in section content
CALL db.index.fulltext.queryNodes('section_content_index', 'data breach notification')
YIELD node, score
RETURN node.section_number, node.title, node.citation, score
ORDER BY score DESC
LIMIT 20
```

### Search Section Titles
```cypher
// Full-text search in section titles
CALL db.index.fulltext.queryNodes('section_title_index', 'consent')
YIELD node, score
MATCH (r:Regulation)-[:HAS_SECTION]->(node)
RETURN r.regulation_id, node.section_number, node.title, score
ORDER BY score DESC
LIMIT 20
```

### Get Section with Full Content
```cypher
// Get complete section details
MATCH (s:Section {citation: 'PIPEDA Section 4.3'})
RETURN s.section_number, s.title, s.content, s.citation
```

### Sections by Keyword in Content
```cypher
// Find sections containing specific keywords
MATCH (s:Section)
WHERE toLower(s.content) CONTAINS toLower('personal information')
MATCH (r:Regulation)-[:HAS_SECTION]->(s)
RETURN r.regulation_id, s.section_number, s.title, s.citation
LIMIT 25
```

---

## 🔗 Relationship Queries

### Show Regulation-Section Structure
```cypher
// Visualize regulation and its sections
MATCH path = (r:Regulation {regulation_id: 'PIPEDA'})-[:HAS_SECTION]->(s:Section)
RETURN path
LIMIT 25
```

### Count Sections per Regulation
```cypher
// How many sections does each regulation have?
MATCH (r:Regulation)-[:HAS_SECTION]->(s:Section)
RETURN r.regulation_id, r.title, count(s) AS section_count
ORDER BY section_count DESC
```

### Find Cross-References
```cypher
// Find sections that reference other sections
MATCH (s1:Section)-[rel:REFERENCES|CITES]->(s2:Section)
RETURN s1.citation, type(rel), s2.citation
LIMIT 50
```

### Find Related Sections (if similarity relationships exist)
```cypher
// Find sections similar to a given section
MATCH (s1:Section {citation: 'PIPEDA Section 4.3'})-[rel:SIMILAR_TO]->(s2:Section)
RETURN s1.citation, s2.citation, rel.score
ORDER BY rel.score DESC
LIMIT 10
```

---

## 🔎 Advanced Search Queries

### Multi-Term Full-Text Search
```cypher
// Search with multiple terms
CALL db.index.fulltext.queryNodes('section_content_index', 'privacy AND consent AND collection')
YIELD node, score
MATCH (r:Regulation)-[:HAS_SECTION]->(node)
RETURN r.regulation_id, node.section_number, node.title, node.citation, score
ORDER BY score DESC
LIMIT 20
```

### Fuzzy Search (Approximate Matching)
```cypher
// Fuzzy search with ~1 character difference
CALL db.index.fulltext.queryNodes('section_content_index', 'privasy~1')
YIELD node, score
RETURN node.citation, node.title, score
ORDER BY score DESC
LIMIT 10
```

### Search Across Multiple Fields
```cypher
// Search in both title and content
CALL db.index.fulltext.queryNodes('section_title_index', 'security breach')
YIELD node AS title_match, score AS title_score
WITH collect({node: title_match, score: title_score}) AS title_matches

CALL db.index.fulltext.queryNodes('section_content_index', 'security breach')
YIELD node AS content_match, score AS content_score
WITH title_matches, collect({node: content_match, score: content_score}) AS content_matches

UNWIND title_matches + content_matches AS result
RETURN DISTINCT result.node.citation, result.node.title, result.score
ORDER BY result.score DESC
LIMIT 20
```

### Find Sections with Specific Properties
```cypher
// Find sections with certain characteristics
MATCH (s:Section)
WHERE s.content IS NOT NULL 
  AND size(s.content) > 1000
MATCH (r:Regulation)-[:HAS_SECTION]->(s)
RETURN r.regulation_id, s.citation, size(s.content) AS content_length
ORDER BY content_length DESC
LIMIT 20
```

---

## 📈 Analytics Queries

### Most Referenced Sections
```cypher
// Find sections with most incoming references
MATCH (s:Section)<-[r:REFERENCES|CITES]-()
WITH s, count(r) AS ref_count
WHERE ref_count > 0
RETURN s.citation, s.title, ref_count
ORDER BY ref_count DESC
LIMIT 20
```

### Regulation Coverage Analysis
```cypher
// Analyze data completeness
MATCH (r:Regulation)
OPTIONAL MATCH (r)-[:HAS_SECTION]->(s:Section)
RETURN r.regulation_id,
       r.title,
       count(s) AS section_count,
       count(s.content) AS sections_with_content,
       round(100.0 * count(s.content) / count(s), 2) AS completeness_pct
ORDER BY section_count DESC
```

### Content Size Distribution
```cypher
// Analyze section content sizes
MATCH (s:Section)
WHERE s.content IS NOT NULL
WITH size(s.content) AS content_size
RETURN 
  min(content_size) AS min_size,
  max(content_size) AS max_size,
  round(avg(content_size)) AS avg_size,
  percentileCont(content_size, 0.5) AS median_size
```

### Find Orphaned Nodes
```cypher
// Find sections not connected to any regulation
MATCH (s:Section)
WHERE NOT exists((s)<-[:HAS_SECTION]-(:Regulation))
RETURN s.citation, s.title
LIMIT 20
```

---

## 🛠️ Maintenance Queries

### Delete a Specific Regulation and Its Sections
```cypher
// ⚠️ WARNING: This deletes data permanently!
MATCH (r:Regulation {regulation_id: 'TEST_REG'})
OPTIONAL MATCH (r)-[rel:HAS_SECTION]->(s:Section)
DELETE r, rel, s
RETURN 'Deleted' AS status
```

### Delete All Test Data
```cypher
// ⚠️ WARNING: Deletes all test/sample data
MATCH (n)
WHERE n.regulation_id STARTS WITH 'TEST_' 
   OR n.citation STARTS WITH 'TEST_'
DETACH DELETE n
RETURN 'Test data deleted' AS status
```

### Update Regulation Metadata
```cypher
// Update a regulation's properties
MATCH (r:Regulation {regulation_id: 'PIPEDA'})
SET r.last_updated = datetime(),
    r.notes = 'Updated metadata'
RETURN r
```

### Find Duplicate Sections
```cypher
// Find sections with duplicate citations
MATCH (s:Section)
WITH s.citation AS citation, collect(s) AS sections
WHERE size(sections) > 1
RETURN citation, size(sections) AS duplicate_count
ORDER BY duplicate_count DESC
```

---

## 🎯 Use Case Examples

### Compliance Check: Find All Privacy-Related Sections
```cypher
// Find all sections related to privacy across regulations
CALL db.index.fulltext.queryNodes('section_content_index', 
  'privacy OR "personal information" OR "data protection"')
YIELD node, score
MATCH (r:Regulation)-[:HAS_SECTION]->(node)
WHERE score > 1.0
RETURN r.regulation_id, 
       r.jurisdiction,
       node.citation, 
       node.title,
       round(score, 2) AS relevance_score
ORDER BY score DESC
LIMIT 50
```

### Audit Trail: Find Consent Requirements
```cypher
// Find all sections about consent requirements
CALL db.index.fulltext.queryNodes('section_content_index', 
  'consent AND (obtain OR required OR mandatory)')
YIELD node, score
MATCH (r:Regulation)-[:HAS_SECTION]->(node)
RETURN r.regulation_id,
       r.title,
       node.section_number,
       node.title AS section_title,
       node.citation
ORDER BY score DESC
LIMIT 30
```

### Gap Analysis: Compare Regulations
```cypher
// Find regulations covering similar topics
MATCH (r1:Regulation)-[:HAS_SECTION]->(s1:Section)
WHERE toLower(s1.title) CONTAINS 'breach notification'
WITH collect(DISTINCT r1.regulation_id) AS regs_with_breach
MATCH (r:Regulation)
RETURN r.regulation_id,
       r.title,
       r.jurisdiction,
       CASE WHEN r.regulation_id IN regs_with_breach 
            THEN 'Has Breach Notification' 
            ELSE 'Missing' 
       END AS coverage
ORDER BY r.jurisdiction, r.title
```

---

## 💡 Tips for Neo4j Browser

### Visualization Settings
- **Limit results**: Add `LIMIT 25` to avoid overwhelming visualizations
- **Style nodes**: Click on node labels in the bottom panel to customize colors
- **Expand nodes**: Double-click nodes to see their connections
- **Pan/Zoom**: Use mouse wheel to zoom, drag to pan

### Query Performance
- **Use indexes**: The database has fulltext indexes on section_content and section_title
- **Profile queries**: Prefix with `PROFILE` to see execution plan
- **Explain queries**: Prefix with `EXPLAIN` to see query plan without executing

### Example: Profile a Query
```cypher
PROFILE
MATCH (r:Regulation)-[:HAS_SECTION]->(s:Section)
WHERE toLower(s.title) CONTAINS 'privacy'
RETURN r.regulation_id, count(s) AS section_count
ORDER BY section_count DESC
```

### Save Favorites
- Click the star icon ⭐ in the query editor to save frequently used queries
- Access saved queries from the "Favorites" tab

### Export Results
- Use the download icon to export results as CSV or JSON
- For programmatic access, use the REST API or Python driver

---

## 📚 Additional Resources

- **Neo4j Cypher Documentation**: https://neo4j.com/docs/cypher-manual/current/
- **Full-Text Search Syntax**: https://neo4j.com/docs/cypher-manual/current/indexes-for-full-text-search/
- **Graph Data Science**: https://neo4j.com/docs/graph-data-science/current/

---

## 🔒 Security Notes

- Never run `DELETE` queries without `WHERE` clauses in production
- Always test queries on a small subset first using `LIMIT`
- Back up data before running maintenance queries
- Use read-only credentials for exploration in production environments

---

**Last Updated**: v1.3.7 - December 2025
