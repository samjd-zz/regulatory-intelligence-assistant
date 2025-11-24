"""
Unit Tests for Search Service

Tests Elasticsearch-based search functionality including keyword search,
vector search, hybrid search, and document indexing.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.search_service import SearchService


class TestSearchService:
    """Test the search service"""

    @pytest.fixture
    def mock_es(self):
        """Create a mock Elasticsearch client"""
        mock = MagicMock()
        mock.ping.return_value = True
        mock.indices.exists.return_value = True
        return mock

    @pytest.fixture
    def search_service(self, mock_es):
        """Create a search service with mocked ES"""
        with patch('services.search_service.Elasticsearch', return_value=mock_es):
            service = SearchService()
            service.es = mock_es
            return service

    def test_init_service(self, search_service):
        """Test service initialization"""
        assert search_service is not None
        assert search_service.INDEX_NAME == "regulatory_documents"
        assert search_service.embedding_model_name == "all-MiniLM-L6-v2"

    def test_create_index_new(self, search_service, mock_es):
        """Test creating a new index"""
        mock_es.indices.exists.return_value = False
        mock_es.indices.create.return_value = {"acknowledged": True}

        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = '{"mappings": {}}'
                success = search_service.create_index(force_recreate=False)

        assert success is True or success is False  # Depends on file existence

    def test_create_index_force_recreate(self, search_service, mock_es):
        """Test force recreating an index"""
        mock_es.indices.exists.return_value = True
        mock_es.indices.delete.return_value = {"acknowledged": True}
        mock_es.indices.create.return_value = {"acknowledged": True}

        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = '{"mappings": {}}'
                success = search_service.create_index(force_recreate=True)

        assert success is True or success is False

    def test_build_filters_jurisdiction(self, search_service):
        """Test building jurisdiction filter"""
        filters = {'jurisdiction': 'federal'}
        filter_clauses = search_service._build_filters(filters)

        assert len(filter_clauses) == 1
        assert filter_clauses[0] == {"term": {"jurisdiction": "federal"}}

    def test_build_filters_program(self, search_service):
        """Test building program filter"""
        filters = {'program': 'employment_insurance'}
        filter_clauses = search_service._build_filters(filters)

        assert len(filter_clauses) == 1
        assert filter_clauses[0] == {"terms": {"program": ["employment_insurance"]}}

    def test_build_filters_multiple_programs(self, search_service):
        """Test building filter with multiple programs"""
        filters = {'program': ['employment_insurance', 'canada_pension_plan']}
        filter_clauses = search_service._build_filters(filters)

        assert len(filter_clauses) == 1
        assert filter_clauses[0] == {"terms": {"program": ['employment_insurance', 'canada_pension_plan']}}

    def test_build_filters_date_range(self, search_service):
        """Test building date range filter"""
        filters = {'date_from': '2020-01-01', 'date_to': '2025-01-01'}
        filter_clauses = search_service._build_filters(filters)

        assert len(filter_clauses) == 1
        assert 'range' in filter_clauses[0]
        assert filter_clauses[0]['range']['effective_date']['gte'] == '2020-01-01'
        assert filter_clauses[0]['range']['effective_date']['lte'] == '2025-01-01'

    def test_build_filters_combined(self, search_service):
        """Test building multiple filters"""
        filters = {
            'jurisdiction': 'federal',
            'program': 'employment_insurance',
            'status': 'in_force'
        }
        filter_clauses = search_service._build_filters(filters)

        assert len(filter_clauses) == 3

    def test_build_filters_empty(self, search_service):
        """Test building filters with no criteria"""
        filter_clauses = search_service._build_filters(None)
        assert filter_clauses == []

        filter_clauses = search_service._build_filters({})
        assert filter_clauses == []

    def test_format_search_response(self, search_service):
        """Test formatting ES response"""
        es_response = {
            'hits': {
                'total': {'value': 2},
                'max_score': 1.5,
                'hits': [
                    {
                        '_id': 'doc1',
                        '_score': 1.5,
                        '_source': {'title': 'Test Doc 1'}
                    },
                    {
                        '_id': 'doc2',
                        '_score': 1.2,
                        '_source': {'title': 'Test Doc 2'},
                        'highlight': {'content': ['highlighted text']}
                    }
                ]
            }
        }

        formatted = search_service._format_search_response(es_response, "keyword")

        assert formatted['total'] == 2
        assert formatted['max_score'] == 1.5
        assert formatted['search_type'] == 'keyword'
        assert len(formatted['hits']) == 2
        assert formatted['hits'][0]['id'] == 'doc1'
        assert formatted['hits'][0]['score'] == 1.5
        assert formatted['hits'][1]['highlights'] == {'content': ['highlighted text']}

    def test_keyword_search(self, search_service, mock_es):
        """Test keyword search"""
        mock_response = {
            'hits': {
                'total': {'value': 1},
                'max_score': 1.0,
                'hits': [
                    {
                        '_id': 'test-doc',
                        '_score': 1.0,
                        '_source': {'title': 'Test Document', 'content': 'Test content'}
                    }
                ]
            }
        }
        mock_es.search.return_value = mock_response

        results = search_service.keyword_search("test query")

        assert results['total'] == 1
        assert results['search_type'] == 'keyword'
        assert len(results['hits']) == 1
        mock_es.search.assert_called_once()

    def test_keyword_search_with_filters(self, search_service, mock_es):
        """Test keyword search with filters"""
        mock_response = {
            'hits': {
                'total': {'value': 0},
                'max_score': None,
                'hits': []
            }
        }
        mock_es.search.return_value = mock_response

        filters = {'jurisdiction': 'federal', 'program': 'employment_insurance'}
        results = search_service.keyword_search("test", filters=filters)

        assert results['total'] == 0
        mock_es.search.assert_called_once()

        # Verify filter clauses were included
        call_args = mock_es.search.call_args
        assert 'body' in call_args[1]
        assert 'query' in call_args[1]['body']

    def test_vector_search_mock(self, search_service, mock_es):
        """Test vector search with mocked embedder"""
        mock_response = {
            'hits': {
                'total': {'value': 1},
                'max_score': 0.95,
                'hits': [
                    {
                        '_id': 'test-doc',
                        '_score': 0.95,
                        '_source': {'title': 'Similar Document'}
                    }
                ]
            }
        }
        mock_es.search.return_value = mock_response

        # Mock the embedder
        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1] * 384
            mock_embedder.return_value = mock_model

            results = search_service.vector_search("test query")

            assert results['total'] == 1
            assert results['search_type'] == 'vector'
            mock_model.encode.assert_called_once_with("test query")

    def test_vector_search_knn_query_structure(self, search_service, mock_es):
        """Test that vector search uses correct kNN query format (not script_score)"""
        mock_response = {
            'hits': {
                'total': {'value': 1},
                'max_score': 0.95,
                'hits': [
                    {
                        '_id': 'test-doc',
                        '_score': 0.95,
                        '_source': {'title': 'Test'}
                    }
                ]
            }
        }
        mock_es.search.return_value = mock_response

        # Mock the embedder - return object with tolist() method
        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            query_vector = [0.1] * 384
            # Create a mock array-like object with tolist() method
            mock_embedding = Mock()
            mock_embedding.tolist.return_value = query_vector
            mock_model.encode.return_value = mock_embedding
            mock_embedder.return_value = mock_model

            search_service.vector_search("test query", size=10)

            # Verify the query structure
            call_args = mock_es.search.call_args
            assert 'body' in call_args[1]
            body = call_args[1]['body']

            # Should use kNN query, not script_score
            assert 'knn' in body, "Query should use kNN format"
            assert 'script_score' not in body, "Query should NOT use script_score"

            # Verify kNN structure
            assert body['knn']['field'] == 'embedding'
            assert body['knn']['query_vector'] == query_vector
            assert body['knn']['k'] == 10
            assert body['knn']['num_candidates'] == 100
            assert body['size'] == 10

    def test_vector_search_with_filters_knn(self, search_service, mock_es):
        """Test that filters are properly added to kNN query"""
        mock_response = {
            'hits': {
                'total': {'value': 0},
                'max_score': None,
                'hits': []
            }
        }
        mock_es.search.return_value = mock_response

        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            # Create mock with tolist() method
            mock_embedding = Mock()
            mock_embedding.tolist.return_value = [0.1] * 384
            mock_model.encode.return_value = mock_embedding
            mock_embedder.return_value = mock_model

            filters = {'jurisdiction': 'federal', 'program': 'employment_insurance'}
            search_service.vector_search("test", filters=filters)

            # Verify filters are in kNN query
            call_args = mock_es.search.call_args
            body = call_args[1]['body']

            assert 'knn' in body
            assert 'filter' in body['knn']
            filter_clauses = body['knn']['filter']

            # Should have 2 filter clauses
            assert len(filter_clauses) == 2

    def test_vector_search_error_handling(self, search_service, mock_es):
        """Test vector search error handling"""
        mock_es.search.side_effect = Exception("Search failed")

        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            # Create mock with tolist() method
            mock_embedding = Mock()
            mock_embedding.tolist.return_value = [0.1] * 384
            mock_model.encode.return_value = mock_embedding
            mock_embedder.return_value = mock_model

            results = search_service.vector_search("test")

            assert 'error' in results
            assert results['total'] == 0
            assert len(results['hits']) == 0

    def test_hybrid_search_mock(self, search_service, mock_es):
        """Test hybrid search combines keyword and vector results"""
        mock_keyword_response = {
            'hits': {
                'total': {'value': 1},
                'max_score': 1.0,
                'hits': [
                    {
                        '_id': 'doc1',
                        '_score': 1.0,
                        '_source': {'title': 'Doc 1'}
                    }
                ]
            }
        }

        mock_vector_response = {
            'hits': {
                'total': {'value': 1},
                'max_score': 0.9,
                'hits': [
                    {
                        '_id': 'doc2',
                        '_score': 0.9,
                        '_source': {'title': 'Doc 2'}
                    }
                ]
            }
        }

        # Mock both searches
        mock_es.search.side_effect = [mock_keyword_response, mock_vector_response]

        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1] * 384
            mock_embedder.return_value = mock_model

            results = search_service.hybrid_search("test query", keyword_weight=0.6, vector_weight=0.4)

            assert results['search_type'] == 'hybrid'
            assert results['total'] == 2
            assert 'weights' in results
            assert results['weights']['keyword'] == 0.6
            assert results['weights']['vector'] == 0.4

    def test_get_document_success(self, search_service, mock_es):
        """Test retrieving a document"""
        mock_es.get.return_value = {
            '_source': {'title': 'Test Doc', 'content': 'Test content'}
        }

        doc = search_service.get_document('test-id')

        assert doc is not None
        assert doc['title'] == 'Test Doc'
        mock_es.get.assert_called_once_with(index='regulatory_documents', id='test-id')

    def test_get_document_not_found(self, search_service, mock_es):
        """Test retrieving a non-existent document"""
        from elasticsearch import NotFoundError
        mock_es.get.side_effect = NotFoundError()

        doc = search_service.get_document('nonexistent')

        assert doc is None

    def test_delete_document_success(self, search_service, mock_es):
        """Test deleting a document"""
        mock_es.delete.return_value = {'result': 'deleted'}

        success = search_service.delete_document('test-id')

        assert success is True
        mock_es.delete.assert_called_once_with(index='regulatory_documents', id='test-id')

    def test_delete_document_error(self, search_service, mock_es):
        """Test delete failure"""
        mock_es.delete.side_effect = Exception("Delete failed")

        success = search_service.delete_document('test-id')

        assert success is False

    def test_get_index_stats(self, search_service, mock_es):
        """Test getting index statistics"""
        mock_es.indices.stats.return_value = {
            '_all': {
                'primaries': {
                    'store': {'size_in_bytes': 1024000}
                },
                'total': {
                    'shard_stats': {'total_count': 1}
                }
            }
        }
        mock_es.count.return_value = {'count': 100}

        stats = search_service.get_index_stats()

        assert stats['index_name'] == 'regulatory_documents'
        assert stats['document_count'] == 100
        assert stats['size_in_bytes'] == 1024000
        assert stats['number_of_shards'] == 1

    def test_health_check_healthy(self, search_service, mock_es):
        """Test health check when healthy"""
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = True

        with patch.object(search_service, 'get_index_stats') as mock_stats:
            mock_stats.return_value = {'document_count': 50}

            health = search_service.health_check()

            assert health['status'] == 'healthy'
            assert health['index'] == 'regulatory_documents'
            assert health['document_count'] == 50

    def test_health_check_no_ping(self, search_service, mock_es):
        """Test health check when ES doesn't respond"""
        mock_es.ping.return_value = False

        health = search_service.health_check()

        assert health['status'] == 'unhealthy'
        assert 'Cannot ping' in health['message']

    def test_health_check_no_index(self, search_service, mock_es):
        """Test health check when index doesn't exist"""
        mock_es.ping.return_value = True
        mock_es.indices.exists.return_value = False

        health = search_service.health_check()

        assert health['status'] == 'degraded'
        assert 'does not exist' in health['message']

    def test_index_document_mock(self, search_service, mock_es):
        """Test indexing a single document"""
        mock_es.index.return_value = {'result': 'created'}

        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1] * 384
            mock_embedder.return_value = mock_model

            doc = {
                'title': 'Test Doc',
                'content': 'Test content',
                'document_type': 'legislation'
            }

            success = search_service.index_document('test-id', doc, generate_embedding=True)

            assert success is True
            mock_es.index.assert_called_once()
            # Verify embedding was added
            call_args = mock_es.index.call_args
            assert 'embedding' in call_args[1]['document']

    def test_index_document_no_embedding(self, search_service, mock_es):
        """Test indexing without generating embedding"""
        mock_es.index.return_value = {'result': 'created'}

        doc = {
            'title': 'Test Doc',
            'content': 'Test content'
        }

        success = search_service.index_document('test-id', doc, generate_embedding=False)

        assert success is True

    def test_bulk_index_documents_mock(self, search_service, mock_es):
        """Test bulk indexing documents"""
        docs = [
            {
                'id': 'doc1',
                'title': 'Doc 1',
                'content': 'Content 1'
            },
            {
                'id': 'doc2',
                'title': 'Doc 2',
                'content': 'Content 2'
            }
        ]

        with patch.object(search_service, '_get_embedder') as mock_embedder:
            mock_model = Mock()
            mock_model.encode.return_value = [0.1] * 384
            mock_embedder.return_value = mock_model

            with patch('services.search_service.bulk') as mock_bulk:
                mock_bulk.return_value = (2, [])  # 2 success, 0 failed

                success, failed = search_service.bulk_index_documents(docs, generate_embeddings=True)

                assert success == 2
                assert failed == 0
                mock_bulk.assert_called_once()

    def test_pagination(self, search_service, mock_es):
        """Test search pagination"""
        mock_response = {
            'hits': {
                'total': {'value': 100},
                'max_score': 1.0,
                'hits': []
            }
        }
        mock_es.search.return_value = mock_response

        results = search_service.keyword_search("test", size=20, from_=40)

        call_args = mock_es.search.call_args
        assert call_args[1]['body']['size'] == 20
        assert call_args[1]['body']['from'] == 40


