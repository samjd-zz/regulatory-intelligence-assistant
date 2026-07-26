#!/usr/bin/env python3
"""
Simple script to initialize Neo4j schema with fulltext indexes.
Run this script after starting the Neo4j container.

Usage:
    python initialize_neo4j_schema.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import logging
from utils.neo4j_client import get_neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_fulltext_indexes():
    """Create the required fulltext indexes."""
    logger.info("Creating Neo4j fulltext indexes...")
    
    client = get_neo4j_client()
    
    # Check connectivity first
    if not client.verify_connectivity():
        logger.error("Cannot connect to Neo4j. Make sure Neo4j is running.")
        return False
    
    # Fulltext indexes required by the graph service
    fulltext_indexes = [
        """
        CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
        FOR (l:Legislation) ON EACH [l.title, l.full_text]
        """,
        """
        CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
        FOR (s:Section) ON EACH [s.title, s.content]
        """,
        """
        CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS
        FOR (r:Regulation) ON EACH [r.title, r.full_text]
        """
    ]
    
    success_count = 0
    
    for index_query in fulltext_indexes:
        try:
            clean_query = ' '.join(line.strip() for line in index_query.split('\\n') if line.strip())
            client.execute_write(clean_query)
            logger.info(f"Created index: {clean_query[:50]}...")
            success_count += 1
        except Exception as e:
            if "already exists" in str(e) or "An equivalent" in str(e):
                logger.info(f"Index already exists: {clean_query[:50]}...")
                success_count += 1
            else:
                logger.error(f"Failed to create index: {e}")
                logger.debug(f"Query: {clean_query}")
    
    logger.info(f"✅ Successfully created/verified {success_count}/{len(fulltext_indexes)} fulltext indexes")
    return success_count == len(fulltext_indexes)


def verify_indexes():
    """Verify that fulltext indexes exist."""
    logger.info("Verifying fulltext indexes...")
    
    client = get_neo4j_client()
    
    try:
        # Check for fulltext indexes
        indexes = client.execute_query("SHOW INDEXES")
        fulltext_indexes = [idx for idx in indexes if idx.get('type') == 'FULLTEXT']
        
        required_indexes = ['legislation_fulltext', 'section_fulltext']
        found_indexes = [idx['name'] for idx in fulltext_indexes]
        
        logger.info(f"Found fulltext indexes: {found_indexes}")
        
        missing_indexes = [idx for idx in required_indexes if idx not in found_indexes]
        if missing_indexes:
            logger.warning(f"Missing required indexes: {missing_indexes}")
            return False
        else:
            logger.info("✅ All required fulltext indexes are present")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying indexes: {e}")
        return False


def main():
    """Main function."""
    logger.info("🚀 Initializing Neo4j Schema for Regulatory Intelligence Assistant")
    
    # Create fulltext indexes
    if not create_fulltext_indexes():
        logger.error("❌ Failed to create fulltext indexes")
        return 1
    
    # Verify indexes were created
    if not verify_indexes():
        logger.error("❌ Index verification failed")
        return 1
    
    logger.info("🎉 Neo4j schema initialization complete!")
    logger.info("The graph service should now work correctly with fulltext search.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())