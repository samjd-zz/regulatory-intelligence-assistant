#!/usr/bin/env python3
"""
Quick verification script for Knowledge Graph implementation.
Tests core functionality without requiring full graph population.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.neo4j_client import Neo4jClient
from services.graph_builder import GraphBuilder
from database import SessionLocal
from models.document_models import Document, DocumentSection, DocumentType
from datetime import datetime
import uuid

def test_neo4j_connection():
    """Test Neo4j connectivity."""
    print("=" * 60)
    print("TEST 1: Neo4j Connection")
    print("=" * 60)
    
    try:
        client = Neo4jClient()
        if client.verify_connectivity():
            print("✅ Neo4j connection successful")
            return True
        else:
            print("❌ Neo4j connection failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_constraint_creation():
    """Test creating constraints."""
    print("\n" + "=" * 60)
    print("TEST 2: Constraint Creation")
    print("=" * 60)
    
    try:
        client = Neo4jClient()
        client.connect()
        
        query = "CREATE CONSTRAINT test_constraint IF NOT EXISTS FOR (n:TestNode) REQUIRE n.id IS UNIQUE"
        client.execute_write(query)
        print("✅ Constraint creation successful")
        
        # Clean up
        try:
            client.execute_write("DROP CONSTRAINT test_constraint IF EXISTS")
        except:
            pass
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_node_creation():
    """Test creating nodes."""
    print("\n" + "=" * 60)
    print("TEST 3: Node Creation")
    print("=" * 60)
    
    try:
        client = Neo4jClient()
        client.connect()
        
        # Create test node
        test_id = str(uuid.uuid4())
        node = client.create_node(
            "TestLegislation",
            {
                "id": test_id,
                "title": "Test Act",
                "jurisdiction": "federal"
            }
        )
        
        print(f"✅ Node created with ID: {test_id}")
        
        # Verify node exists
        found = client.find_node("TestLegislation", {"id": test_id})
        if found:
            print("✅ Node verification successful")
        else:
            print("❌ Node not found")
            return False
        
        # Clean up
        client.delete_node("TestLegislation", test_id)
        print("✅ Node cleanup successful")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_relationship_creation():
    """Test creating relationships."""
    print("\n" + "=" * 60)
    print("TEST 4: Relationship Creation")
    print("=" * 60)
    
    try:
        client = Neo4jClient()
        client.connect()
        
        # Create two test nodes
        leg_id = str(uuid.uuid4())
        sec_id = str(uuid.uuid4())
        
        client.create_node("TestLegislation", {"id": leg_id, "title": "Test Act"})
        client.create_node("TestSection", {"id": sec_id, "section_number": "1"})
        
        # Create relationship
        result = client.create_relationship(
            "TestLegislation", leg_id,
            "TestSection", sec_id,
            "HAS_SECTION",
            {"order": 0}
        )
        
        print("✅ Relationship created successfully")
        
        # Verify relationship
        related = client.find_related_nodes("TestLegislation", leg_id, "HAS_SECTION")
        if related:
            print(f"✅ Relationship verification successful (found {len(related)} related nodes)")
        else:
            print("❌ Relationship not found")
            return False
        
        # Clean up
        client.delete_node("TestLegislation", leg_id)
        client.delete_node("TestSection", sec_id)
        print("✅ Relationship cleanup successful")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_graph_builder():
    """Test graph builder with mock data."""
    print("\n" + "=" * 60)
    print("TEST 5: Graph Builder")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Create test document
        doc = Document(
            id=uuid.uuid4(),
            title="Test Employment Act",
            document_type=DocumentType.LEGISLATION,
            jurisdiction="federal",
            authority="Test Authority",
            full_text="Section 1: Employment insurance benefits are available.",
            file_format="txt",
            file_size=100,
            file_hash=str(uuid.uuid4()),
            is_processed=True,
            processed_date=datetime.utcnow()
        )
        db.add(doc)
        
        # Create test section
        section = DocumentSection(
            id=uuid.uuid4(),
            document_id=doc.id,
            section_number="1",
            section_title="Eligibility",
            content="Employment insurance benefits are available to eligible persons.",
            order_index=0,
            level=0
        )
        db.add(section)
        db.commit()
        
        print(f"✅ Test document created: {doc.title}")
        
        # Build graph
        client = Neo4jClient()
        client.connect()
        builder = GraphBuilder(db, client)
        
        stats = builder.build_document_graph(doc.id)
        
        print(f"✅ Graph built successfully")
        print(f"   - Nodes created: {stats.get('nodes_created', 0)}")
        print(f"   - Relationships created: {stats.get('relationships_created', 0)}")
        
        # Clean up
        client.delete_node("Legislation", str(doc.id))
        client.delete_node("Section", str(section.id))
        db.delete(section)
        db.delete(doc)
        db.commit()
        print("✅ Graph builder cleanup successful")
        
        return stats.get('nodes_created', 0) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def test_program_extraction():
    """Test program entity extraction."""
    print("\n" + "=" * 60)
    print("TEST 6: Program Extraction")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        client = Neo4jClient()
        client.connect()
        builder = GraphBuilder(db, client)
        
        # Create test document with program mentions
        doc = Document(
            id=uuid.uuid4(),
            title="Employment Insurance Act",
            document_type=DocumentType.LEGISLATION,
            jurisdiction="federal",
            authority="Parliament",
            full_text="""
            The Employment Insurance program provides benefits to eligible workers.
            Old Age Security benefits are available to seniors.
            Canada Pension Plan benefits support retirement.
            """,
            file_format="txt",
            file_size=100,
            file_hash=str(uuid.uuid4()),
            is_processed=True
        )
        
        # Extract programs
        programs = builder._extract_programs(doc)
        
        print(f"✅ Extracted {len(programs)} programs:")
        for prog in programs:
            print(f"   - {prog['name']}")
        
        return len(programs) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def test_situation_extraction():
    """Test situation entity extraction."""
    print("\n" + "=" * 60)
    print("TEST 7: Situation Extraction")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        client = Neo4jClient()
        client.connect()
        builder = GraphBuilder(db, client)
        
        # Create test document with situations
        doc = Document(
            id=uuid.uuid4(),
            title="Test Act",
            document_type=DocumentType.LEGISLATION,
            jurisdiction="federal",
            authority="Test",
            full_text="",
            file_format="txt",
            file_size=100,
            file_hash=str(uuid.uuid4()),
            is_processed=True
        )
        db.add(doc)
        
        section = DocumentSection(
            id=uuid.uuid4(),
            document_id=doc.id,
            section_number="1",
            section_title="Eligibility",
            content="""
            If you are unemployed and available for work, you may be eligible.
            Where a person has been dismissed without cause, benefits apply.
            In the case of disability, special provisions are available.
            """,
            order_index=0,
            level=0
        )
        db.add(section)
        db.commit()
        
        # Extract situations
        situations = builder._extract_situations(doc)
        
        print(f"✅ Extracted {len(situations)} situations:")
        for sit in situations[:3]:
            print(f"   - {sit['description'][:60]}...")
            print(f"     Tags: {sit.get('tags', [])}")
        
        # Clean up
        db.delete(section)
        db.delete(doc)
        db.commit()
        
        return len(situations) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH VERIFICATION")
    print("=" * 60)
    print()
    
    tests = [
        test_neo4j_connection,
        test_constraint_creation,
        test_node_creation,
        test_relationship_creation,
        test_graph_builder,
        test_program_extraction,
        test_situation_extraction,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
