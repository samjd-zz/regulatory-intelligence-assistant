#!/usr/bin/env python3
"""
Migration script to add Program nodes and APPLIES_TO relationships to Neo4j.

This script analyzes existing Regulation nodes in Neo4j and creates:
1. Program nodes for government programs (EI, CPP, OAS, etc.)
2. APPLIES_TO relationships from Regulation nodes to Program nodes

The script uses the same program detection logic as the graph_builder to ensure
consistency between new ingestions and existing data.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from config.program_mappings import FEDERAL_PROGRAMS
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_programs_from_title(title: str) -> list:
    """
    Extract program mentions from regulation title using FEDERAL_PROGRAMS config.
    
    Args:
        title: Regulation title
        
    Returns:
        List of program keys that match
    """
    programs = []
    title_lower = title.lower()
    
    # Check title for each known program
    for program_key, program_config in FEDERAL_PROGRAMS.items():
        found = False
        
        # Check keywords in title
        for keyword in program_config.get('keywords', []):
            if keyword.lower() in title_lower:
                found = True
                break
        
        # Check patterns in title
        if not found:
            for pattern in program_config.get('patterns', []):
                if re.search(pattern, title, re.IGNORECASE):
                    found = True
                    break
        
        if found:
            programs.append(program_key)
    
    return programs


def migrate_programs():
    """
    Add Program nodes and APPLIES_TO relationships to existing Neo4j data.
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
            # Get all Regulation nodes
            logger.info("Fetching all Regulation nodes...")
            result = session.run("""
                MATCH (r:Regulation)
                RETURN r.id as id, r.title as title, r.authority as authority
            """)
            
            regulations = list(result)
            total = len(regulations)
            logger.info(f"Found {total} regulation nodes")
            
            # Track statistics
            programs_created = {}
            relationships_created = 0
            regs_with_programs = 0
            
            # Process each regulation
            for i, reg in enumerate(regulations):
                reg_id = reg['id']
                title = reg['title']
                authority = reg['authority']
                
                # Extract programs from title
                program_keys = extract_programs_from_title(title)
                
                if program_keys:
                    regs_with_programs += 1
                    
                    for program_key in program_keys:
                        # Convert to readable name
                        program_name = program_key.replace('_', ' ').title()
                        
                        # Track programs
                        if program_key not in programs_created:
                            programs_created[program_key] = program_name
                        
                        # Create Program node if it doesn't exist
                        session.run("""
                            MERGE (p:Program {program_key: $program_key})
                            ON CREATE SET 
                                p.name = $program_name,
                                p.description = $description,
                                p.created_at = datetime()
                        """, 
                            program_key=program_key,
                            program_name=program_name,
                            description=f"Government program: {program_name}"
                        )
                        
                        # Create APPLIES_TO relationship
                        session.run("""
                            MATCH (r:Regulation {id: $reg_id})
                            MATCH (p:Program {program_key: $program_key})
                            MERGE (r)-[:APPLIES_TO]->(p)
                        """,
                            reg_id=reg_id,
                            program_key=program_key
                        )
                        
                        relationships_created += 1
                
                # Progress update
                if (i + 1) % 100 == 0:
                    logger.info(f"Processed {i + 1}/{total} regulations...")
            
            logger.info(f"\nMigration complete!")
            logger.info(f"  Regulations with programs: {regs_with_programs}")
            logger.info(f"  Unique programs created: {len(programs_created)}")
            logger.info(f"  APPLIES_TO relationships: {relationships_created}")
            
            # List programs created
            if programs_created:
                logger.info(f"\nPrograms identified:")
                for program_key, program_name in sorted(programs_created.items()):
                    logger.info(f"  - {program_name} ({program_key})")
            
            # Verify final counts
            result = session.run("MATCH (p:Program) RETURN count(p) as count")
            program_count = result.single()['count']
            
            result = session.run("MATCH ()-[r:APPLIES_TO]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            
            logger.info(f"\nVerification:")
            logger.info(f"  Total Program nodes in Neo4j: {program_count}")
            logger.info(f"  Total APPLIES_TO relationships: {rel_count}")
            
            # Show sample relationships
            logger.info(f"\nSample relationships:")
            result = session.run("""
                MATCH (r:Regulation)-[:APPLIES_TO]->(p:Program)
                RETURN r.title as regulation, p.name as program
                LIMIT 5
            """)
            for record in result:
                logger.info(f"  {record['regulation']} → {record['program']}")
            
    finally:
        driver.close()
        logger.info("\nConnection closed")


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Neo4j Program Nodes Migration Script")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        migrate_programs()
        logger.info("\n✓ Migration successful!")
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
