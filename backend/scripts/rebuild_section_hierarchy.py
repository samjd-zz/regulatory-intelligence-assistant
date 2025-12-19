#!/usr/bin/env python3
"""
Rebuild all PART_OF relationships in Neo4j for section hierarchies.

This script queries sections with parent_number from PostgreSQL and creates
corresponding PART_OF relationships in Neo4j between Section nodes.

Usage:
    python backend/scripts/rebuild_section_hierarchy.py
"""

import sys
import os
import logging
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.orm import Session
from sqlalchemy import and_
from database import SessionLocal
from models.models import Section
from utils.neo4j_client import get_neo4j_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def rebuild_section_hierarchy():
    """
    Rebuild all PART_OF relationships in Neo4j from sections with parent_number.
    """
    db: Session = SessionLocal()
    neo4j = get_neo4j_client()
    
    try:
        logger.info("🔄 Starting section hierarchy rebuild...")
        
        # First, remove all existing PART_OF relationships
        logger.info("🗑️  Removing existing PART_OF relationships...")
        delete_query = """
        MATCH ()-[r:PART_OF]->()
        DELETE r
        """
        neo4j.execute_query(delete_query)
        logger.info(f"✅ Removed existing PART_OF relationships")
        
        # Query all sections with parent_number
        logger.info("📊 Querying sections with parent relationships...")
        sections_with_parents = db.query(Section).filter(
            Section.extra_metadata['parent_number'].isnot(None)
        ).all()
        
        total_sections = len(sections_with_parents)
        logger.info(f"📋 Found {total_sections} sections with parent relationships")
        
        if total_sections == 0:
            logger.warning("⚠️  No sections with parent relationships found")
            return
        
        # Create PART_OF relationships
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for i, section in enumerate(sections_with_parents, 1):
            try:
                parent_number = section.extra_metadata.get('parent_number')
                if not parent_number:
                    skipped_count += 1
                    continue
                
                # Find parent section (same regulation, matching section_number)
                parent_section = db.query(Section).filter(
                    and_(
                        Section.regulation_id == section.regulation_id,
                        Section.section_number == parent_number
                    )
                ).first()
                
                if not parent_section:
                    logger.debug(f"Skipping section {section.section_number}: Parent section '{parent_number}' not found")
                    skipped_count += 1
                    continue
                
                # Create PART_OF relationship in Neo4j (child -> parent)
                query = """
                MATCH (child:Section {id: $child_id})
                MATCH (parent:Section {id: $parent_id})
                MERGE (child)-[r:PART_OF]->(parent)
                SET r.created_at = datetime()
                RETURN r
                """
                
                neo4j.execute_write(
                    query,
                    {
                        "child_id": str(section.id),
                        "parent_id": str(parent_section.id)
                    }
                )
                created_count += 1
                
                # Log progress every 10,000 sections
                if i % 10000 == 0:
                    logger.info(f"Progress: {i}/{total_sections} sections processed ({created_count} relationships created)...")
                    
            except Exception as e:
                logger.error(f"Error processing section {i}/{total_sections} ({section.section_number}): {e}")
                error_count += 1
        
        # Summary
        logger.info("=" * 60)
        logger.info("📊 SECTION HIERARCHY REBUILD SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total sections with parents:  {total_sections}")
        logger.info(f"✅ PART_OF relationships created: {created_count}")
        logger.info(f"⏭️  Sections skipped:              {skipped_count}")
        logger.info(f"❌ Errors encountered:            {error_count}")
        logger.info("=" * 60)
        
        if created_count > 0:
            logger.info("✅ Section hierarchy rebuild completed successfully!")
        else:
            logger.warning("⚠️  No PART_OF relationships were created")
        
    except Exception as e:
        logger.error(f"❌ Fatal error during rebuild: {e}", exc_info=True)
        raise
    finally:
        db.close()
        neo4j.close()


if __name__ == "__main__":
    try:
        rebuild_section_hierarchy()
    except KeyboardInterrupt:
        logger.info("\n🛑 Rebuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Rebuild failed: {e}")
        sys.exit(1)
