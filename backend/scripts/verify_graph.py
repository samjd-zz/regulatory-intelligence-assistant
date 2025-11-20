"""
Verify Neo4j knowledge graph data.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.neo4j_client import get_neo4j_client
from backend.services.graph_service import get_graph_service


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
