"""
Integration Tests for Search Service

Tests the search service with real Elasticsearch instance.
Validates keyword search, vector search, hybrid search, and indexing.

Note: Requires Elasticsearch to be running. Tests will be skipped if
Elasticsearch is not available.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, date

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.search_service import SearchService


# Check if Elasticsearch is available
def check_elasticsearch_available():
    """Check if Elasticsearch is running"""
    try:
        service = SearchService()
        return service.es_client.ping()
    except:
        return False


ES_AVAILABLE = check_elasticsearch_available()
skip_if_no_es = pytest.mark.skipif(
    not ES_AVAILABLE,
    reason="Elasticsearch not available"
)


@skip_if_no_es
class TestSearchServiceIntegration:
    """Integration tests for Search Service with real Elasticsearch"""

    @pytest.fixture(scope="class")
    def search_service(self):
        """Create search service"""
        return SearchService()

    @pytest.fixture(scope="class")
    def sample_documents(self):
        """Sample regulatory documents for testing"""
        return [
            {
                "id": "test-ei-s7",
                "title": "Employment Insurance Act - Section 7",
                "content": "Benefits are payable to persons who have lost employment and are available for work. Applicants must have accumulated sufficient insurable hours and must be authorized to work in Canada.",
                "citation": "S.C. 1996, c. 23, s. 7",
                "section_number": "7",
                "jurisdiction": "federal",
                "program": "employment_insurance",
                "effective_date": "1996-06-30"
            },
            {
                "id": "test-cpp-overview",
                "title": "Canada Pension Plan - Eligibility",
                "content": "The Canada Pension Plan provides retirement, disability, and survivor benefits. Contributors must be at least 18 years old and make contributions based on their earnings.",
                "citation": "R.S.C. 1985, c. C-8",
                "section_number": "44",
                "jurisdiction": "federal",
                "program": "canada_pension_plan",
                "effective_date": "1966-01-01"
            },
            {
                "id": "test-oas-eligibility",
                "title": "Old Age Security - Eligibility Requirements",
                "content": "Old Age Security pension is available to Canadian citizens and legal residents aged 65 and older who meet residency requirements. Applicants must have lived in Canada for at least 10 years after age 18.",
                "citation": "R.S.C. 1985, c. O-9",
                "section_number": "3",
                "jurisdiction": "federal",
                "program": "old_age_security",
                "effective_date": "1952-01-01"
            },
            {
                "id": "test-bc-worksafe",
                "title": "BC Workers Compensation - Coverage",
                "content": "WorkSafeBC provides coverage for workers injured on the job in British Columbia. Employers must register and pay premiums for workplace injury insurance.",
                "citation": "RSBC 2019, c. 1",
                "section_number": "1",
                "jurisdiction": "british_columbia",
                "program": "workers_compensation",
                "effective_date": "2019-01-01"
            },
            {
                "id": "test-on-tenant",
                "title": "Ontario Residential Tenancies Act",
                "content": "The Residential Tenancies Act governs rental housing in Ontario. It sets out rights and responsibilities of landlords and tenants, including rules about rent increases and evictions.",
                "citation": "S.O. 2006, c. 17",
                "section_number": "1",
                "jurisdiction": "ontario",
                "program": "housing",
                "effective_date": "2006-01-31"
            }
        ]

    @pytest.fixture(scope="class", autouse=True)
    def setup_test_data(self, search_service, sample_documents):
        """Index sample documents before tests"""
        # Create index
        try:
            search_service.create_index()
        except:
            pass  # Index may already exist

        # Index documents
        for doc in sample_documents:
            try:
                search_service.index_document(doc)
            except Exception as e:
                print(f"Warning: Failed to index {doc['id']}: {e}")

        # Wait for indexing
        search_service.es_client.indices.refresh(index=search_service.index_name)

        yield

        # Cleanup (optional - comment out to keep data for debugging)
        # try:
        #     search_service.delete_index()
        # except:
        #     pass

    # Keyword Search Tests

    def test_keyword_search_exact_match(self, search_service):
        """Test keyword search with exact term match"""
        result = search_service.keyword_search(
            query="employment insurance",
            size=5
        )

        assert result['total'] > 0
        assert len(result['hits']) > 0

        # Top result should be Employment Insurance document
        top_hit = result['hits'][0]
        assert 'employment' in top_hit['title'].lower()

    def test_keyword_search_with_filters(self, search_service):
        """Test keyword search with jurisdiction filter"""
        result = search_service.keyword_search(
            query="benefits",
            filters={'jurisdiction': 'federal'},
            size=10
        )

        # All results should be federal jurisdiction
        for hit in result['hits']:
            assert hit['jurisdiction'] == 'federal'

    def test_keyword_search_synonym_recognition(self, search_service):
        """Test that keyword search recognizes synonyms"""
        # Search for "EI" (synonym for employment insurance)
        result = search_service.keyword_search(
            query="EI benefits",
            size=5
        )

        assert result['total'] > 0

        # Should return employment insurance documents
        assert any('employment' in hit['title'].lower() for hit in result['hits'])

    def test_keyword_search_pagination(self, search_service):
        """Test keyword search pagination"""
        # First page
        page1 = search_service.keyword_search(
            query="Canada",
            size=2,
            from_=0
        )

        # Second page
        page2 = search_service.keyword_search(
            query="Canada",
            size=2,
            from_=2
        )

        assert len(page1['hits']) <= 2
        assert len(page2['hits']) <= 2

        # Pages should have different results
        if len(page1['hits']) > 0 and len(page2['hits']) > 0:
            assert page1['hits'][0]['id'] != page2['hits'][0]['id']

    # Vector Search Tests

    def test_vector_search_semantic_matching(self, search_service):
        """Test vector search finds semantically similar documents"""
        result = search_service.vector_search(
            query="retirement benefits for elderly Canadians",
            size=5
        )

        assert result['total'] > 0

        # Should find OAS or CPP documents (related to retirement)
        titles = [hit['title'].lower() for hit in result['hits']]
        assert any('pension' in title or 'old age' in title for title in titles)

    def test_vector_search_with_filters(self, search_service):
        """Test vector search with program filter"""
        result = search_service.vector_search(
            query="disability coverage",
            filters={'jurisdiction': 'federal'},
            size=5
        )

        # All results should match filter
        for hit in result['hits']:
            assert hit['jurisdiction'] == 'federal'

    # Hybrid Search Tests

    def test_hybrid_search_combines_results(self, search_service):
        """Test that hybrid search combines keyword and vector results"""
        result = search_service.hybrid_search(
            query="work injury compensation British Columbia",
            keyword_weight=0.5,
            vector_weight=0.5,
            size=5
        )

        assert result['total'] > 0

        # Should find BC WorkSafe document
        assert any('worksafe' in hit['title'].lower() or 'british columbia' in hit.get('jurisdiction', '').lower()
                   for hit in result['hits'])

    def test_hybrid_search_keyword_weighted(self, search_service):
        """Test hybrid search with higher keyword weight"""
        result = search_service.hybrid_search(
            query="Ontario tenancies",
            keyword_weight=0.8,
            vector_weight=0.2,
            size=5
        )

        assert result['total'] > 0

        # With high keyword weight, should prioritize exact matches
        top_hit = result['hits'][0]
        assert 'ontario' in top_hit['title'].lower() or top_hit.get('jurisdiction') == 'ontario'

    def test_hybrid_search_vector_weighted(self, search_service):
        """Test hybrid search with higher vector weight"""
        result = search_service.hybrid_search(
            query="coverage for workplace accidents",
            keyword_weight=0.2,
            vector_weight=0.8,
            size=5
        )

        assert result['total'] > 0

        # With high vector weight, should find semantically similar docs
        # (workers compensation)
        assert any('worker' in hit['title'].lower() or 'compensation' in hit['title'].lower()
                   for hit in result['hits'])

    # Filtering Tests

    def test_filter_by_jurisdiction(self, search_service):
        """Test filtering by jurisdiction"""
        result = search_service.hybrid_search(
            query="benefits",
            filters={'jurisdiction': 'ontario'},
            size=10
        )

        for hit in result['hits']:
            assert hit['jurisdiction'] == 'ontario'

    def test_filter_by_program(self, search_service):
        """Test filtering by program"""
        result = search_service.hybrid_search(
            query="eligibility",
            filters={'program': 'employment_insurance'},
            size=10
        )

        for hit in result['hits']:
            assert hit['program'] == 'employment_insurance'

    def test_filter_by_date_range(self, search_service):
        """Test filtering by date range"""
        result = search_service.hybrid_search(
            query="regulations",
            filters={
                'effective_date_from': '1990-01-01',
                'effective_date_to': '2000-12-31'
            },
            size=10
        )

        # Check that returned documents are within date range
        for hit in result['hits']:
            if 'effective_date' in hit:
                eff_date = datetime.strptime(hit['effective_date'], '%Y-%m-%d').date()
                assert date(1990, 1, 1) <= eff_date <= date(2000, 12, 31)

    def test_multiple_filters_combined(self, search_service):
        """Test combining multiple filters"""
        result = search_service.hybrid_search(
            query="eligibility",
            filters={
                'jurisdiction': 'federal',
                'program': 'canada_pension_plan'
            },
            size=10
        )

        for hit in result['hits']:
            assert hit['jurisdiction'] == 'federal'
            assert hit['program'] == 'canada_pension_plan'

    # Indexing Tests

    def test_index_single_document(self, search_service):
        """Test indexing a single document"""
        doc = {
            "id": "test-new-doc",
            "title": "Test Document",
            "content": "This is a test document for indexing.",
            "jurisdiction": "federal",
            "program": "test"
        }

        result = search_service.index_document(doc)
        assert result['result'] in ['created', 'updated']

        # Verify document is searchable
        search_service.es_client.indices.refresh(index=search_service.index_name)

        search_result = search_service.keyword_search(
            query="test document",
            size=5
        )

        assert any(hit['id'] == 'test-new-doc' for hit in search_result['hits'])

    def test_bulk_index_documents(self, search_service):
        """Test bulk indexing"""
        docs = [
            {
                "id": f"test-bulk-{i}",
                "title": f"Bulk Test Document {i}",
                "content": f"Content for bulk test document number {i}",
                "jurisdiction": "federal"
            }
            for i in range(5)
        ]

        result = search_service.bulk_index_documents(docs)
        assert result['indexed'] == 5
        assert result['failed'] == 0

        # Verify documents are searchable
        search_service.es_client.indices.refresh(index=search_service.index_name)

        search_result = search_service.keyword_search(
            query="bulk test document",
            size=10
        )

        assert search_result['total'] >= 5

    def test_update_existing_document(self, search_service):
        """Test updating an existing document"""
        doc_id = "test-update-doc"

        # Index initial version
        doc_v1 = {
            "id": doc_id,
            "title": "Original Title",
            "content": "Original content",
            "jurisdiction": "federal"
        }
        search_service.index_document(doc_v1)

        # Update document
        doc_v2 = {
            "id": doc_id,
            "title": "Updated Title",
            "content": "Updated content",
            "jurisdiction": "federal"
        }
        result = search_service.index_document(doc_v2)
        assert result['result'] in ['updated', 'created']

        # Verify update
        search_service.es_client.indices.refresh(index=search_service.index_name)

        retrieved = search_service.get_document(doc_id)
        assert retrieved['title'] == "Updated Title"
        assert retrieved['content'] == "Updated content"

    # Performance Tests

    def test_search_performance_keyword(self, search_service):
        """Test keyword search performance"""
        import time

        start = time.time()
        result = search_service.keyword_search(query="benefits", size=10)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete under 100ms
        assert elapsed_ms < 100, f"Keyword search took {elapsed_ms:.1f}ms (target: <100ms)"

    def test_search_performance_vector(self, search_service):
        """Test vector search performance"""
        import time

        start = time.time()
        result = search_service.vector_search(query="employment benefits", size=10)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete under 400ms
        assert elapsed_ms < 400, f"Vector search took {elapsed_ms:.1f}ms (target: <400ms)"

    def test_search_performance_hybrid(self, search_service):
        """Test hybrid search performance"""
        import time

        start = time.time()
        result = search_service.hybrid_search(query="Canada pension plan", size=10)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete under 500ms
        assert elapsed_ms < 500, f"Hybrid search took {elapsed_ms:.1f}ms (target: <500ms)"

    # Edge Cases and Error Handling

    def test_search_empty_query(self, search_service):
        """Test search with empty query"""
        result = search_service.keyword_search(query="", size=10)

        # Should return results (match all) or handle gracefully
        assert 'hits' in result
        assert 'total' in result

    def test_search_very_long_query(self, search_service):
        """Test search with very long query"""
        long_query = "benefits " * 100

        result = search_service.keyword_search(query=long_query, size=5)

        # Should handle without error
        assert 'hits' in result

    def test_search_special_characters(self, search_service):
        """Test search with special characters"""
        queries = [
            "employment & insurance",
            "section 7(1)",
            "S.C. 1996, c. 23",
            "worker's compensation"
        ]

        for query in queries:
            result = search_service.keyword_search(query=query, size=5)
            assert 'hits' in result

    def test_filter_nonexistent_value(self, search_service):
        """Test filter with nonexistent value"""
        result = search_service.hybrid_search(
            query="benefits",
            filters={'jurisdiction': 'nonexistent_jurisdiction'},
            size=10
        )

        # Should return no results
        assert result['total'] == 0
        assert len(result['hits']) == 0

    def test_get_document_nonexistent(self, search_service):
        """Test getting a document that doesn't exist"""
        result = search_service.get_document("nonexistent-doc-id")

        # Should return None or empty dict
        assert result is None or result == {}

    # Health Check Tests

    def test_health_check(self, search_service):
        """Test search service health check"""
        health = search_service.health_check()

        assert health['status'] in ['healthy', 'degraded']
        assert 'elasticsearch' in health
        assert health['elasticsearch']['available'] is True

    def test_get_stats(self, search_service):
        """Test getting search statistics"""
        stats = search_service.get_stats()

        assert 'index_name' in stats
        assert 'document_count' in stats
        assert stats['document_count'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