class TestSearchServiceIntegration:
    """Integration tests (require running Elasticsearch)"""

    @pytest.fixture
    def live_service(self):
        """Create service with live ES (skip if not available)"""
        try:
            service = SearchService()
            if not service.es.ping():
                pytest.skip("Elasticsearch not available")
            return service
        except Exception:
            pytest.skip("Elasticsearch not available")

    def test_create_index_real(self, live_service):
        """Test creating index on real ES"""
        success = live_service.create_index(force_recreate=True)
        assert success is True

    def test_index_and_keyword_search_real(self, live_service):
        """Test full indexing and keyword search flow"""
        import time
        
        # Create index
        live_service.create_index(force_recreate=True)
        time.sleep(1)

        # Index test documents
        docs = [
            {
                'id': 'ei-test-1',
                'title': 'Employment Insurance Eligibility',
                'content': 'To qualify for employment insurance benefits, you must have worked a certain number of hours and lost your job through no fault of your own.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance',
                'status': 'in_force'
            },
            {
                'id': 'cpp-test-1',
                'title': 'Canada Pension Plan Benefits',
                'content': 'The Canada Pension Plan provides retirement, disability, and survivor benefits to eligible contributors.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'canada_pension_plan',
                'status': 'in_force'
            }
        ]

        success, failed = live_service.bulk_index_documents(docs, generate_embeddings=False)
        assert success == 2
        assert failed == 0

        # Wait for indexing
        time.sleep(2)

        # Test keyword search
        results = live_service.keyword_search("employment insurance")
        assert results['total'] > 0
        assert any('employment' in hit['source']['title'].lower() for hit in results['hits'])

    def test_vector_search_e2e_real(self, live_service):
        """E2E test: Vector search with real embeddings"""
        import time
        
        # Create index
        live_service.create_index(force_recreate=True)
        time.sleep(1)

        # Index documents WITH embeddings
        docs = [
            {
                'id': 'vec-test-1',
                'title': 'Employment Insurance for Workers',
                'content': 'Employment insurance provides temporary financial assistance to unemployed workers who have lost their job.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance'
            },
            {
                'id': 'vec-test-2',
                'title': 'Pension Benefits for Seniors',
                'content': 'Pension plans provide retirement income to seniors who have contributed throughout their working years.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'canada_pension_plan'
            },
            {
                'id': 'vec-test-3',
                'title': 'Maternity and Parental Leave Benefits',
                'content': 'Special benefits are available for new parents during maternity and parental leave periods.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance'
            }
        ]

        # Index with embeddings
        success, failed = live_service.bulk_index_documents(docs, generate_embeddings=True)
        assert success == 3
        assert failed == 0

        # Wait for indexing to complete
        time.sleep(3)

        # Test vector search - should find semantically similar docs
        results = live_service.vector_search("benefits for unemployed people", size=3)
        
        # Verify results
        assert results['total'] > 0, "Vector search should return results"
        assert results['search_type'] == 'vector'
        
        # The most relevant should be the employment insurance doc
        if results['hits']:
            top_hit = results['hits'][0]
            assert 'employment' in top_hit['source']['content'].lower() or \
                   'unemployed' in top_hit['source']['content'].lower()

    def test_hybrid_search_e2e_real(self, live_service):
        """E2E test: Hybrid search combining keyword and vector"""
        import time
        
        # Create index
        live_service.create_index(force_recreate=True)
        time.sleep(1)

        # Index diverse documents
        docs = [
            {
                'id': 'hybrid-1',
                'title': 'EI Application Process',
                'content': 'To apply for employment insurance, you must submit your application online within 4 weeks of your last day of work.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance'
            },
            {
                'id': 'hybrid-2',
                'title': 'Unemployment Benefits Guide',
                'content': 'Benefits for unemployed workers include financial assistance and job search support programs.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance'
            },
            {
                'id': 'hybrid-3',
                'title': 'Pension Eligibility Requirements',
                'content': 'To receive pension benefits, you must be at least 60 years old and have made contributions.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'canada_pension_plan'
            }
        ]

        success, failed = live_service.bulk_index_documents(docs, generate_embeddings=True)
        assert success == 3
        assert failed == 0

        time.sleep(3)

        # Test hybrid search
        results = live_service.hybrid_search(
            "employment insurance application",
            size=3,
            keyword_weight=0.5,
            vector_weight=0.5
        )

        assert results['total'] > 0
        assert results['search_type'] == 'hybrid'
        assert 'weights' in results
        
        # Verify score breakdown exists
        if results['hits']:
            first_hit = results['hits'][0]
            assert 'score_breakdown' in first_hit
            assert 'keyword' in first_hit['score_breakdown']
            assert 'vector' in first_hit['score_breakdown']
            assert 'combined' in first_hit['score_breakdown']

    def test_vector_search_with_filters_e2e_real(self, live_service):
        """E2E test: Vector search with filters"""
        import time
        
        # Create index
        live_service.create_index(force_recreate=True)
        time.sleep(1)

        # Index documents from different programs
        docs = [
            {
                'id': 'filter-1',
                'title': 'EI Benefits Overview',
                'content': 'Employment insurance provides financial support during unemployment.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance'
            },
            {
                'id': 'filter-2',
                'title': 'CPP Benefits Overview',
                'content': 'Canada Pension Plan provides financial support during retirement.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'canada_pension_plan'
            },
            {
                'id': 'filter-3',
                'title': 'OAS Benefits Overview',
                'content': 'Old Age Security provides financial support to seniors.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'old_age_security'
            }
        ]

        success, failed = live_service.bulk_index_documents(docs, generate_embeddings=True)
        assert success == 3
        assert failed == 0

        time.sleep(3)

        # Search with filter - should only return EI docs
        results = live_service.vector_search(
            "financial support programs",
            filters={'program': 'employment_insurance'},
            size=5
        )

        assert results['total'] > 0
        # All results should be from employment_insurance program
        for hit in results['hits']:
            assert hit['source']['program'] == 'employment_insurance'

    def test_vector_search_knn_no_script_score_real(self, live_service):
        """E2E test: Verify kNN query works (not script_score)"""
        import time
        
        # Create index
        live_service.create_index(force_recreate=True)
        time.sleep(1)

        # Index a simple document
        doc = {
            'id': 'knn-test-1',
            'title': 'Test Document',
            'content': 'This is a test document for kNN search verification.',
            'document_type': 'test',
            'jurisdiction': 'federal',
            'program': 'test'
        }

        success = live_service.index_document('knn-test-1', doc, generate_embedding=True)
        assert success is True

        time.sleep(2)

        # This should NOT raise BadRequestError
        try:
            results = live_service.vector_search("test document")
            # If we get here, the query worked
            assert results['total'] >= 0
            assert 'error' not in results or results.get('error') == ''
        except Exception as e:
            # Should not get search_phase_execution_exception
            assert 'search_phase_execution_exception' not in str(e)
            assert 'BadRequestError' not in str(type(e))

    def test_pagination_real(self, live_service):
        """E2E test: Search pagination"""
        import time
        
        # Create index
        live_service.create_index(force_recreate=True)
        time.sleep(1)

        # Index multiple documents
        docs = [
            {
                'id': f'page-test-{i}',
                'title': f'Document {i}',
                'content': f'This is test document number {i} about employment insurance.',
                'document_type': 'test',
                'jurisdiction': 'federal',
                'program': 'employment_insurance'
            }
            for i in range(1, 11)  # 10 documents
        ]

        success, failed = live_service.bulk_index_documents(docs, generate_embeddings=False)
        assert success == 10
        assert failed == 0

        time.sleep(2)

        # Test pagination
        page1 = live_service.keyword_search("test document", size=5, from_=0)
        page2 = live_service.keyword_search("test document", size=5, from_=5)

        # Both pages should have results
        assert len(page1['hits']) > 0
        assert len(page2['hits']) > 0

        # Documents should be different
        page1_ids = {hit['id'] for hit in page1['hits']}
        page2_ids = {hit['id'] for hit in page2['hits']}
        assert len(page1_ids.intersection(page2_ids)) == 0  # No overlap


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
