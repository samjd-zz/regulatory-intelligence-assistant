#!/usr/bin/env python3
"""
Migration script to create SUPERSEDES relationships between Acts based on amendment data.

When Act B amends Act A, we create: (B)-[:SUPERSEDES]->(A)
This indicates B is a newer version or modifies A.

Run: python scripts/migrate_neo4j_supersedes.py
"""

import sys
import os
from pathlib import Path
import re

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from database import SessionLocal
from models.models import Amendment, Regulation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_bill_reference(description: str) -> tuple:
    """
    Extract year and chapter from amendment description.
    
    Examples:
    - "Amendment by 2023, c. 26" -> (2023, 26)
    - "Amendment by 2024, ch. 12" -> (2024, 12)
    - "Amendment by 2018, ch. 27, art. 485" -> (2018, 27)
    
    Returns:
        (year, chapter) or (None, None)
    """
    # Pattern for "YYYY, c. NN" or "YYYY, ch. NN"
    pattern = r'(\d{4}),\s+ch?\.?\s+(\d+)'
    match = re.search(pattern, description)
    if match:
        return (int(match.group(1)), int(match.group(2)))
    return (None, None)


def create_supersedes_relationships():
    """
    Create SUPERSEDES relationships based on amendment data.
    """
    # Database connection
    db = SessionLocal()
    
    # Neo4j connection
    uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password123')
    
    logger.info(f"Connecting to Neo4j at {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        print("=" * 80)
        print("SUPERSEDES RELATIONSHIPS MIGRATION")
        print("=" * 80)
        
        # Step 1: Get all amendments
        print("\n[1/3] Loading amendment data from PostgreSQL...")
        amendments = db.query(Amendment).all()
        print(f"Found {len(amendments)} amendments")
        
        # Step 2: Group amendments by regulation
        print("\n[2/3] Processing amendments...")
        amendment_map = {}  # reg_id -> list of (year, chapter)
        
        for amendment in amendments:
            year, chapter = extract_bill_reference(amendment.description or '')
            if year and chapter:
                if amendment.regulation_id not in amendment_map:
                    amendment_map[amendment.regulation_id] = []
                amendment_map[amendment.regulation_id].append({
                    'year': year,
                    'chapter': chapter,
                    'description': amendment.description,
                    'effective_date': amendment.effective_date
                })
        
        print(f"Processed {len(amendment_map)} regulations with parseable amendments")
        
        # Step 3: Create SUPERSEDES relationships
        # When Act A has amendment "by 2023, c. 26", we need to find the Act that is "2023, c. 26"
        # and create: (AmendingAct)-[:SUPERSEDES]->(A)
        
        print("\n[3/3] Creating SUPERSEDES relationships...")
        created_count = 0
        
        with driver.session() as session:
            for reg_id, amendments_list in amendment_map.items():
                # Get the regulation being amended
                reg = db.query(Regulation).filter(Regulation.id == reg_id).first()
                if not reg:
                    continue
                
                # Check if this regulation exists in Neo4j
                result = session.run("""
                    MATCH (target:Regulation {id: $reg_id})
                    RETURN target.title as title
                """, reg_id=str(reg_id))
                
                if not result.single():
                    continue  # Skip if not in Neo4j
                
                # For each amendment, try to find the amending Act
                for amend_info in amendments_list:
                    year = amend_info['year']
                    chapter = amend_info['chapter']
                    
                    # Try to find an Act with this year and chapter in its title
                    # Format variations: "2023, c. 26" or "S.C. 2023, c. 26" or just contains "2023"
                    result = session.run("""
                        MATCH (source:Regulation)
                        WHERE source.node_type = 'Legislation'
                        AND (
                            source.title CONTAINS $search1
                            OR source.title CONTAINS $search2
                            OR (source.title CONTAINS $year_str AND source.title CONTAINS $chapter_str)
                        )
                        RETURN source.id as id, source.title as title
                        LIMIT 1
                    """, search1=f"{year}, c. {chapter}",
                         search2=f"{year}, ch. {chapter}",
                         year_str=str(year),
                         chapter_str=f"c. {chapter}")
                    
                    source_record = result.single()
                    if source_record:
                        # Create SUPERSEDES relationship
                        result = session.run("""
                            MATCH (source:Regulation {id: $source_id})
                            MATCH (target:Regulation {id: $target_id})
                            MERGE (source)-[r:SUPERSEDES]->(target)
                            ON CREATE SET r.amendment_year = $year,
                                         r.amendment_chapter = $chapter,
                                         r.description = $description,
                                         r.effective_date = $effective_date,
                                         r.created_at = datetime()
                            RETURN r
                        """, source_id=source_record['id'],
                             target_id=str(reg_id),
                             year=year,
                             chapter=chapter,
                             description=amend_info['description'],
                             effective_date=amend_info['effective_date'].isoformat() if amend_info['effective_date'] else None)
                        
                        if result.single():
                            created_count += 1
                            if created_count <= 10:  # Show first 10
                                print(f"  ✓ {source_record['title'][:50]:50} SUPERSEDES {reg.title[:50]:50}")
        
        # Summary
        print("\n" + "=" * 80)
        print("MIGRATION SUMMARY")
        print("=" * 80)
        print(f"Amendments processed: {len(amendments)}")
        print(f"Regulations with amendments: {len(amendment_map)}")
        print(f"SUPERSEDES relationships created: {created_count}")
        
        # Verification
        print("\n" + "=" * 80)
        print("NEO4J VERIFICATION")
        print("=" * 80)
        
        with driver.session() as session:
            # Count SUPERSEDES relationships
            result = session.run("""
                MATCH ()-[r:SUPERSEDES]->()
                RETURN count(r) as count
            """)
            supersedes_count = result.single()['count']
            print(f"SUPERSEDES relationships: {supersedes_count}")
            
            # Sample some SUPERSEDES relationships
            if supersedes_count > 0:
                result = session.run("""
                    MATCH (source:Regulation)-[r:SUPERSEDES]->(target:Regulation)
                    RETURN source.title as source, target.title as target, r.amendment_year as year
                    LIMIT 5
                """)
                print("\nSample SUPERSEDES relationships:")
                for record in result:
                    print(f"  {record['source'][:60]:60} → {record['target'][:60]:60} ({record['year']})")
            
            # Count all relationship types
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            print("\nTop relationship types:")
            for record in result:
                print(f"  {record['rel_type']}: {record['count']}")
        
        print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        driver.close()


if __name__ == "__main__":
    create_supersedes_relationships()
