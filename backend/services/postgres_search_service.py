"""
PostgreSQL Full-Text Search Service - Tier 4 Fallback for RAG

This module provides PostgreSQL full-text search capabilities as a fallback
when Elasticsearch and Neo4j searches return no results. It uses PostgreSQL's
ts_vector and ts_query for comprehensive text matching across all documents.

Features:
- Full-text search using PostgreSQL's generated search_vector columns
- Metadata-only search for Tier 5 fallback
- Language-aware search (English/French) with dedicated indexes
- Ranking by text similarity with title boosting
- Query expansion using legal synonyms
- Headline/snippet generation for matched text
- Date range and status filtering

Author: Developer 2 (AI/ML Engineer)
Created: 2025-12-12
Updated: 2025-12-19 - Enhanced with better schema integration
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, date

from database import get_db
from models.models import Regulation, Section

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PostgresSearchService:
    """
    PostgreSQL full-text search service for regulatory documents.
    
    This service is used as Tier 4 in the multi-tier RAG search fallback strategy.
    It provides comprehensive text matching when other search methods fail.
    """
    
    def __init__(self, db: Optional[Session] = None):
        """
        Initialize PostgreSQL search service.
        
        Args:
            db: Database session (creates new if None)
        """
        self.db = db
        
        # Common English stop words that PostgreSQL FTS typically ignores
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'what', 'when', 'where', 'who', 'how'
        }
        
        # Try to import legal synonyms for query expansion
        try:
            from config.legal_synonyms import get_synonyms, detect_program_from_query
            self.get_synonyms = get_synonyms
            self.detect_program = detect_program_from_query
            self.use_synonyms = True
        except ImportError:
            logger.warning("legal_synonyms not available - query expansion disabled")
            self.use_synonyms = False
    
    def _build_ts_query(self, query_text: str) -> str:
        """
        Build a proper PostgreSQL ts_query from user input.
        
        This method:
        1. Removes common English stop words
        2. Handles special characters like slashes (GST/HST -> (GST | HST))
        3. Cleans punctuation
        4. Joins terms with AND operator
        
        Args:
            query_text: Raw user query
            
        Returns:
            Formatted ts_query string
            
        Examples:
            "How is GST/HST calculated?" -> "(GST | HST) & calculated"
            "What is EI eligibility" -> "EI & eligibility"
        """
        words = query_text.split()
        query_terms = []
        
        for word in words:
            word_lower = word.lower().strip()
            
            # Skip stop words
            if word_lower in self.stop_words:
                continue
            
            # Handle slashes (e.g., "GST/HST" becomes "(GST | HST)")
            if '/' in word:
                variants = word.split('/')
                variants_clean = [v.strip() for v in variants if v.strip()]
                if len(variants_clean) > 1:
                    # Create OR group for variants
                    query_terms.append(f"({' | '.join(variants_clean)})".replace('?', '').replace('!', ''))
                elif variants_clean:
                    clean = variants_clean[0].replace('?', '').replace('!', '').strip()
                    if clean:
                        query_terms.append(clean)
            else:
                # Clean special characters but preserve alphanumeric
                clean_word = ''.join(c for c in word if c.isalnum() or c in ('-', '_'))
                if clean_word and clean_word.lower() not in self.stop_words:
                    query_terms.append(clean_word)
        
        # Join with AND operator, fallback to original if no terms extracted
        result = " & ".join(query_terms) if query_terms else query_text
        
        logger.info(f"Built ts_query: '{query_text}' -> '{result}'")
        return result
    
    def _get_db(self) -> Session:
        """Get database session"""
        if self.db:
            return self.db
        return next(get_db())
    
    def full_text_search(
        self,
        query: str,
        limit: int = 20,
        language: str = 'english',
        filters: Optional[Dict[str, Any]] = None,
        include_snippets: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search across regulations and sections.
        
        Uses PostgreSQL's pre-generated search_vector columns with GIN indexes
        for fast full-text search. This is a fallback method when Elasticsearch
        returns no results.
        
        Args:
            query: Search query text
            limit: Maximum number of results (default: 20)
            language: Text search language ('english' or 'french')
            filters: Optional filters (language, jurisdiction, status, date_from, date_to)
            include_snippets: Generate highlighted snippets (default: True)
        
        Returns:
            List of matching documents with scores and optional snippets
        """
        try:
            db = self._get_db()
            
            # Build PostgreSQL ts_query with proper formatting
            ts_query = self._build_ts_query(query)
            
            # Determine which config and column to use
            ts_config = 'english' if language == 'english' else 'french'
            vector_col = 'search_vector' if language == 'english' else 'search_vector_fr'
            
            # Build filter clauses
            filter_conditions = []
            filter_params = {}
            
            if filters:
                if 'language' in filters:
                    filter_conditions.append("r.language = :filter_language")
                    filter_params['filter_language'] = filters['language']
                
                if 'jurisdiction' in filters:
                    filter_conditions.append("r.jurisdiction = :filter_jurisdiction")
                    filter_params['filter_jurisdiction'] = filters['jurisdiction']
                
                if 'status' in filters:
                    filter_conditions.append("r.status = :filter_status")
                    filter_params['filter_status'] = filters['status']
                
                if 'date_from' in filters:
                    filter_conditions.append("r.effective_date >= :date_from")
                    filter_params['date_from'] = filters['date_from']
                
                if 'date_to' in filters:
                    filter_conditions.append("r.effective_date <= :date_to")
                    filter_params['date_to'] = filters['date_to']
            
            filter_sql = (" AND " + " AND ".join(filter_conditions)) if filter_conditions else ""
            
            # Build headline (snippet) generation if requested
            headline_sql = ""
            if include_snippets:
                headline_sql = f"""
                    ts_headline(:ts_config, 
                               COALESCE({{content_field}}, ''), 
                               to_tsquery(:ts_config, :ts_query),
                               'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=25') as snippet,
                """
            else:
                headline_sql = "'' as snippet,"
            
            # Search across both regulations and sections using the pre-generated search_vector columns
            sql_template = f"""
                WITH regulation_matches AS (
                    SELECT 
                        r.id,
                        r.title,
                        SUBSTRING(r.full_text, 1, 1500) as content,
                        r.title as citation,
                        '' as section_number,
                        r.jurisdiction,
                        r.language,
                        r.status,
                        r.effective_date,
                        r.extra_metadata,
                        'regulation' as doc_type,
                        {headline_sql.format(content_field='r.full_text')}
                        ts_rank(r.{vector_col}, to_tsquery(:ts_config, :ts_query)) as rank
                    FROM regulations r
                    WHERE r.{vector_col} @@ to_tsquery(:ts_config, :ts_query)
                    {filter_sql}
                ),
                section_matches AS (
                    SELECT 
                        s.id,
                        COALESCE(s.title, s.section_number) as title,
                        SUBSTRING(s.content, 1, 1500) as content,
                        r.title as citation,
                        s.section_number,
                        r.jurisdiction,
                        r.language,
                        r.status,
                        r.effective_date,
                        s.extra_metadata,
                        'section' as doc_type,
                        {headline_sql.format(content_field='s.content')}
                        ts_rank(s.{vector_col}, to_tsquery(:ts_config, :ts_query)) as rank
                    FROM sections s
                    JOIN regulations r ON s.regulation_id = r.id
                    WHERE s.{vector_col} @@ to_tsquery(:ts_config, :ts_query)
                    {filter_sql}
                )
                SELECT * FROM (
                    SELECT * FROM regulation_matches
                    UNION ALL
                    SELECT * FROM section_matches
                ) combined
                ORDER BY rank DESC, effective_date DESC NULLS LAST
                LIMIT :limit
            """
            
            # Execute query
            params = {
                'ts_config': ts_config,
                'ts_query': ts_query,
                'limit': limit,
                **filter_params
            }
            
            result = db.execute(text(sql_template), params)
            rows = result.fetchall()
            
            # Format results
            documents = []
            for row in rows:
                # Extract programs from metadata if present
                programs = []
                if hasattr(row, 'extra_metadata') and row.extra_metadata:
                    metadata = row.extra_metadata
                    if isinstance(metadata, dict):
                        programs = metadata.get('programs', [])
                        if isinstance(programs, str):
                            programs = [programs]
                
                doc = {
                    'id': str(row.id),
                    'title': row.title,
                    'content': row.content if row.content else '',
                    'citation': row.citation or '',
                    'section_number': row.section_number or '',
                    'jurisdiction': row.jurisdiction or '',
                    'programs': programs,
                    'language': row.language or 'en',
                    'status': row.status or 'active',
                    'document_type': row.doc_type,
                    'score': float(row.rank),
                    'effective_date': row.effective_date.isoformat() if row.effective_date else None
                }
                
                if include_snippets and hasattr(row, 'snippet'):
                    doc['snippet'] = row.snippet
                
                documents.append(doc)
            
            logger.info(f"PostgreSQL FTS found {len(documents)} documents for query: {query[:50]}... (language: {language})")
            return documents
            
        except Exception as e:
            logger.error(f"PostgreSQL full-text search failed: {e}", exc_info=True)
            # Return empty list on error - don't crash the RAG system
            return []
    
    def metadata_only_search(
        self,
        filters: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tier 5 fallback: Search by metadata only (no text matching).
        
        This is the last resort when all text-based searches fail. It returns
        documents that match the metadata filters (jurisdiction, language, status).
        
        Args:
            filters: Metadata filters (must include at least one)
            limit: Maximum number of results
        
        Returns:
            List of documents matching metadata filters, ordered by recency
        """
        try:
            db = self._get_db()
            
            # Build query based on available filters
            conditions = []
            params = {'limit': limit}
            
            if not filters:
                logger.warning("metadata_only_search called with no filters - returning empty")
                return []
            
            if 'language' in filters:
                conditions.append("r.language = :language")
                params['language'] = filters['language']
            
            if 'jurisdiction' in filters:
                conditions.append("r.jurisdiction = :jurisdiction")
                params['jurisdiction'] = filters['jurisdiction']
            
            if 'status' in filters:
                conditions.append("r.status = :status")
                params['status'] = filters['status']
            else:
                # Default to active only if not specified
                conditions.append("r.status = 'active'")
            
            if 'date_from' in filters:
                conditions.append("r.effective_date >= :date_from")
                params['date_from'] = filters['date_from']
            
            if 'date_to' in filters:
                conditions.append("r.effective_date <= :date_to")
                params['date_to'] = filters['date_to']
            
            # Check metadata for programs if specified
            if 'programs' in filters:
                programs = filters['programs'] if isinstance(filters['programs'], list) else [filters['programs']]
                # Use JSONB containment for programs in extra_metadata
                conditions.append("r.extra_metadata @> :programs_json")
                params['programs_json'] = {'programs': programs}
            
            if not conditions:
                logger.warning("metadata_only_search: No valid filters provided")
                return []
            
            where_clause = " AND ".join(conditions)
            
            # Query for regulations matching metadata, ordered by recency and status
            sql_template = f"""
                SELECT 
                    r.id,
                    r.title,
                    SUBSTRING(r.full_text, 1, 1500) as content,
                    r.title as citation,
                    r.jurisdiction,
                    r.language,
                    r.status,
                    r.effective_date,
                    r.extra_metadata,
                    'regulation' as doc_type
                FROM regulations r
                WHERE {where_clause}
                ORDER BY 
                    r.effective_date DESC NULLS LAST,
                    r.created_at DESC
                LIMIT :limit
            """
            
            result = db.execute(text(sql_template), params)
            rows = result.fetchall()
            
            # Format results
            documents = []
            for row in rows:
                # Extract programs from metadata
                programs = []
                if row.extra_metadata and isinstance(row.extra_metadata, dict):
                    programs = row.extra_metadata.get('programs', [])
                    if isinstance(programs, str):
                        programs = [programs]
                
                documents.append({
                    'id': str(row.id),
                    'title': row.title,
                    'content': row.content if row.content else '',
                    'citation': row.citation or '',
                    'section_number': '',
                    'jurisdiction': row.jurisdiction or '',
                    'programs': programs,
                    'language': row.language or 'en',
                    'status': row.status or 'active',
                    'document_type': row.doc_type,
                    'score': 0.5,  # Low confidence - metadata match only
                    'effective_date': row.effective_date.isoformat() if row.effective_date else None
                })
            
            logger.info(f"Metadata-only search found {len(documents)} documents with filters: {filters}")
            return documents
            
        except Exception as e:
            logger.error(f"Metadata-only search failed: {e}", exc_info=True)
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check PostgreSQL search health.
        
        Returns:
            Health status dictionary with document counts and index status
        """
        try:
            db = self._get_db()
            
            # Check if we can query the database
            result = db.execute(text("SELECT COUNT(*) FROM regulations"))
            reg_count = result.scalar()
            
            result = db.execute(text("SELECT COUNT(*) FROM sections"))
            sec_count = result.scalar()
            
            # Check for search_vector indexes
            index_check = db.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename IN ('regulations', 'sections') 
                AND indexname LIKE '%search_vector%'
            """))
            indexes = [row[0] for row in index_check.fetchall()]
            
            # Check for trigram indexes
            trigram_check = db.execute(text("""
                SELECT indexname FROM pg_indexes 
                WHERE tablename IN ('regulations', 'sections') 
                AND indexname LIKE '%trgm%'
            """))
            trigram_indexes = [row[0] for row in trigram_check.fetchall()]
            
            return {
                'status': 'healthy',
                'regulations_count': reg_count,
                'sections_count': sec_count,
                'total_documents': reg_count + sec_count,
                'fts_indexes': indexes,
                'trigram_indexes': trigram_indexes,
                'query_expansion': self.use_synonyms
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def similarity_search(
        self,
        query: str,
        limit: int = 20,
        similarity_threshold: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform similarity search using PostgreSQL's trigram matching.
        
        This is useful for finding documents with similar text even when
        exact word matches don't exist. Uses pg_trgm extension for fuzzy matching.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0.0 to 1.0, default: 0.3)
            filters: Optional metadata filters
        
        Returns:
            List of documents with similarity scores
        """
        try:
            db = self._get_db()
            
            # Build filter conditions
            filter_conditions = []
            filter_params = {'query': query, 'threshold': similarity_threshold, 'limit': limit}
            
            if filters:
                if 'language' in filters:
                    filter_conditions.append("r.language = :filter_language")
                    filter_params['filter_language'] = filters['language']
                
                if 'jurisdiction' in filters:
                    filter_conditions.append("r.jurisdiction = :filter_jurisdiction")
                    filter_params['filter_jurisdiction'] = filters['jurisdiction']
                
                if 'status' in filters:
                    filter_conditions.append("r.status = :filter_status")
                    filter_params['filter_status'] = filters['status']
            
            filter_sql = (" AND " + " AND ".join(filter_conditions)) if filter_conditions else ""
            
            # Use trigram similarity for fuzzy matching
            sql_template = f"""
                WITH regulation_similarities AS (
                    SELECT 
                        r.id,
                        r.title,
                        SUBSTRING(r.full_text, 1, 1500) as content,
                        r.title as citation,
                        '' as section_number,
                        r.jurisdiction,
                        r.language,
                        r.status,
                        r.effective_date,
                        r.extra_metadata,
                        'regulation' as doc_type,
                        GREATEST(
                            similarity(r.title, :query),
                            similarity(COALESCE(r.full_text, ''), :query)
                        ) as similarity_score
                    FROM regulations r
                    WHERE (
                        similarity(r.title, :query) > :threshold
                        OR similarity(COALESCE(r.full_text, ''), :query) > :threshold
                    )
                    {filter_sql}
                ),
                section_similarities AS (
                    SELECT 
                        s.id,
                        COALESCE(s.title, s.section_number) as title,
                        SUBSTRING(s.content, 1, 1500) as content,
                        r.title as citation,
                        s.section_number,
                        r.jurisdiction,
                        r.language,
                        r.status,
                        r.effective_date,
                        s.extra_metadata,
                        'section' as doc_type,
                        GREATEST(
                            similarity(COALESCE(s.title, ''), :query),
                            similarity(s.content, :query)
                        ) as similarity_score
                    FROM sections s
                    JOIN regulations r ON s.regulation_id = r.id
                    WHERE (
                        similarity(COALESCE(s.title, ''), :query) > :threshold
                        OR similarity(s.content, :query) > :threshold
                    )
                    {filter_sql}
                )
                SELECT * FROM (
                    SELECT * FROM regulation_similarities
                    UNION ALL
                    SELECT * FROM section_similarities
                ) combined
                ORDER BY similarity_score DESC, effective_date DESC NULLS LAST
                LIMIT :limit
            """
            
            result = db.execute(text(sql_template), filter_params)
            rows = result.fetchall()
            
            # Format results
            documents = []
            for row in rows:
                # Extract programs from metadata
                programs = []
                if hasattr(row, 'extra_metadata') and row.extra_metadata:
                    if isinstance(row.extra_metadata, dict):
                        programs = row.extra_metadata.get('programs', [])
                        if isinstance(programs, str):
                            programs = [programs]
                
                documents.append({
                    'id': str(row.id),
                    'title': row.title,
                    'content': row.content if row.content else '',
                    'citation': row.citation or '',
                    'section_number': row.section_number or '',
                    'jurisdiction': row.jurisdiction or '',
                    'programs': programs,
                    'language': row.language or 'en',
                    'status': row.status or 'active',
                    'document_type': row.doc_type,
                    'score': float(row.similarity_score),
                    'effective_date': row.effective_date.isoformat() if row.effective_date else None
                })
            
            logger.info(f"Similarity search found {len(documents)} documents (threshold: {similarity_threshold})")
            return documents
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            return []


# Global service instance
_service: Optional[PostgresSearchService] = None


def get_postgres_search_service() -> PostgresSearchService:
    """Get global PostgreSQL search service instance."""
    global _service
    if _service is None:
        _service = PostgresSearchService()
    return _service


if __name__ == "__main__":
    # Test the PostgreSQL search service
    print("=" * 80)
    print("PostgreSQL Search Service - Enhanced Test Suite")
    print("=" * 80)
    
    service = PostgresSearchService()
    
    # Health check
    print("\n1. Health Check:")
    health = service.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   Documents: {health.get('total_documents', 0)}")
    print(f"   FTS Indexes: {len(health.get('fts_indexes', []))}")
    print(f"   Trigram Indexes: {len(health.get('trigram_indexes', []))}")
    print(f"   Query Expansion: {health.get('query_expansion')}")
    
    # Test full-text search with snippets
    print("\n2. Full-Text Search with Snippets:")
    query = "employment insurance eligibility temporary resident"
    results = service.full_text_search(query, limit=3, include_snippets=True)
    print(f"   Query: '{query}'")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"\n   {i}. {doc['title'][:70]}...")
        print(f"      Score: {doc['score']:.4f} | Type: {doc['document_type']}")
        if 'snippet' in doc and doc['snippet']:
            print(f"      Snippet: {doc['snippet'][:100]}...")
    
    # Test full-text search with filters
    print("\n3. Full-Text Search with Filters:")
    filters = {
        'jurisdiction': 'federal',
        'language': 'en',
        'status': 'active'
    }
    results = service.full_text_search(
        "pension plan contributions",
        limit=3,
        filters=filters,
        include_snippets=False
    )
    print(f"   Query: 'pension plan contributions'")
    print(f"   Filters: {filters}")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"   {i}. {doc['title'][:70]}... (score: {doc['score']:.4f})")
    
    # Test similarity search (trigram matching)
    print("\n4. Similarity Search (Fuzzy Matching):")
    results = service.similarity_search(
        "emplyment insuranse",  # Intentional typos
        limit=3,
        similarity_threshold=0.2
    )
    print(f"   Query: 'emplyment insuranse' (with typos)")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"   {i}. {doc['title'][:70]}... (similarity: {doc['score']:.3f})")
    
    # Test metadata-only search
    print("\n5. Metadata-Only Search:")
    filters = {
        'language': 'en',
        'jurisdiction': 'federal',
        'status': 'active'
    }
    results = service.metadata_only_search(filters, limit=5)
    print(f"   Filters: {filters}")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results[:3], 1):
        print(f"   {i}. {doc['title'][:70]}...")
        if doc.get('effective_date'):
            print(f"      Effective: {doc['effective_date']}")
    
    # Test French language search if available
    print("\n6. French Language Search:")
    results = service.full_text_search(
        "assurance emploi",
        limit=3,
        language='french',
        filters={'language': 'fr'}
    )
    print(f"   Query: 'assurance emploi' (French)")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results, 1):
        print(f"   {i}. {doc['title'][:70]}... (score: {doc['score']:.4f})")
    
    print("\n" + "=" * 80)
    print("Enhanced test suite complete!")
    print("=" * 80)
