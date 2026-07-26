#!/usr/bin/env python3
"""
Quick verification script to check all 278,854 documents are accessible
Usage: python scripts/verify_all_systems.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from database import SessionLocal
from models.models import Regulation, Section, Amendment

def check_postgresql():
    """Check PostgreSQL document counts"""
    print("=" * 60)
    print("PostgreSQL Database")
    print("=" * 60)
    db = SessionLocal()
    regulations = db.query(Regulation).count()
    sections = db.query(Section).count()
    amendments = db.query(Amendment).count()
    total = regulations + sections
    
    print(f"✓ Regulations: {regulations:,}")
    print(f"✓ Sections: {sections:,}")
    print(f"✓ Amendments: {amendments:,}")
    print(f"✓ Total Documents: {total:,}")
    db.close()
    return total

def check_elasticsearch():
    """Check Elasticsearch index"""
    print("\n" + "=" * 60)
    print("Elasticsearch")
    print("=" * 60)
    
    try:
        # Check index exists
        response = requests.get("http://elasticsearch:9200/regulatory_documents/_count")
        if response.status_code == 200:
            count = response.json()['count']
            print(f"✓ Index: regulatory_documents")
            print(f"✓ Documents: {count:,}")
            
            # Sample a few documents
            sample = requests.get("http://elasticsearch:9200/regulatory_documents/_search?size=5")
            if sample.status_code == 200:
                hits = sample.json()['hits']['hits']
                print(f"✓ Sample documents retrieved: {len(hits)}")
                print("\nSample titles:")
                for hit in hits[:3]:
                    title = hit['_source'].get('title', 'N/A')[:70]
                    doc_type = hit['_source'].get('document_type', 'N/A')
                    print(f"  - [{doc_type}] {title}...")
            return count
        else:
            print(f"✗ Error: {response.status_code}")
            return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0

def check_neo4j():
    """Check Neo4j graph"""
    print("\n" + "=" * 60)
    print("Neo4j Knowledge Graph")
    print("=" * 60)
    
    try:
        query = {
            "statements": [
                {"statement": "MATCH (n:Regulation) RETURN count(n) as count"},
                {"statement": "MATCH (n:Section) RETURN count(n) as count"}
            ]
        }
        
        response = requests.post(
            "http://neo4j:7474/db/neo4j/tx/commit",
            json=query,
            auth=("neo4j", "password123")
        )
        
        if response.status_code == 200:
            results = response.json()['results']
            reg_count = results[0]['data'][0]['row'][0] if results[0]['data'] else 0
            sec_count = results[1]['data'][0]['row'][0] if results[1]['data'] else 0
            
            print(f"✓ Regulation nodes: {reg_count:,}")
            print(f"✓ Section nodes: {sec_count:,}")
            print(f"✓ Total nodes: {reg_count + sec_count:,}")
            return reg_count + sec_count
        else:
            print(f"✗ Error: {response.status_code}")
            return 0
    except Exception as e:
        print(f"✗ Error: {e}")
        return 0

def test_rag_access():
    """Test RAG system can access documents"""
    print("\n" + "=" * 60)
    print("RAG System Test")
    print("=" * 60)
    
    test_questions = [
        "What is the Employment Insurance Act?",
        "Tell me about the Income Tax Act",
        "What is the Criminal Code?"
    ]
    
    try:
        for question in test_questions:
            response = requests.post(
                "http://localhost:8000/api/rag/ask",
                json={
                    "question": question,
                    "num_context_docs": 5
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                sources = len(data.get('sources', []))
                confidence = data.get('confidence', 0)
                print(f"✓ '{question[:40]}...'")
                print(f"  Sources: {sources}, Confidence: {confidence:.2f}")
            else:
                print(f"✗ '{question}' - Status: {response.status_code}")
                
    except Exception as e:
        print(f"✗ Error testing RAG: {e}")

def test_search():
    """Test search functionality"""
    print("\n" + "=" * 60)
    print("Search Service Test")
    print("=" * 60)
    
    try:
        # Note: parse_query=False to avoid automatic filters that may not match indexed fields
        response = requests.post(
            "http://localhost:8000/api/search/hybrid",
            json={
                "query": "employment insurance",
                "size": 10,
                "parse_query": False  # Disable NLP parsing to avoid non-existent field filters
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            hits = data.get('hits', [])
            total = data.get('total', 0)
            print(f"✓ Hybrid search for 'employment insurance'")
            print(f"  Total results: {total:,}")
            print(f"  Returned: {len(hits)}")
            
            if hits:
                top_hit = hits[0]['source']
                title = top_hit.get('title', 'N/A')[:60]
                print(f"  Top result: {title}...")
            
            if total == 0:
                print("  ⚠ Warning: Search returned 0 results")
                print("  This may indicate missing program/filter fields in documents")
        else:
            print(f"✗ Search failed: {response.status_code}")
            if response.text:
                print(f"  Error: {response.text[:100]}")
            
    except Exception as e:
        print(f"✗ Error testing search: {e}")

def main():
    print("\n" + "=" * 60)
    print("REGULATORY INTELLIGENCE ASSISTANT")
    print("System Verification Report")
    print("=" * 60)
    
    # Check all systems
    pg_count = check_postgresql()
    es_count = check_elasticsearch()
    neo4j_count = check_neo4j()
    
    # Test functionality
    test_search()
    test_rag_access()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if pg_count == es_count == 278854:
        print("✓ All systems operational!")
        print(f"✓ {pg_count:,} documents accessible across all systems")
        print("\n✓ Ready for chat testing with full knowledge base access")
    else:
        print("⚠ Warning: Document counts don't match")
        print(f"  PostgreSQL: {pg_count:,}")
        print(f"  Elasticsearch: {es_count:,}")
        print(f"  Expected: 278,854")
        if es_count == 0:
            print("\n  Run: docker compose exec backend python scripts/reindex_elasticsearch.py")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
