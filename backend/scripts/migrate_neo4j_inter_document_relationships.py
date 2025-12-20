#!/usr/bin/env python3
"""
Migration script to add inter-document relationships in Neo4j.

This script creates relationships BETWEEN different regulations:
1. ENACTED_UNDER: Links Regulations to their parent Acts
   - Example: "Employment Insurance Fishing Regulations" → "Employment Insurance Act"
2. REFERENCES: Links documents that cite each other

This connects the graph properly so all documents are interconnected.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_parent_act_name(regulation_title: str) -> str:
    """
    Extract the parent Act name from a regulation title.
    
    Examples:
    - "Employment Insurance (Fishing) Regulations" → "Employment Insurance Act"
    - "Canada Pension Plan Regulations" → "Canada Pension Plan"
    - "Immigration and Refugee Protection Regulations" → "Immigration and Refugee Protection Act"
    
    Args:
        regulation_title: Title of the regulation
        
    Returns:
        Likely parent Act name
    """
    title_lower = regulation_title.lower()
    
    # Remove common regulation suffixes
    patterns = [
        r'\s+regulations?$',
        r'\s+\(.*?\)\s+regulations?$',  # (Something) Regulations
        r'\s+rules?$',
        r'\s+\(.*?\)\s+rules?$',
        r'\s+order$',
        r'\s+\(.*?\)\s+order$',
    ]
    
    base_name = regulation_title
    for pattern in patterns:
        base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
    
    # If it doesn't end with "Act", add it
    if not base_name.lower().endswith('act') and not base_name.lower().endswith('loi'):
        # Check if this might already be an Act name
        if 'act' in title_lower or 'loi' in title_lower:
            return base_name.strip()
        else:
            return f"{base_name.strip()} Act"
    
    return base_name.strip()


def migrate_inter_document_relationships():
    """
    Add ENACTED_UNDER relationships from Regulations to their parent Acts.
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
            # Get all Regulation nodes (those with node_type='Regulation')
            logger.info("Fetching Regulation nodes...")
            result = session.run("""
                MATCH (r:Regulation)
                WHERE r.node_type = 'Regulation'
                RETURN r.id as id, r.title as title
            """)
            
            regulations = list(result)
            logger.info(f"Found {len(regulations)} regulation nodes")
            
            # Get all Legislation nodes (Acts)
            result = session.run("""
                MATCH (l:Regulation)
                WHERE l.node_type = 'Legislation'
                RETURN l.id as id, l.title as title
            """)
            
            acts = {act['title']: act['id'] for act in result}
            logger.info(f"Found {len(acts)} legislation (Act) nodes")
            
            # Create ENACTED_UNDER relationships
            enacted_under_count = 0
            
            for reg in regulations:
                reg_id = reg['id']
                reg_title = reg['title']
                
                # Extract parent Act name
                parent_act_name = extract_parent_act_name(reg_title)
                
                # Try exact match first
                if parent_act_name in acts:
                    session.run("""
                        MATCH (r:Regulation {id: $reg_id})
                        MATCH (a:Regulation {id: $act_id})
                        MERGE (r)-[:ENACTED_UNDER]->(a)
                    """,
                        reg_id=reg_id,
                        act_id=acts[parent_act_name]
                    )
                    enacted_under_count += 1
                    logger.debug(f"Linked: {reg_title} → {parent_act_name}")
                else:
                    # Try fuzzy match (case-insensitive, partial)
                    found_match = False
                    parent_lower = parent_act_name.lower()
                    
                    for act_title, act_id in acts.items():
                        act_lower = act_title.lower()
                        
                        # Check if significant parts match
                        # Remove "Act", "Loi" for comparison
                        parent_base = parent_lower.replace(' act', '').replace(' loi', '').strip()
                        act_base = act_lower.replace(' act', '').replace(' loi', '').strip()
                        
                        if parent_base and act_base and (parent_base in act_base or act_base in parent_base):
                            session.run("""
                                MATCH (r:Regulation {id: $reg_id})
                                MATCH (a:Regulation {id: $act_id})
                                MERGE (r)-[:ENACTED_UNDER]->(a)
                            """,
                                reg_id=reg_id,
                                act_id=act_id
                            )
                            enacted_under_count += 1
                            logger.debug(f"Linked (fuzzy): {reg_title} → {act_title}")
                            found_match = True
                            break
                    
                    if not found_match:
                        logger.debug(f"No parent Act found for: {reg_title} (looking for: {parent_act_name})")
            
            logger.info(f"\nMigration complete!")
            logger.info(f"  ENACTED_UNDER relationships created: {enacted_under_count}")
            
            # Verify counts
            result = session.run("""
                MATCH ()-[r:ENACTED_UNDER]->()
                RETURN count(r) as count
            """)
            enacted_count = result.single()['count']
            
            logger.info(f"\nVerification:")
            logger.info(f"  Total ENACTED_UNDER relationships: {enacted_count}")
            
            # Show sample relationships
            logger.info(f"\nSample ENACTED_UNDER relationships:")
            result = session.run("""
                MATCH (r:Regulation)-[:ENACTED_UNDER]->(a:Regulation)
                WHERE r.node_type = 'Regulation' AND a.node_type = 'Legislation'
                RETURN r.title as regulation, a.title as act
                LIMIT 10
            """)
            
            for record in result:
                logger.info(f"  {record['regulation']} → {record['act']}")
            
            # Count connected vs disconnected
            result = session.run("""
                MATCH (r:Regulation)
                WHERE r.node_type = 'Regulation'
                AND NOT (r)-[:ENACTED_UNDER]->()
                RETURN count(r) as count
            """)
            disconnected = result.single()['count']
            
            logger.info(f"\nConnectivity:")
            logger.info(f"  Regulations with parent Acts: {enacted_under_count}")
            logger.info(f"  Regulations without parent Acts: {disconnected}")
            
    finally:
        driver.close()
        logger.info("\nConnection closed")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Neo4j Inter-Document Relationships Migration Script")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        migrate_inter_document_relationships()
        logger.info("\n✓ Migration successful!")
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
