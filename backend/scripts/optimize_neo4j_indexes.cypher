// ============================================
// Neo4j Index Optimization for Multi-Tier RAG Search
// Phase 4.2: Optimize Neo4j Queries for Tier 3 Fallback
// ============================================
//
// Purpose: Optimize Neo4j for fast full-text search and graph traversal
// in the multi-tier RAG system (Tier 3 fallback).
//
// Usage:
//   docker exec -it regulatory-neo4j cypher-shell -u neo4j -p password123 < backend/scripts/optimize_neo4j_indexes.cypher
//   OR
//   cat backend/scripts/optimize_neo4j_indexes.cypher | docker exec -i regulatory-neo4j cypher-shell -u neo4j -p password123
//
// Requirements:
//   - Neo4j 5.15+ (current: 5.15-community)
//   - Database must be running and healthy
//   - Sufficient memory for index creation (configured: 2GB heap, 512MB pagecache)
//
// Performance Impact:
//   - Initial index creation: 1-5 minutes (depending on data size)
//   - Query performance improvement: 10-100x faster
//   - Storage overhead: ~10-20% of data size
//
// ============================================

// ============================================
// STEP 1: FULL-TEXT SEARCH INDEXES
// (Required for Tier 3 semantic search)
// ============================================

// Full-text index for Legislation nodes
// Searches across title and full_text fields with weighted relevance
CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
FOR (l:Legislation)
ON EACH [l.title, l.full_text]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'standard-no-stop-words',
    `fulltext.eventually_consistent`: true
  }
};

// Full-text index for Section nodes
// Searches across title and content fields
CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
FOR (s:Section)
ON EACH [s.title, s.content]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'standard-no-stop-words',
    `fulltext.eventually_consistent`: true
  }
};

// Full-text index for Regulation nodes
CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS
FOR (r:Regulation)
ON EACH [r.title, r.full_text]
OPTIONS {
  indexConfig: {
    `fulltext.analyzer`: 'standard-no-stop-words',
    `fulltext.eventually_consistent`: true
  }
};

// ============================================
// STEP 2: PROPERTY INDEXES FOR FAST FILTERING
// (Optimize common query patterns)
// ============================================

// Index on section_number for fast section lookup
CREATE INDEX section_number_idx IF NOT EXISTS
FOR (s:Section)
ON (s.section_number);

// Index on jurisdiction for geographic filtering
CREATE INDEX legislation_jurisdiction_idx IF NOT EXISTS
FOR (l:Legislation)
ON (l.jurisdiction);

// Index on status for active/inactive filtering
CREATE INDEX legislation_status_idx IF NOT EXISTS
FOR (l:Legislation)
ON (l.status);

// Index on language for bilingual support
CREATE INDEX legislation_language_idx IF NOT EXISTS
FOR (l:Legislation)
ON (l.language);

// Composite index for common filter combinations
CREATE INDEX legislation_jurisdiction_status_idx IF NOT EXISTS
FOR (l:Legislation)
ON (l.jurisdiction, l.status);

// ============================================
// STEP 3: RELATIONSHIP INDEXES
// (Optimize graph traversal for Tier 3)
// ============================================

// Index for HAS_SECTION relationships (most common traversal)
CREATE INDEX has_section_rel_idx IF NOT EXISTS
FOR ()-[r:HAS_SECTION]-()
ON (r.order);

// Index for REFERENCES relationships (cross-reference discovery)
CREATE INDEX references_rel_idx IF NOT EXISTS
FOR ()-[r:REFERENCES]-()
ON (r.citation_text);

// Index for AMENDED_BY relationships (version tracking)
CREATE INDEX amended_by_rel_idx IF NOT EXISTS
FOR ()-[r:AMENDED_BY]-()
ON (r.effective_date);

// ============================================
// STEP 4: CONSTRAINT VERIFICATION
// (Ensure data integrity for RAG system)
// ============================================

// Verify unique constraints exist (should already be created by init_graph.cypher)
// These are critical for preventing duplicate nodes in the knowledge graph

CREATE CONSTRAINT legislation_id IF NOT EXISTS
FOR (l:Legislation) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT section_id IF NOT EXISTS
FOR (s:Section) REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT regulation_id IF NOT EXISTS
FOR (r:Regulation) REQUIRE r.id IS UNIQUE;

// ============================================
// NOTES AND RECOMMENDATIONS
// ============================================
//
// 1. Index Creation Time:
//    - Small datasets (<10k nodes): 1-2 minutes
//    - Medium datasets (10k-100k nodes): 2-5 minutes
//    - Large datasets (>100k nodes): 5-10 minutes
//
// 2. Memory Requirements:
//    - Ensure Neo4j has at least 2GB heap memory
//    - Increase page cache for large datasets
//    - Already configured in docker-compose.yml:
//      NEO4J_server_memory_heap_initial__size=512m
//      NEO4J_server_memory_heap_max__size=2G
//      NEO4J_server_memory_pagecache_size=512m
//
// 3. Monitoring (Neo4j 5.15+ syntax):
//    - Check index status: SHOW INDEXES;
//    - Check constraints: SHOW CONSTRAINTS;
//    - Check query performance: PROFILE <query>
//    - Monitor memory usage: CALL dbms.listConfig();
//
// 4. Verification Commands (run separately after this script):
//    - SHOW INDEXES;
//    - SHOW CONSTRAINTS;
//    - MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count ORDER BY Count DESC;
//    - MATCH ()-[r]->() RETURN type(r) as RelationType, count(r) as Count ORDER BY Count DESC;
//
// 5. Maintenance:
//    - Indexes are automatically maintained
//    - No periodic rebuilding needed
//    - If corruption occurs, use: DROP INDEX <name>; then re-create
//
// 6. Troubleshooting:
//    - If indexes fail to create: check Neo4j logs
//    - If queries are slow: use PROFILE to analyze
//    - If out of memory: increase heap size
//
// ============================================
// END OF OPTIMIZATION SCRIPT
// ============================================
