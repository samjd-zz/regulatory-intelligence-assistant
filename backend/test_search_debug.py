#!/usr/bin/env python3
"""
Debug script to test Elasticsearch search functionality
"""

import sys
sys.path.insert(0, '/app')

from services.search_service import SearchService

# Initialize search service
search = SearchService()

print("=" * 80)
print("Search Service Debug Test")
print("=" * 80)

# Test 1: Simple keyword search
print("\n1. Testing keyword search for 'employment insurance'...")
results = search.keyword_search("employment insurance", size=5)
print(f"   Total hits: {results.get('total', 0)}")
print(f"   Returned hits: {len(results.get('hits', []))}")

if results.get('hits'):
    print("   First hit:")
    first_hit = results['hits'][0]
    print(f"   - ID: {first_hit['id']}")
    print(f"   - Score: {first_hit['score']}")
    print(f"   - Title: {first_hit['source'].get('title', 'N/A')[:100]}")
else:
    print("   ❌ NO HITS RETURNED")
    if 'error' in results:
        print(f"   Error: {results['error']}")

# Test 2: Simple vector search  
print("\n2. Testing vector search for 'employment insurance'...")
try:
    results = search.vector_search("employment insurance", size=5)
    print(f"   Total hits: {results.get('total', 0)}")
    print(f"   Returned hits: {len(results.get('hits', []))}")
    
    if results.get('hits'):
        print("   First hit:")
        first_hit = results['hits'][0]
        print(f"   - ID: {first_hit['id']}")
        print(f"   - Score: {first_hit['score']}")
        print(f"   - Title: {first_hit['source'].get('title', 'N/A')[:100]}")
    else:
        print("   ❌ NO HITS RETURNED")
        if 'error' in results:
            print(f"   Error: {results['error']}")
except Exception as e:
    print(f"   ❌ EXCEPTION: {e}")

# Test 3: Hybrid search
print("\n3. Testing hybrid search for 'employment insurance'...")
results = search.hybrid_search("employment insurance", size=5)
print(f"   Total hits: {results.get('total', 0)}")
print(f"   Returned hits: {len(results.get('hits', []))}")

if results.get('hits'):
    print("   First hit:")
    first_hit = results['hits'][0]
    print(f"   - ID: {first_hit['id']}")
    print(f"   - Score: {first_hit['score']}")
    print(f"   - Title: {first_hit['source'].get('title', 'N/A')[:100]}")
else:
    print("   ❌ NO HITS RETURNED")
    if 'error' in results:
        print(f"   Error: {results['error']}")

# Test 4: Direct ES query to verify documents exist
print("\n4. Testing direct Elasticsearch query...")
from elasticsearch import Elasticsearch
import os

es_url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
es = Elasticsearch([es_url])

try:
    response = es.search(
        index="regulatory_documents",
        body={
            "query": {"match": {"content": "employment insurance"}},
            "size": 1,
            "_source": ["title"],
            "track_total_hits": True
        }
    )
    total = response['hits']['total']['value']
    print(f"   Direct ES query found: {total} documents")
    
    if response['hits']['hits']:
        print(f"   Sample title: {response['hits']['hits'][0]['_source'].get('title', 'N/A')[:100]}")
except Exception as e:
    print(f"   ❌ Direct query failed: {e}")

print("\n" + "=" * 80)
print("Debug test complete!")
