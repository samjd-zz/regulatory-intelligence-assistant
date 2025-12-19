#!/usr/bin/env python3
"""
Rebuild all REFERENCES relationships in Neo4j from the Citation table.

This script queries all citations from PostgreSQL and creates corresponding
REFERENCES relationships in Neo4j between Section nodes.

Usage:
    python backend/scripts/rebuild_citation_relationships.py
"""

import sys
import os
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from database import SessionLocal
from models.models import Citation, Section
from utils.neo4j_client import get_neo4j_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def rebuild_citation_relationships():
    """
    Rebuild all REFERENCES relationships in Neo4j from Citations table.
    """
    db: Session = SessionLocal()
    neo4j = get_neo4j_client()
    
    try:
        logger.info("🔄 Starting citation relationship rebuild...")
        
        # First, remove all existing REFERENCES relationships
        logger.info("🗑️  Removing existing REFERENCES relationships...")
        delete_query = """
        MATCH ()-[r:REFERENCES]->()
        DELETE r
        """
        result = neo4j.execute_query(delete_query)
        logger.info(f"✅ Removed existing REFERENCES relationships")
        
        # Query all citations
        logger.info("📊 Querying all citations from database...")
        citations = db.query(Citation).all()
        total_citations = len(citations)
        logger.info(f"📋 Found {total_citations} citations to process")
        
        if total_citations == 0:
            logger.warning("⚠️  No citations found in database")
            return
        
        # Create REFERENCES relationships
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, citation in enumerate(citations, 1):
            try:
                # Verify both sections exist in database
                source_section = db.query(Section).filter_by(id=citation.section_id).first()
                target_section = db.query(Section).filter_by(id=citation.cited_section_id).first()
                
                if not source_section or not target_section:
                    logger.debug(f"Skipping citation {i}/{total_citations}: Missing section nodes")
                    skipped_count += 1
                    continue
                
                # Create REFERENCES relationship in Neo4j
                query = """
                MATCH (source:Section {id: $source_id})
                MATCH (target:Section {id: $target_id})
                MERGE (source)-[r:REFERENCES]->(target)
                SET r.citation_text = $citation_text
                SET r.created_at = datetime()
                RETURN r
                """
                
                neo4j.execute_write(
                    query,
                    {
                        "source_id": str(citation.section_id),
                        "target_id": str(citation.cited_section_id),
                        "citation_text": citation.citation_text or ""
                    }
                )
                created_count += 1
                
                # Log progress every 1000 citations
                if i % 1000 == 0:
                    logger.info(f"Progress: {i}/{total_citations} citations processed...")
                    
            except Exception as e:
                logger.error(f"Error processing citation {i}/{total_citations}: {e}")
                error_count += 1
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 CITATION RELATIONSHIP REBUILD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total citations in database:  {total_citations}")
        logger.info(f"✅ Relationships created:      {created_count}")
        logger.info(f"⏭️  Citations skipped:          {skipped_count}")
        logger.info(f"❌ Errors encountered:         {error_count}")
        logger.info("=" * 60)
        
        if created_count > 0:
            logger.info("✅ Citation relationship rebuild completed successfully!")
        else:
            logger.warning("⚠️  No citation relationships were created")
        
    except Exception as e:
        logger.error(f"❌ Fatal error during rebuild: {e}", exc_info=True)
        raise
    finally:
        db.close()
        neo4j.close()


if __name__ == "__main__":
    try:
        rebuild_citation_relationships()
    except KeyboardInterrupt:
        logger.info("\n🛑 Rebuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Rebuild failed: {e}")
        sys.exit(1)
