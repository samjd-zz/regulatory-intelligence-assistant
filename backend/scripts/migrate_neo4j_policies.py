#!/usr/bin/env python3
"""
Migration script to:
1. Identify Policy documents in Neo4j (currently labeled as Regulation)
2. Re-label them as Policy nodes
3. Create INTERPRETS relationships from Policy to Legislation

Run: python scripts/migrate_neo4j_policies.py
"""

import sys
import os
from pathlib import Path
import re
from collections import Counter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from database import SessionLocal
from models.models import Regulation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def determine_node_type(title: str) -> str:
    """
    Determine if document should be Policy, Legislation, or Regulation.
    
    Args:
        title: Document title
        
    Returns:
        'Policy', 'Legislation', or 'Regulation'
    """
    title_lower = title.lower()
    
    # Policy documents - check specific patterns first
    if 'order issuing' in title_lower:
        return 'Policy'
    if 'ministerial order' in title_lower:
        return 'Policy'
    if title_lower.endswith('guidelines') or title_lower.endswith('guideline'):
        return 'Policy'
    if title_lower.endswith('directive') or title_lower.endswith('directives'):
        return 'Policy'
    if 'policy' in title_lower and 'act' not in title_lower:
        return 'Policy'
    if 'proclamation' in title_lower:
        return 'Policy'
    
    # Acts and Lois are Legislation
    if ' act' in title_lower or title_lower.startswith('act ') or title_lower.endswith(' act'):
        return 'Legislation'
    if ' loi' in title_lower or title_lower.startswith('loi ') or title_lower.endswith(' loi'):
        return 'Legislation'
    
    # Everything else is Regulation
    return 'Regulation'

