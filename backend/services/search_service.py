"""
Search Service - Elasticsearch-based Search for Regulatory Documents

This module provides hybrid search capabilities combining:
- Keyword search (BM25) with legal-specific analysis
- Vector search (semantic similarity) using embeddings
- Filtering by jurisdiction, program, document type, etc.
- Result ranking and relevance tuning

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import logging

from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.helpers import bulk
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchService:
    """
    Elasticsearch-based search service for regulatory documents.

    Provides hybrid search combining keyword (BM25) and vector (semantic) search
    with legal-specific text analysis and filtering capabilities.
    """

    INDEX_NAME = "regulatory_documents"

    def __init__(self, es_url: Optional[str] = None, embedding_model: Optional[str] = None):
        """
        Initialize the search service.

        Args:
            es_url: Elasticsearch URL (defaults to env var or localhost)
            embedding_model: Sentence transformer model name
        """
        self.es_url = es_url or os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.es = Elasticsearch([self.es_url])

        # Initialize embedding model for vector search
        self.embedding_model_name = embedding_model or "all-MiniLM-L6-v2"
        self.embedder = None  # Lazy load

        # Verify connection
        if not self.es.ping():
            logger.warning(f"Cannot connect to Elasticsearch at {self.es_url}")
        else:
            logger.info(f"Connected to Elasticsearch at {self.es_url}")

    def _get_embedder(self) -> SentenceTransformer:
        """Lazy load the embedding model"""
        if self.embedder is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self.embedder = SentenceTransformer(self.embedding_model_name)
        return self.embedder

    def create_index(self, force_recreate: bool = False) -> bool:
        """
        Create the Elasticsearch index with legal-specific mappings.

        Args:
            force_recreate: If True, delete existing index first

        Returns:
            True if index created successfully
        """
        try:
            # Check if index exists
            if self.es.indices.exists(index=self.INDEX_NAME):
                if force_recreate:
                    logger.info(f"Deleting existing index: {self.INDEX_NAME}")
                    self.es.indices.delete(index=self.INDEX_NAME)
                else:
                    logger.info(f"Index {self.INDEX_NAME} already exists")
                    return True

            # Load mappings from config file
            config_path = Path(__file__).parent.parent / "config" / "elasticsearch_mappings.json"

            if not config_path.exists():
                logger.error(f"Mappings file not found: {config_path}")
                return False

            with open(config_path, 'r') as f:
                mappings = json.load(f)

            # Create index
            logger.info(f"Creating index: {self.INDEX_NAME}")
            self.es.indices.create(index=self.INDEX_NAME, body=mappings)
            logger.info(f"Index {self.INDEX_NAME} created successfully")

            return True

        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    def index_document(self, doc_id: str, document: Dict[str, Any],
                      generate_embedding: bool = True) -> bool:
        """
        Index a single regulatory document.

        Args:
            doc_id: Unique document identifier
            document: Document data dictionary
            generate_embedding: Whether to generate and include embedding

        Returns:
            True if indexed successfully
        """
        try:
            # Generate embedding if requested
            if generate_embedding and 'embedding' not in document:
                text_to_embed = f"{document.get('title', '')} {document.get('content', '')}"
                embedder = self._get_embedder()
                embedding = embedder.encode(text_to_embed).tolist()
                document['embedding'] = embedding

            # Add timestamps
            if 'created_at' not in document:
                document['created_at'] = datetime.now().isoformat()
            document['updated_at'] = datetime.now().isoformat()

            # Index document
            response = self.es.index(
                index=self.INDEX_NAME,
                id=doc_id,
                document=document
            )

            logger.debug(f"Indexed document {doc_id}: {response['result']}")
            return True

        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False

    def bulk_index_documents(self, documents: List[Dict[str, Any]],
                            generate_embeddings: bool = True) -> Tuple[int, int]:
        """
        Bulk index multiple documents.

        Args:
            documents: List of document dictionaries with 'id' field
            generate_embeddings: Whether to generate embeddings

        Returns:
            Tuple of (success_count, failure_count)
        """
        try:
            # Generate embeddings if requested
            if generate_embeddings:
                embedder = self._get_embedder()
                for doc in documents:
                    if 'embedding' not in doc:
                        text = f"{doc.get('title', '')} {doc.get('content', '')}"
                        doc['embedding'] = embedder.encode(text).tolist()

            # Add timestamps
            now = datetime.now().isoformat()
            for doc in documents:
                if 'created_at' not in doc:
                    doc['created_at'] = now
                doc['updated_at'] = now

            # Prepare bulk actions
            actions = [
                {
                    '_index': self.INDEX_NAME,
                    '_id': doc.pop('id'),
                    '_source': doc
                }
                for doc in documents
            ]

            # Execute bulk index
            success, failed = bulk(self.es, actions, stats_only=True)

            logger.info(f"Bulk indexed: {success} successful, {len(failed)} failed")
            return success, len(failed) if isinstance(failed, list) else 0

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0, len(documents)

    def keyword_search(self, query: str, filters: Optional[Dict] = None,
                      size: int = 10, from_: int = 0) -> Dict[str, Any]:
        """
        Perform keyword-based search using BM25.

        Args:
            query: Search query text
            filters: Filter criteria (jurisdiction, program, etc.)
            size: Number of results to return
            from_: Offset for pagination

        Returns:
            Search results dictionary
        """
        try:
            # Build query
            must_clauses = [
                {
                    "multi_match": {
                        "query": query,
                        "fields": [
                            "title^3",  # Boost title matches
                            "content",
                            "summary^2",
                            "legislation_name^2"
                        ],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                }
            ]

            # Add filters
            filter_clauses = self._build_filters(filters)

            # Construct query
            search_body = {
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "filter": filter_clauses
                    }
                },
                "size": size,
                "from": from_,
                "highlight": {
                    "fields": {
                        "content": {
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        },
                        "title": {},
                        "summary": {}
                    }
                }
            }

            # Execute search
            response = self.es.search(index=self.INDEX_NAME, body=search_body)

            return self._format_search_response(response, "keyword")

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def vector_search(self, query: str, filters: Optional[Dict] = None,
                     size: int = 10, from_: int = 0) -> Dict[str, Any]:
        """
        Perform vector-based semantic search using embeddings.

        Args:
            query: Search query text
            filters: Filter criteria
            size: Number of results to return
            from_: Offset for pagination

        Returns:
            Search results dictionary
        """
        try:
            # Generate query embedding
            embedder = self._get_embedder()
            query_embedding = embedder.encode(query).tolist()

            # Add filters
            filter_clauses = self._build_filters(filters)

            # Construct query
            search_body = {
                "query": {
                    "script_score": {
                        "query": {
                            "bool": {
                                "filter": filter_clauses
                            }
                        },
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {
                                "query_vector": query_embedding
                            }
                        }
                    }
                },
                "size": size,
                "from": from_
            }

            # Execute search
            response = self.es.search(index=self.INDEX_NAME, body=search_body)

            return self._format_search_response(response, "vector")

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def hybrid_search(self, query: str, filters: Optional[Dict] = None,
                     size: int = 10, from_: int = 0,
                     keyword_weight: float = 0.5,
                     vector_weight: float = 0.5) -> Dict[str, Any]:
        """
        Perform hybrid search combining keyword and vector search.

        Args:
            query: Search query text
            filters: Filter criteria
            size: Number of results to return
            from_: Offset for pagination
            keyword_weight: Weight for keyword search (0.0 to 1.0)
            vector_weight: Weight for vector search (0.0 to 1.0)

        Returns:
            Combined and re-ranked search results
        """
        try:
            # Perform both searches
            keyword_results = self.keyword_search(query, filters, size=size*2, from_=from_)
            vector_results = self.vector_search(query, filters, size=size*2, from_=from_)

            # Combine and re-rank results
            combined_scores = {}

            # Add keyword scores
            for hit in keyword_results.get('hits', []):
                doc_id = hit['id']
                combined_scores[doc_id] = {
                    'document': hit,
                    'keyword_score': hit['score'] * keyword_weight,
                    'vector_score': 0.0
                }

            # Add vector scores
            for hit in vector_results.get('hits', []):
                doc_id = hit['id']
                if doc_id in combined_scores:
                    combined_scores[doc_id]['vector_score'] = hit['score'] * vector_weight
                else:
                    combined_scores[doc_id] = {
                        'document': hit,
                        'keyword_score': 0.0,
                        'vector_score': hit['score'] * vector_weight
                    }

            # Calculate combined scores
            for doc_id, scores in combined_scores.items():
                scores['combined_score'] = scores['keyword_score'] + scores['vector_score']
                scores['document']['score'] = scores['combined_score']
                scores['document']['score_breakdown'] = {
                    'keyword': scores['keyword_score'],
                    'vector': scores['vector_score'],
                    'combined': scores['combined_score']
                }

            # Sort by combined score
            sorted_results = sorted(
                combined_scores.values(),
                key=lambda x: x['combined_score'],
                reverse=True
            )

            # Return top results
            final_hits = [item['document'] for item in sorted_results[:size]]

            return {
                "hits": final_hits,
                "total": len(final_hits),
                "search_type": "hybrid",
                "weights": {
                    "keyword": keyword_weight,
                    "vector": vector_weight
                }
            }

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def _build_filters(self, filters: Optional[Dict]) -> List[Dict]:
        """Build Elasticsearch filter clauses from filter dictionary"""
        if not filters:
            return []

        filter_clauses = []

        # Jurisdiction filter
        if 'jurisdiction' in filters:
            filter_clauses.append({"term": {"jurisdiction": filters['jurisdiction']}})

        # Program filter
        if 'program' in filters:
            programs = filters['program'] if isinstance(filters['program'], list) else [filters['program']]
            filter_clauses.append({"terms": {"program": programs}})

        # Document type filter
        if 'document_type' in filters:
            filter_clauses.append({"term": {"document_type": filters['document_type']}})

        # Person type filter
        if 'person_type' in filters:
            person_types = filters['person_type'] if isinstance(filters['person_type'], list) else [filters['person_type']]
            filter_clauses.append({"terms": {"person_types": person_types}})

        # Date range filter
        if 'date_from' in filters or 'date_to' in filters:
            date_range = {}
            if 'date_from' in filters:
                date_range['gte'] = filters['date_from']
            if 'date_to' in filters:
                date_range['lte'] = filters['date_to']
            filter_clauses.append({"range": {"effective_date": date_range}})

        # Status filter
        if 'status' in filters:
            filter_clauses.append({"term": {"status": filters['status']}})

        # Tags filter
        if 'tags' in filters:
            tags = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
            filter_clauses.append({"terms": {"tags": tags}})

        return filter_clauses

    def _format_search_response(self, es_response: Dict, search_type: str) -> Dict[str, Any]:
        """Format Elasticsearch response to standard format"""
        hits = []

        for hit in es_response['hits']['hits']:
            formatted_hit = {
                'id': hit['_id'],
                'score': hit['_score'],
                'source': hit['_source'],
                'search_type': search_type
            }

            # Add highlights if present
            if 'highlight' in hit:
                formatted_hit['highlights'] = hit['highlight']

            hits.append(formatted_hit)

        return {
            'hits': hits,
            'total': es_response['hits']['total']['value'],
            'max_score': es_response['hits']['max_score'],
            'search_type': search_type
        }

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document dictionary or None if not found
        """
        try:
            response = self.es.get(index=self.INDEX_NAME, id=doc_id)
            return response['_source']
        except NotFoundError:
            logger.warning(f"Document not found: {doc_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID"""
        try:
            self.es.delete(index=self.INDEX_NAME, id=doc_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the index"""
        try:
            stats = self.es.indices.stats(index=self.INDEX_NAME)
            count = self.es.count(index=self.INDEX_NAME)

            return {
                'index_name': self.INDEX_NAME,
                'document_count': count['count'],
                'size_in_bytes': stats['_all']['primaries']['store']['size_in_bytes'],
                'number_of_shards': stats['_all']['total']['shard_stats']['total_count']
            }
        except Exception as e:
            logger.error(f"Failed to get index stats: {e}")
            return {}

    def health_check(self) -> Dict[str, Any]:
        """Check Elasticsearch health and connectivity"""
        try:
            if not self.es.ping():
                return {'status': 'unhealthy', 'message': 'Cannot ping Elasticsearch'}

            # Check index exists
            index_exists = self.es.indices.exists(index=self.INDEX_NAME)

            if not index_exists:
                return {
                    'status': 'degraded',
                    'message': f'Index {self.INDEX_NAME} does not exist'
                }

            # Get stats
            stats = self.get_index_stats()

            return {
                'status': 'healthy',
                'elasticsearch_url': self.es_url,
                'index': self.INDEX_NAME,
                'document_count': stats.get('document_count', 0),
                'embedding_model': self.embedding_model_name
            }

        except Exception as e:
            return {'status': 'unhealthy', 'error': str(e)}


if __name__ == "__main__":
    # Test the search service
    print("=" * 80)
    print("Search Service - Test")
    print("=" * 80)

    # Initialize service
    search = SearchService()

    # Check health
    print("\n1. Health Check:")
    health = search.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   Message: {health.get('message', 'OK')}")

    # Create index
    print("\n2. Creating Index:")
    success = search.create_index(force_recreate=True)
    print(f"   Success: {success}")

    # Index sample documents
    print("\n3. Indexing Sample Documents:")
    sample_docs = [
        {
            'id': 'ei-act-s7',
            'title': 'Employment Insurance Act - Section 7',
            'content': 'Unemployment benefits are payable to persons who have lost their employment through no fault of their own and are available for and able to work. Applicants must have a valid social insurance number and be legally authorized to work in Canada.',
            'document_type': 'legislation',
            'jurisdiction': 'federal',
            'program': 'employment_insurance',
            'legislation_name': 'Employment Insurance Act',
            'citation': 'S.C. 1996, c. 23, s. 7',
            'section_number': '7',
            'person_types': ['worker', 'temporary_resident', 'permanent_resident'],
            'requirements': ['social_insurance_number', 'work_permit'],
            'status': 'in_force'
        },
        {
            'id': 'cpp-eligibility',
            'title': 'Canada Pension Plan - Eligibility Requirements',
            'content': 'The Canada Pension Plan provides retirement, disability and survivor benefits. To qualify, you must be at least 18 years old, earn more than the minimum amount, and make valid contributions to the CPP.',
            'document_type': 'regulation',
            'jurisdiction': 'federal',
            'program': 'canada_pension_plan',
            'legislation_name': 'Canada Pension Plan',
            'person_types': ['worker', 'permanent_resident', 'citizen'],
            'status': 'in_force'
        },
        {
            'id': 'oas-overview',
            'title': 'Old Age Security Program Overview',
            'content': 'Old Age Security is a monthly payment available to seniors aged 65 and older. Most Canadian seniors qualify for OAS. You must be a Canadian citizen or legal resident, and have lived in Canada for at least 10 years after age 18.',
            'document_type': 'program_guide',
            'jurisdiction': 'federal',
            'program': 'old_age_security',
            'person_types': ['senior', 'citizen', 'permanent_resident'],
            'status': 'in_force'
        }
    ]

    success, failed = search.bulk_index_documents(sample_docs, generate_embeddings=True)
    print(f"   Indexed: {success} documents, {failed} failed")

    # Wait for indexing
    import time
    time.sleep(2)

    # Test keyword search
    print("\n4. Keyword Search Test:")
    query = "employment insurance eligibility"
    results = search.keyword_search(query, size=3)
    print(f"   Query: '{query}'")
    print(f"   Results: {results['total']}")
    for i, hit in enumerate(results['hits'][:3], 1):
        print(f"   {i}. {hit['source']['title']} (score: {hit['score']:.2f})")

    # Test vector search
    print("\n5. Vector Search Test:")
    query = "pension for seniors"
    results = search.vector_search(query, size=3)
    print(f"   Query: '{query}'")
    print(f"   Results: {results['total']}")
    for i, hit in enumerate(results['hits'][:3], 1):
        print(f"   {i}. {hit['source']['title']} (score: {hit['score']:.2f})")

    # Test hybrid search
    print("\n6. Hybrid Search Test:")
    query = "benefits for temporary residents"
    results = search.hybrid_search(query, size=3)
    print(f"   Query: '{query}'")
    print(f"   Results: {results['total']}")
    for i, hit in enumerate(results['hits'][:3], 1):
        breakdown = hit.get('score_breakdown', {})
        print(f"   {i}. {hit['source']['title']}")
        print(f"      Keyword: {breakdown.get('keyword', 0):.3f}, "
              f"Vector: {breakdown.get('vector', 0):.3f}, "
              f"Combined: {breakdown.get('combined', 0):.3f}")

    # Test with filters
    print("\n7. Filtered Search Test:")
    query = "benefits"
    filters = {'jurisdiction': 'federal', 'program': 'employment_insurance'}
    results = search.keyword_search(query, filters=filters, size=3)
    print(f"   Query: '{query}'")
    print(f"   Filters: {filters}")
    print(f"   Results: {results['total']}")
    for i, hit in enumerate(results['hits'], 1):
        print(f"   {i}. {hit['source']['title']}")

    print("\n" + "=" * 80)
    print("Test complete!")
