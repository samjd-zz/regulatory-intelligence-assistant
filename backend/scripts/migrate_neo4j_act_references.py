#!/usr/bin/env python3
"""
Migration script to create REFERENCES relationships between Acts (Legislation nodes).

This creates document-level REFERENCES relationships when:
- Sections of Act A reference sections of Act B
- This indicates Act A relies on or relates to Act B

Run: python scripts/migrate_neo4j_act_references.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_act_level_references():
    """
    Create REFERENCES relationships between Legislation nodes (Acts)
    based on cross-references between their sections.
    """
    # Get Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', 'password123')
    
    logger.info(f"Connecting to Neo4j at {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    try:
        with driver.session() as session:
            print("=" * 80)
            print("ACT-LEVEL REFERENCES MIGRATION")
            print("=" * 80)
            
            # Step 1: Find Act pairs that have section-level references between them
            print("\n[1/2] Finding Acts with section-level cross-references...")
            result = session.run("""
                MATCH (l1:Regulation)-[:HAS_SECTION]->(s1:Section)-[:REFERENCES]->(s2:Section)<-[:HAS_SECTION]-(l2:Regulation)
                WHERE l1.node_type = 'Legislation' 
                AND l2.node_type = 'Legislation'
                AND l1.id <> l2.id
                WITH l1, l2, count(DISTINCT s1) as ref_count
                WHERE ref_count > 0
                RETURN l1.id as source_id, l1.title as source_title, 
                       l2.id as target_id, l2.title as target_title,
                       ref_count
                ORDER BY ref_count DESC
            """)
            
            act_pairs = list(result)
            print(f"Found {len(act_pairs)} Act pairs with section cross-references")
            
            if act_pairs:
                print("\nTop 10 Act pairs by reference count:")
                for pair in act_pairs[:10]:
                    print(f"  {pair['source_title'][:50]:50} → {pair['target_title'][:50]:50} ({pair['ref_count']} refs)")
            
            # Step 2: Create document-level REFERENCES relationships
            print(f"\n[2/2] Creating Act-level REFERENCES relationships...")
            created_count = 0
            
            for pair in act_pairs:
                result = session.run("""
                    MATCH (l1:Regulation {id: $source_id})
                    MATCH (l2:Regulation {id: $target_id})
                    MERGE (l1)-[r:REFERENCES]->(l2)
                    ON CREATE SET r.reference_count = $ref_count,
                                  r.created_at = datetime()
                    ON MATCH SET r.reference_count = $ref_count
                    RETURN r
                """, source_id=pair['source_id'], 
                     target_id=pair['target_id'],
                     ref_count=pair['ref_count'])
                
                if result.single():
                    created_count += 1
                    if created_count <= 5:  # Show first 5
                        print(f"  ✓ {pair['source_title'][:60]}... → {pair['target_title'][:60]}...")
            
            # Summary
            print("\n" + "=" * 80)
            print("MIGRATION SUMMARY")
            print("=" * 80)
            print(f"Act pairs identified: {len(act_pairs)}")
            print(f"REFERENCES relationships created: {created_count}")
            
            # Verification
            print("\n" + "=" * 80)
            print("NEO4J VERIFICATION")
            print("=" * 80)
            
            # Count Act-level REFERENCES
            result = session.run("""
                MATCH (l1:Regulation)-[r:REFERENCES]->(l2:Regulation)
                WHERE l1.node_type = 'Legislation' AND l2.node_type = 'Legislation'
                RETURN count(r) as count
            """)
            act_refs = result.single()['count']
            print(f"Act-to-Act REFERENCES: {act_refs}")
            
            # Count Section-level REFERENCES
            result = session.run("""
                MATCH (s1:Section)-[r:REFERENCES]->(s2:Section)
                RETURN count(r) as count
            """)
            section_refs = result.single()['count']
            print(f"Section-to-Section REFERENCES: {section_refs}")
            
            # Count all relationship types for Legislation nodes
            result = session.run("""
                MATCH (l:Regulation)-[r]-()
                WHERE l.node_type = 'Legislation'
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
            """)
            print("\nLegislation node relationships:")
            for record in result:
                print(f"  {record['rel_type']}: {record['count']}")
            
            print("\n✓ Migration completed successfully!")
            
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.close()


if __name__ == "__main__":
    create_act_level_references()
