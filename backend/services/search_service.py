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
import re
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

# Common Canadian federal act patterns for exact matching
# These patterns extract act names from queries like "Tell me about the Employment Insurance Act"
ACT_NAME_PATTERNS = [
    # Match "the X Act" where X is capitalized words
    r'(?:the\s+)?([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*)\s+Act\b',
    # Match "the X Code" 
    r'(?:the\s+)?([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*)\s+Code\b',
    # Match "the X Regulations"
    r'(?:the\s+)?([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*)*)\s+Regulations?\b',
]


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
    
    def _extract_act_names(self, query: str) -> List[str]:
        """
        Extract potential Act names from the query.
        
        Examples:
            "Tell me about the Employment Insurance Act" -> ["Employment Insurance Act"]
            "What does the Canada Pension Plan Act cover?" -> ["Canada Pension Plan Act"]
            "Criminal Code of Canada" -> ["Criminal Code"]
        
        Returns:
            List of extracted act names
        """
        act_names = []
        
        for pattern in ACT_NAME_PATTERNS:
            # Don't use re.IGNORECASE - we want to match only properly capitalized act names
            # This prevents matching "What does the Excise Tax Act" and instead matches just "Excise Tax Act"
            matches = re.finditer(pattern, query)
            for match in matches:
                # Get the full match (including "Act", "Code", etc.)
                act_name = match.group(0).strip()
                # Remove optional "the " prefix if present
                if act_name.lower().startswith('the '):
                    act_name = act_name[4:]
                if act_name and len(act_name) > 5:  # Filter out very short matches
                    act_names.append(act_name)
        
        return list(set(act_names))  # Remove duplicates
    
    def _detect_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Detect query intent to optimize search strategy.
        
        Returns:
            Dict with intent information:
                - type: "overview", "specific_question", "comparison", etc.
                - act_names: List of detected act names
                - wants_summary: Whether query asks for summary/overview
                - prefers_acts: Whether to prioritize act-level documents
        """
        query_lower = query.lower()
        
        # Extract act names
        act_names = self._extract_act_names(query)
        
        # Detect overview/summary requests (expanded to include coverage questions)
        overview_keywords = ['about', 'overview', 'summary', 'summarize', 'explain', 'what is', 
                            'tell me about', 'describe', 'introduce', 'what does', 'cover']
        wants_summary = any(keyword in query_lower for keyword in overview_keywords)
        
        # Special case: "what does X cover?" is always an overview question
        if 'cover' in query_lower and len(act_names) > 0:
            wants_summary = True
        
        # Detect specific section/subsection questions
        specific_keywords = ['how to', 'can i', 'am i eligible', 'what are the requirements',
                           'section', 'subsection', 'paragraph', 'clause']
        is_specific = any(keyword in query_lower for keyword in specific_keywords)
        
        # Determine if we should prefer act-level documents
        # If act names are detected and NOT asking about specific sections, prefer act-level docs
        prefers_acts = len(act_names) > 0 and not is_specific
        
        return {
            'type': 'overview' if wants_summary else 'specific',
            'act_names': act_names,
            'wants_summary': wants_summary,
            'is_specific': is_specific,
            'prefers_acts': prefers_acts
        }

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
        doc_count = len(documents)
        
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

            # Prepare bulk actions (don't modify original docs)
            actions = [
                {
                    '_index': self.INDEX_NAME,
                    '_id': doc['id'],
                    '_source': {k: v for k, v in doc.items() if k != 'id'}
                }
                for doc in documents
            ]

            # Execute bulk index
            success, failed = bulk(self.es, actions, stats_only=True)

            logger.info(f"Bulk indexed: {success} successful, {len(failed) if isinstance(failed, list) else 0} failed")
            return success, len(failed) if isinstance(failed, list) else 0

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            return 0, doc_count

    def keyword_search(self, query: str, filters: Optional[Dict] = None,
                      size: int = 10, from_: int = 0, boost_sections: bool = False) -> Dict[str, Any]:
        """
        Perform keyword-based search using BM25.

        Args:
            query: Search query text
            filters: Filter criteria (jurisdiction, program, etc.)
            size: Number of results to return
            from_: Offset for pagination
            boost_sections: If True, boost section documents over full acts

        Returns:
            Search results dictionary
        """
        try:
            # Build filter clauses
            filter_clauses = self._build_filters(filters)
            
            # For specific queries (not act overviews), ONLY search sections
            if boost_sections:
                logger.info("🎯 Filtering to ONLY sections for specific query (excluding full acts)")
                filter_clauses.append({"term": {"document_type": "section"}})
            
            # Build multi_match query - use best_fields for more flexible matching
            multi_match_query = {
                "query": query,
                "fields": [
                    "title^1.5",  # Moderate title boost
                    "content^2",   # Boost content heavily for specific queries
                    "summary^1.5",
                    "legislation_name^1.5"
                ],
                "type": "best_fields",
                "operator": "or"
            }
            
            # Only use fuzziness when NOT filtering to sections (fuzziness too strict for multi-term queries)
            if not boost_sections:
                multi_match_query["fuzziness"] = "AUTO"
            else:
                logger.info("🔍 Disabled fuzziness for section-only search")
            
            # Build base query
            base_query = {
                "bool": {
                    "must": [{"multi_match": multi_match_query}],
                    "filter": filter_clauses
                }
            }
            
            search_query = base_query

            # Construct query
            search_body = {
                "query": search_query,
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

            # Log the actual query for debugging
            logger.debug(f"🔍 Keyword query: {json.dumps(search_body, indent=2)}")

            # Execute search
            response = self.es.search(index=self.INDEX_NAME, body=search_body)

            return self._format_search_response(response, "keyword")

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def vector_search(self, query: str, filters: Optional[Dict] = None,
                     size: int = 10, from_: int = 0, boost_sections: bool = False) -> Dict[str, Any]:
        """
        Perform vector-based semantic search using embeddings.

        Args:
            query: Search query text
            filters: Filter criteria
            size: Number of results to return
            from_: Offset for pagination
            boost_sections: If True, filter to ONLY sections (exclude full acts)

        Returns:
            Search results dictionary
        """
        try:
            # Generate query embedding
            embedder = self._get_embedder()
            query_embedding = embedder.encode(query).tolist()

            # Add filters
            filter_clauses = self._build_filters(filters)
            
            # Filter to sections only if requested
            if boost_sections:
                logger.info("🎯 Vector search: Filtering to ONLY sections (excluding full acts)")
                filter_clauses.append({"term": {"document_type": "section"}})

            # Construct kNN query for indexed dense vectors
            search_body = {
                "knn": {
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": size,
                    "num_candidates": min(size * 10, 100)  # Search more candidates for better results
                },
                "size": size
            }

            # Add filters if present - kNN requires bool query wrapper
            if filter_clauses:
                search_body["knn"]["filter"] = {
                    "bool": {
                        "must": filter_clauses
                    }
                }

            # Log the actual query for debugging
            logger.debug(f"🔍 Vector query: {json.dumps(search_body, indent=2)}")

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
        Perform intelligent hybrid search with query-aware boosting.

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
            # Detect query intent for intelligent search optimization
            intent = self._detect_query_intent(query)
            
            # Log intent detection for debugging
            if intent['act_names']:
                logger.info(f"Detected act names in query: {intent['act_names']}")
            logger.info(f"Query intent: {intent['type']}, prefers_acts: {intent['prefers_acts']}")
            
            # Adjust weights based on query type
            # For overview queries about specific acts, favor keyword matching (titles)
            # For complex/specific questions, favor semantic understanding
            if intent['wants_summary'] and intent['act_names']:
                # Override weights for overview queries - heavily favor exact title matches
                keyword_weight = 0.7
                vector_weight = 0.3
                logger.info(f"Adjusted weights for overview query: keyword={keyword_weight}, vector={vector_weight}")
            
            # Perform both searches with section boost for specific queries
            boost_sections = not intent['prefers_acts']
            keyword_results = self.keyword_search(query, filters, size=size*2, from_=from_, boost_sections=boost_sections)
            vector_results = self.vector_search(query, filters, size=size*2, from_=from_, boost_sections=boost_sections)

            # Log what document types we got from Elasticsearch
            keyword_doc_types = {}
            for hit in keyword_results.get('hits', []):
                doc_type = hit.get('source', {}).get('document_type', 'unknown')
                keyword_doc_types[doc_type] = keyword_doc_types.get(doc_type, 0) + 1
            logger.info(f"🔍 Keyword search returned: {keyword_doc_types}")
            
            vector_doc_types = {}
            for hit in vector_results.get('hits', []):
                doc_type = hit.get('source', {}).get('document_type', 'unknown')
                vector_doc_types[doc_type] = vector_doc_types.get(doc_type, 0) + 1
            logger.info(f"🔍 Vector search returned: {vector_doc_types}")

            # Combine and re-rank results
            combined_scores = {}

            # Add keyword scores
            for hit in keyword_results.get('hits', []):
                doc_id = hit['id']
                combined_scores[doc_id] = {
                    'document': hit,
                    'keyword_score': hit['score'] * keyword_weight,
                    'vector_score': 0.0,
                    'title_boost': 0.0,
                    'doc_type_boost': 0.0
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
                        'vector_score': hit['score'] * vector_weight,
                        'title_boost': 0.0,
                        'doc_type_boost': 0.0
                    }

            # Apply intelligent boosting based on query intent
            for doc_id, scores in combined_scores.items():
                doc_source = scores['document']['source']
                doc_title = doc_source.get('title', '').lower()
                legislation_name = doc_source.get('legislation_name', '').lower()
                doc_type = doc_source.get('document_type', '')
                
                # BOOST 1: Exact act name matching (10x boost)
                # If query mentions "Employment Insurance Act", heavily boost docs with that exact title
                for act_name in intent['act_names']:
                    act_name_lower = act_name.lower()
                    if act_name_lower in doc_title or act_name_lower in legislation_name:
                        scores['title_boost'] = 10.0
                        logger.debug(f"Applied title boost to: {doc_title[:50]}...")
                        break
                
                # BOOST 2: Document type preference based on query intent
                # When asking "Tell me about X Act", prefer regulation/act-level docs over sections
                if intent['prefers_acts']:
                    # Boost act-level documents (regulation, legislation, act overview)
                    if doc_type in ['regulation', 'legislation', 'act'] or 'act' in doc_title:
                        # Check if it's NOT a section (sections usually have "section X" in title)
                        if not re.search(r'section\s+\d+', doc_title, re.IGNORECASE):
                            scores['doc_type_boost'] = 5.0
                            logger.debug(f"Applied act-level doc boost to: {doc_title[:50]}...")
                else:
                    # For specific queries (not overview), prefer sections over full acts
                    if doc_type == 'section':
                        scores['doc_type_boost'] = 8.0
                        logger.debug(f"Applied section boost to: {doc_title[:50]}...")
                    elif doc_type in ['regulation', 'legislation', 'act']:
                        # Penalize full acts on specific queries
                        scores['doc_type_boost'] = -3.0
                        logger.debug(f"Applied act penalty to: {doc_title[:50]}...")
                
                # Calculate final combined score with boosts
                scores['combined_score'] = (
                    scores['keyword_score'] + 
                    scores['vector_score'] + 
                    scores['title_boost'] + 
                    scores['doc_type_boost']
                )
                
                scores['document']['score'] = scores['combined_score']
                scores['document']['score_breakdown'] = {
                    'keyword': scores['keyword_score'],
                    'vector': scores['vector_score'],
                    'title_boost': scores['title_boost'],
                    'doc_type_boost': scores['doc_type_boost'],
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
                "search_type": "hybrid_intelligent",
                "intent": intent,
                "weights": {
                    "keyword": keyword_weight,
                    "vector": vector_weight
                },
                "boosts_applied": {
                    "title_boost": "10x for exact act name matches",
                    "doc_type_boost": "5x for act-level documents on overview queries"
                }
            }

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return {"hits": [], "total": 0, "error": str(e)}

    def relaxed_search(self, query: str, filters: Optional[Dict] = None,
                      size: int = 20, language_only: bool = True,
                      use_synonym_expansion: bool = True) -> Dict[str, Any]:
        """
        Perform relaxed search with minimal filters and query expansion.
        
        This is Tier 2 search in the multi-tier RAG system. Used when
        standard search fails to find enough results.
        
        Features:
        - Query expansion using legal term synonyms
        - Minimal filtering (language only by default)
        - Higher result count (default 20)
        - More lenient matching
        
        Args:
            query: Search query text
            filters: Filter criteria (only language filter applied by default)
            size: Number of results to return (default: 20)
            language_only: If True, only apply language filter (default: True)
            use_synonym_expansion: If True, expand query with synonyms (default: True)
        
        Returns:
            Search results dictionary
        """
        try:
            # Import synonym expansion function
            from backend.config.legal_synonyms import expand_query_with_synonyms
            
            # Expand query with synonyms if requested
            expanded_query = query
            if use_synonym_expansion:
                expanded_query = expand_query_with_synonyms(query, max_expansions=3)
                logger.info(f"Query expansion: '{query[:50]}' → '{expanded_query[:100]}'")
            
            # Build minimal filters
            relaxed_filters = {}
            
            if language_only and filters and 'language' in filters:
                # Only keep language filter
                relaxed_filters['language'] = filters['language']
                logger.info(f"Applying language-only filter: {filters['language']}")
            elif not language_only and filters:
                # Use provided filters
                relaxed_filters = filters
            
            # Perform hybrid search with expanded query and relaxed filters
            # Use lower keyword weight to favor semantic understanding
            results = self.hybrid_search(
                query=expanded_query,
                filters=relaxed_filters,
                size=size,
                from_=0,
                keyword_weight=0.4,  # Favor semantic search
                vector_weight=0.6
            )
            
            # Add metadata to indicate this was a relaxed search
            results['search_type'] = 'relaxed_hybrid'
            results['relaxed_search_metadata'] = {
                'original_query': query,
                'expanded_query': expanded_query,
                'synonym_expansion_used': use_synonym_expansion,
                'language_only_filter': language_only,
                'filters_applied': relaxed_filters
            }
            
            logger.info(f"Relaxed search returned {results['total']} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Relaxed search failed: {e}")
            return {
                "hits": [],
                "total": 0,
                "error": str(e),
                "search_type": "relaxed_hybrid"
            }

    def _build_filters(self, filters: Optional[Dict]) -> List[Dict]:
        """Build Elasticsearch filter clauses from filter dictionary"""
        if not filters:
            return []

        filter_clauses = []

        # Jurisdiction filter
        if 'jurisdiction' in filters:
            filter_clauses.append({"term": {"jurisdiction": filters['jurisdiction']}})

        # Program filter (supports both 'program' and 'programs' for backwards compatibility)
        if 'program' in filters:
            programs = filters['program'] if isinstance(filters['program'], list) else [filters['program']]
            filter_clauses.append({"terms": {"programs": programs}})
        elif 'programs' in filters:
            programs = filters['programs'] if isinstance(filters['programs'], list) else [filters['programs']]
            filter_clauses.append({"terms": {"programs": programs}})

        # Document type filter
        if 'document_type' in filters:
            filter_clauses.append({"term": {"document_type": filters['document_type']}})

        # Node type filter (Legislation vs Regulation)
        if 'node_type' in filters:
            filter_clauses.append({"term": {"node_type": filters['node_type']}})

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

        # Language filter
        if 'language' in filters:
            filter_clauses.append({"term": {"language": filters['language']}})

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

    # Test relaxed search
    print("\n6. Relaxed Search Test:")
    query = "temporary resident benefits"
    results = search.relaxed_search(query, size=3, language_only=False)
    print(f"   Query: '{query}'")
    print(f"   Search Type: {results.get('search_type')}")
    if 'relaxed_search_metadata' in results:
        metadata = results['relaxed_search_metadata']
        print(f"   Expanded Query: {metadata.get('expanded_query', '')[:80]}...")
    print(f"   Results: {results['total']}")
    for i, hit in enumerate(results['hits'][:3], 1):
        print(f"   {i}. {hit['source']['title']} (score: {hit['score']:.2f})")

    # Test hybrid search
    print("\n7. Hybrid Search Test:")
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
    print("\n8. Filtered Search Test:")
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
