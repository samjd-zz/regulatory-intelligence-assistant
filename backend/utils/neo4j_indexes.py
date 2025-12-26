"""
Neo4j index and constraint setup utilities.
Shared by populate_graph.py and data_pipeline.py to ensure consistency.
"""
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


def setup_neo4j_constraints(neo4j: 'Neo4jClient'):
    """
    Create Neo4j constraints and indexes.
    
    This function creates all necessary indexes for optimal query performance:
    - Unique constraints on node IDs
    - Property indexes for filtering
    - Relationship indexes for graph traversal
    - Full-text indexes for search
    
    Args:
        neo4j: Neo4j client instance
    """
    logger.info("Setting up Neo4j constraints and indexes...")
    
    constraints = [
        "CREATE CONSTRAINT legislation_id IF NOT EXISTS FOR (l:Legislation) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT regulation_id IF NOT EXISTS FOR (r:Regulation) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT program_id IF NOT EXISTS FOR (prog:Program) REQUIRE prog.id IS UNIQUE",
        "CREATE CONSTRAINT situation_id IF NOT EXISTS FOR (sit:Situation) REQUIRE sit.id IS UNIQUE",
        "CREATE CONSTRAINT amendment_id IF NOT EXISTS FOR (a:Amendment) REQUIRE a.id IS UNIQUE",
    ]
    
    # Property indexes for fast filtering (from optimize_neo4j_indexes.cypher)
    indexes = [
        # Basic property indexes
        "CREATE INDEX legislation_title IF NOT EXISTS FOR (l:Legislation) ON (l.title)",
        "CREATE INDEX legislation_jurisdiction IF NOT EXISTS FOR (l:Legislation) ON (l.jurisdiction)",
        "CREATE INDEX legislation_status IF NOT EXISTS FOR (l:Legislation) ON (l.status)",
        "CREATE INDEX legislation_language IF NOT EXISTS FOR (l:Legislation) ON (l.language)",
        "CREATE INDEX section_number IF NOT EXISTS FOR (s:Section) ON (s.section_number)",
        "CREATE INDEX program_name IF NOT EXISTS FOR (p:Program) ON (p.name)",
        
        # Composite indexes for common query patterns (VERY IMPORTANT)
        "CREATE INDEX legislation_jurisdiction_status IF NOT EXISTS FOR (l:Legislation) ON (l.jurisdiction, l.status)",
    ]
    
    # Relationship indexes (CRITICAL for graph traversal performance)
    relationship_indexes = [
        # HAS_SECTION relationships (most common traversal)
        "CREATE INDEX has_section_rel_idx IF NOT EXISTS FOR ()-[r:HAS_SECTION]-() ON (r.order)",
        
        # REFERENCES relationships (cross-reference discovery)
        "CREATE INDEX references_rel_idx IF NOT EXISTS FOR ()-[r:REFERENCES]-() ON (r.citation_text)",
        
        # AMENDED_BY relationships (version tracking)
        "CREATE INDEX amended_by_rel_idx IF NOT EXISTS FOR ()-[r:AMENDED_BY]-() ON (r.effective_date)",
    ]
    
    # Full-text indexes with optimization options (from optimize_neo4j_indexes.cypher)
    fulltext_indexes = [
        """
        CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
        FOR (l:Legislation) ON EACH [l.title, l.full_text]
        OPTIONS {
          indexConfig: {
            `fulltext.analyzer`: 'standard-no-stop-words',
            `fulltext.eventually_consistent`: true
          }
        }
        """,
        """
        CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS
        FOR (r:Regulation) ON EACH [r.title, r.full_text]
        OPTIONS {
          indexConfig: {
            `fulltext.analyzer`: 'standard-no-stop-words',
            `fulltext.eventually_consistent`: true
          }
        }
        """,
        """
        CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
        FOR (s:Section) ON EACH [s.title, s.content]
        OPTIONS {
          indexConfig: {
            `fulltext.analyzer`: 'standard-no-stop-words',
            `fulltext.eventually_consistent`: true
          }
        }
        """
    ]
    
    # Execute all index and constraint creation queries
    all_queries = constraints + indexes + relationship_indexes + fulltext_indexes
    
    for query in all_queries:
        try:
            # Clean up multiline queries for logging
            clean_query = ' '.join(line.strip() for line in query.split('\n') if line.strip())
            neo4j.execute_write(query)
            logger.info(f"✓ Executed: {clean_query[:80]}...")
        except Exception as e:
            # Some indexes may already exist from previous runs
            if "already exists" in str(e) or "Equivalent" in str(e):
                logger.debug(f"Index/constraint already exists (OK)")
            else:
                logger.warning(f"Could not create index/constraint: {e}")
    
    logger.info(f"✓ Created {len(constraints)} constraints, {len(indexes)} property indexes, "
                f"{len(relationship_indexes)} relationship indexes, {len(fulltext_indexes)} fulltext indexes")
