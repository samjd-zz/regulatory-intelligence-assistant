"""
Verify Neo4j graph structure and display statistics.
Run this to check the health and contents of the knowledge graph.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.neo4j_client import get_neo4j_client
from backend.services.graph_service import get_graph_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_connectivity():
    """Verify Neo4j connection."""
    print("\n" + "="*60)
    print("1. Verifying Neo4j Connectivity")
    print("="*60)
    
    client = get_neo4j_client()
    if client.verify_connectivity():
        print("✓ Successfully connected to Neo4j")
        return True
    else:
        print("✗ Failed to connect to Neo4j")
        return False


def verify_schema():
    """Verify schema constraints and indexes."""
    print("\n" + "="*60)
    print("2. Verifying Schema (Constraints & Indexes)")
    print("="*60)
    
    client = get_neo4j_client()
    
    # Check constraints
    print("\nConstraints:")
    constraints_query = "SHOW CONSTRAINTS"
    try:
        constraints = client.execute_query(constraints_query)
        if constraints:
            for c in constraints:
                print(f"  ✓ {c.get('name', 'unnamed')}: {c.get('type', 'unknown type')}")
        else:
            print("  ⚠ No constraints found")
    except Exception as e:
        print(f"  ⚠ Could not retrieve constraints: {e}")
    
    # Check indexes
    print("\nIndexes:")
    indexes_query = "SHOW INDEXES"
    try:
        indexes = client.execute_query(indexes_query)
        if indexes:
            for idx in indexes:
                print(f"  ✓ {idx.get('name', 'unnamed')}: {idx.get('type', 'unknown type')}")
        else:
            print("  ⚠ No indexes found")
    except Exception as e:
        print(f"  ⚠ Could not retrieve indexes: {e}")


def verify_data():
    """Verify data exists in the graph."""
    print("\n" + "="*60)
    print("3. Verifying Graph Data")
    print("="*60)
    
    service = get_graph_service()
    overview = service.get_graph_overview()
    
    print("\nNode Counts by Label:")
    if overview['nodes']:
        for label, count in sorted(overview['nodes'].items()):
            print(f"  {label}: {count}")
    else:
        print("  ⚠ No nodes found in graph")
    
    print("\nRelationship Counts by Type:")
    if overview['relationships']:
        for rel_type, count in sorted(overview['relationships'].items()):
            print(f"  {rel_type}: {count}")
    else:
        print("  ⚠ No relationships found in graph")


def show_sample_data():
    """Display sample data from the graph."""
    print("\n" + "="*60)
    print("4. Sample Data")
    print("="*60)
    
    client = get_neo4j_client()
    
    # Sample Legislation
    print("\nSample Legislation (up to 5):")
    legislation_query = """
    MATCH (l:Legislation)
    RETURN l.title, l.jurisdiction, l.status, l.effective_date
    LIMIT 5
    """
    legislation = client.execute_query(legislation_query)
    for i, leg in enumerate(legislation, 1):
        print(f"  {i}. {leg['l.title']}")
        print(f"     Jurisdiction: {leg['l.jurisdiction']}, Status: {leg['l.status']}")
    
    # Sample Programs
    print("\nSample Programs (up to 5):")
    programs_query = """
    MATCH (p:Program)
    RETURN p.name, p.department
    LIMIT 5
    """
    programs = client.execute_query(programs_query)
    for i, prog in enumerate(programs, 1):
        print(f"  {i}. {prog['p.name']}")
        print(f"     Department: {prog['p.department']}")


def show_relationship_examples():
    """Show example relationships in the graph."""
    print("\n" + "="*60)
    print("5. Sample Relationships")
    print("="*60)
    
    client = get_neo4j_client()
    
    # Legislation -> Sections
    print("\nLegislation with Sections:")
    sections_query = """
    MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
    RETURN l.title, count(s) as section_count
    ORDER BY section_count DESC
    LIMIT 3
    """
    leg_sections = client.execute_query(sections_query)
    for item in leg_sections:
        print(f"  • {item['l.title']}: {item['section_count']} sections")
    
    # Regulations -> Legislation
    print("\nRegulations implementing Legislation:")
    impl_query = """
    MATCH (r:Regulation)-[:IMPLEMENTS]->(l:Legislation)
    RETURN r.title, l.title as legislation
    LIMIT 3
    """
    implementations = client.execute_query(impl_query)
    for item in implementations:
        print(f"  • {item['r.title']}")
        print(f"    → implements {item['legislation']}")


def main():
    """Verify graph data."""
    print("\n" + "="*60)
    print("Neo4j Knowledge Graph Verification")
    print("="*60 + "\n")
    
    try:
        client = get_neo4j_client()
        
        # Check connectivity
        print("1. Checking Neo4j connectivity...")
        if client.verify_connectivity():
            print("   ✓ Connected to Neo4j successfully\n")
        else:
            print("   ✗ Failed to connect to Neo4j\n")
            return
        
        # Get graph statistics
        service = get_graph_service()
        overview = service.get_graph_overview()
        
        print("2. Graph Statistics:")
        print("   " + "-"*50)
        print("   Nodes:")
        for label, count in overview['nodes'].items():
            print(f"     - {label}: {count}")
        
        print("\n   Relationships:")
        for rel_type, count in overview['relationships'].items():
            print(f"     - {rel_type}: {count}")
        
        # Find legislation examples
        print("\n3. Sample Legislation:")
        print("   " + "-"*50)
        
        query = """
        MATCH (l:Legislation)
        RETURN l.title as title, l.act_number as act_number, l.jurisdiction as jurisdiction
        LIMIT 5
        """
        results = client.execute_query(query)
        for result in results:
            print(f"   - {result['title']}")
            print(f"     Act: {result['act_number']}, Jurisdiction: {result['jurisdiction']}")
        
        # Check sections
        print("\n4. Sample Sections:")
        print("   " + "-"*50)
        
        query = """
        MATCH (l:Legislation)-[:HAS_SECTION]->(s:Section)
        RETURN l.title as legislation, s.section_number as number, s.title as title
        LIMIT 5
        """
        results = client.execute_query(query)
        for result in results:
            print(f"   - {result['legislation']}, Section {result['number']}: {result['title']}")
        
        # Check relationships
        print("\n5. Sample Relationships:")
        print("   " + "-"*50)
        
        query = """
        MATCH (a)-[r]->(b)
        RETURN labels(a)[0] as from_type, labels(b)[0] as to_type, type(r) as rel_type
        LIMIT 10
        """
        results = client.execute_query(query)
        relationship_summary = {}
        for result in results:
            key = f"{result['from_type']} -{result['rel_type']}-> {result['to_type']}"
            relationship_summary[key] = relationship_summary.get(key, 0) + 1
        
        for rel, count in relationship_summary.items():
            print(f"   - {rel}: {count}")
        
        print("\n" + "="*60)
        print("✓ Verification complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. View the graph in Neo4j Browser: http://localhost:7474")
        print("   Run query: MATCH (n) RETURN n LIMIT 50")
        print("2. Test graph traversal queries")
        print("3. Integrate with backend API endpoints\n")
        
    except Exception as e:
        print(f"\n✗ Error during verification: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
