#!/usr/bin/env python3
"""
Migration script to add node_type property to existing Neo4j Regulation nodes.

This script updates all existing Regulation nodes in Neo4j with the correct
node_type property based on their title:
- Titles containing "Act" or "Loi" → node_type = "Legislation"
- Everything else → node_type = "Regulation"

The node_type property enables filtering in Elasticsearch and maintains
consistency across PostgreSQL, Neo4j, and Elasticsearch.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def determine_node_type(title: str) -> str:
    """
    Determine node_type based on title.
    
    Args:
        title: Regulation title
        
    Returns:
        'Legislation' if it's an Act/Loi, otherwise 'Regulation'
    """
    title_lower = title.lower()
    
    # Acts and Lois (French for laws) are considered Legislation
    if ' act' in title_lower or title_lower.startswith('act ') or title_lower.endswith(' act'):
        return 'Legislation'
    if ' loi' in title_lower or title_lower.startswith('loi ') or title_lower.endswith(' loi'):
        return 'Legislation'
    
    # Everything else is a Regulation
    return 'Regulation'


def migrate_node_types():
    """
    Add node_type property to all existing Regulation nodes in Neo4j.
    """
    # Get Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        logger.error("NEO4J_PASSWORD environment variable not set")
        sys.exit(1)
    
    logger.info(f"Connecting to Neo4j at {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            # Get all Regulation nodes without node_type
            logger.info("Fetching Regulation nodes...")
            result = session.run("""
                MATCH (r:Regulation)
                WHERE r.node_type IS NULL
                RETURN r.id as id, r.title as title
            """)
            
            nodes = list(result)
            total = len(nodes)
            logger.info(f"Found {total} nodes without node_type property")
            
            if total == 0:
                logger.info("All nodes already have node_type set!")
                return
            
            # Update nodes in batches
            legislation_count = 0
            regulation_count = 0
            batch_size = 100
            
            for i in range(0, total, batch_size):
                batch = nodes[i:i+batch_size]
                
                # Prepare updates
                updates = []
                for node in batch:
                    node_id = node['id']
                    title = node['title']
                    node_type = determine_node_type(title)
                    updates.append({'id': node_id, 'node_type': node_type})
                    
                    if node_type == 'Legislation':
                        legislation_count += 1
                    else:
                        regulation_count += 1
                
                # Execute batch update
                session.run("""
                    UNWIND $updates as update
                    MATCH (r:Regulation {id: update.id})
                    SET r.node_type = update.node_type
                """, updates=updates)
                
                logger.info(f"Updated {min(i+batch_size, total)}/{total} nodes...")
            
            logger.info(f"\nMigration complete!")
            logger.info(f"  Legislation nodes: {legislation_count}")
            logger.info(f"  Regulation nodes: {regulation_count}")
            logger.info(f"  Total updated: {total}")
            
            # Verify counts
            result = session.run("""
                MATCH (r:Regulation)
                WHERE r.node_type = 'Legislation'
                RETURN count(r) as count
            """)
            leg_count = result.single()['count']
            
            result = session.run("""
                MATCH (r:Regulation)
                WHERE r.node_type = 'Regulation'
                RETURN count(r) as count
            """)
            reg_count = result.single()['count']
            
            logger.info(f"\nVerification:")
            logger.info(f"  Legislation nodes in Neo4j: {leg_count}")
            logger.info(f"  Regulation nodes in Neo4j: {reg_count}")
            
    finally:
        driver.close()
        logger.info("Connection closed")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Neo4j node_type Migration Script")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        migrate_node_types()
        logger.info("\n✓ Migration successful!")
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