def extract_interpreted_legislation(title: str, full_text: str) -> str:
    """
    Extract the name of the Act/Legislation that a policy interprets.
    
    Args:
        title: Policy title
        full_text: Full text of the policy
        
    Returns:
        Name of the interpreted Act, or empty string
    """
    # Manual mappings for known policies
    known_mappings = {
        'Federal Child Support Guidelines': 'Divorce Act',
        'Order Issuing a Direction to the CRTC on a Renewed Approach to Telecommunications Policy': 'Telecommunications Act',
    }
    
    if title in known_mappings:
        return known_mappings[title]
    
    # Pattern 1: "Guidelines" or "Policy" followed by "under the X Act"
    match = re.search(r'under the ([^,\\.]+Act)', title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Pattern 2: "X Act Guidelines/Policy/Directive"
    match = re.search(r'^(.+Act)\s+(Guidelines?|Policy|Directive)', title, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Pattern 3: Look for Act references in the text
    if full_text:
        # Find first mention of an Act in the text (first 2000 chars)
        text_sample = full_text[:2000] if len(full_text) > 2000 else full_text
        act_mentions = re.findall(r'([A-Z][\w\s]+Act)', text_sample)
        if act_mentions:
            # Return the most common Act mention
            most_common = Counter(act_mentions).most_common(1)
            if most_common:
                return most_common[0][0].strip()
    
    return ""

def migrate_policies():
    """Migrate Policy nodes and create INTERPRETS relationships."""
    
    print("=" * 80)
    print("POLICY NODE MIGRATION")
    print("=" * 80)
    
    # Get Neo4j connection details
    uri = os.getenv('NEO4J_URI', 'bolt://neo4j:7687')
    user = os.getenv('NEO4J_USER', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD')
    
    if not password:
        logger.error("NEO4J_PASSWORD environment variable not set")
        sys.exit(1)
    
    logger.info(f"Connecting to Neo4j at {uri}")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    db = SessionLocal()
    
    try:
        with driver.session() as session:
            # Step 1: Find all Policy and Regulation nodes in Neo4j
            print("\n[1/4] Finding all nodes in Neo4j...")
            
            # Get Regulation nodes
            result = session.run("""
                MATCH (n:Regulation)
                RETURN n.id as id, n.title as title, n.node_type as node_type
            """)
            regulation_nodes = list(result)
            
            # Get Policy nodes (may already be labeled correctly)
            result = session.run("""
                MATCH (n:Policy)
                RETURN n.id as id, n.title as title, n.node_type as node_type
            """)
            existing_policy_nodes = list(result)
            
            print(f"Found {len(regulation_nodes)} Regulation nodes")
            print(f"Found {len(existing_policy_nodes)} existing Policy nodes")
            
            all_nodes = regulation_nodes + existing_policy_nodes
        
            all_nodes = list(result)
            print(f"Found {len(all_nodes)} Regulation nodes")
            print(f"Found {len(regulation_nodes)} Regulation nodes")
            print(f"Found {len(existing_policy_nodes)} existing Policy nodes")
            
            all_nodes = regulation_nodes + existing_policy_nodes
            
            # Step 2: Identify which Regulation nodes should be Policy
            print("\n[2/4] Identifying Policy documents in Regulation nodes...")
            policy_nodes_to_relabel = []
            for node in regulation_nodes:
                node_type = determine_node_type(node['title'])
                if node_type == 'Policy':
                    # Fetch full text from PostgreSQL
                    reg = db.query(Regulation).filter(Regulation.id == node['id']).first()
                    full_text = reg.full_text if reg else ""
                    policy_nodes_to_relabel.append({
                        'id': node['id'],
                        'title': node['title'],
                        'full_text': full_text
                    })
            
            print(f"Found {len(policy_nodes_to_relabel)} Regulation nodes that should be Policy:")
            for policy in policy_nodes_to_relabel:
                print(f"  - {policy['title']}")
            
            # Add existing Policy nodes to the list for INTERPRETS creation
            all_policy_nodes = policy_nodes_to_relabel.copy()
            for node in existing_policy_nodes:
                reg = db.query(Regulation).filter(Regulation.id == node['id']).first()
                full_text = reg.full_text if reg else ""
                all_policy_nodes.append({
                    'id': node['id'],
                    'title': node['title'],
                    'full_text': full_text
                })
            
            print(f"Total Policy documents (existing + to relabel): {len(all_policy_nodes)}")
            
            # Step 3: Re-label Policy nodes (skip if already labeled)
            print(f"\n[3/4] Re-labeling {len(policy_nodes_to_relabel)} nodes as Policy...")
            relabel_count = 0
            for policy in policy_nodes_to_relabel:
                # Check if node already has Policy label
                check_result = session.run("""
                    MATCH (n {id: $id})
                    RETURN labels(n) as labels
                """, id=policy['id'])
                check_record = check_result.single()
                
                if check_record and 'Policy' in check_record['labels']:
                    print(f"  ⊙ Already labeled as Policy: {policy['title'][:60]}...")
                    continue
                
                result = session.run("""
                    MATCH (n:Regulation {id: $id})
                    SET n:Policy
                    SET n.node_type = 'Policy'
                    REMOVE n:Regulation
                    RETURN n.title as title
                """, id=policy['id'])
                record = result.single()
                if record:
                    print(f"  ✓ Re-labeled: {record['title']}")
                    relabel_count += 1
            
            # Step 4: Create INTERPRETS relationships for ALL policy nodes
            print(f"\n[4/4] Creating INTERPRETS relationships for {len(all_policy_nodes)} policies...")
            interprets_count = 0
            for policy in all_policy_nodes:
                # Extract which Act this policy interprets
                interpreted_act = extract_interpreted_legislation(policy['title'], policy['full_text'])
                
                if not interpreted_act:
                    print(f"  ⚠ Could not find interpreted Act for: {policy['title']}")
                    continue
                
                # Find matching Legislation node
                act_base = interpreted_act.replace(' Act', '').replace(' Loi', '').strip()
                result = session.run("""
                    MATCH (p:Policy {id: $policy_id})
                    MATCH (l:Regulation)
                    WHERE l.node_type = 'Legislation'
                    AND (
                        toLower(l.title) = toLower($act_name)
                        OR toLower(l.title) CONTAINS toLower($act_base)
                    )
                    WITH p, l
                    LIMIT 1
                    MERGE (p)-[:INTERPRETS]->(l)
                    RETURN l.title as act_title
                """, policy_id=policy['id'], act_name=interpreted_act, act_base=act_base)
                
                record = result.single()
                if record:
                    print(f"  ✓ {policy['title'][:60]}... → {record['act_title']}")
                    interprets_count += 1
                else:
                    print(f"  ⚠ No matching Act found for: {policy['title']}")
                    print(f"    (Looking for: {interpreted_act})")
            
            # Summary
            print("\n" + "=" * 80)
            print("MIGRATION SUMMARY")
            print("=" * 80)
            print(f"Policy documents identified: {len(all_policy_nodes)}")
            print(f"Nodes re-labeled as Policy: {relabel_count}")
            print(f"INTERPRETS relationships created: {interprets_count}")
            
            # Verify node counts
            print("\n" + "=" * 80)
            print("NEO4J NODE VERIFICATION")
            print("=" * 80)
            
            # Count by node label
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            for record in result:
                print(f"{record['label']}: {record['count']}")
            
            # Count by node_type property
            result = session.run("""
                MATCH (n:Regulation)
                WHERE n.node_type IS NOT NULL
                RETURN n.node_type as node_type, count(n) as count
                ORDER BY count DESC
            """)
            print("\nRegulation nodes by node_type property:")
            for record in result:
                print(f"  {record['node_type']}: {record['count']}")
            
            result = session.run("""
                MATCH (n:Policy)
                RETURN count(n) as count
            """)
            record = result.single()
            print(f"\nPolicy nodes (by label): {record['count'] if record else 0}")
            
            # Count INTERPRETS relationships
            result = session.run("""
                MATCH ()-[r:INTERPRETS]->()
                RETURN count(r) as count
            """)
            record = result.single()
            print(f"INTERPRETS relationships: {record['count'] if record else 0}")
            
            print("\n✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()
        driver.close()

if __name__ == "__main__":
    migrate_policies()
