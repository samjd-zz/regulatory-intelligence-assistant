"""
PostgreSQL Full-Text Search Service - Tier 4 Fallback for RAG

This module provides PostgreSQL full-text search capabilities as a fallback
when Elasticsearch and Neo4j searches return no results. It uses PostgreSQL's
ts_vector and ts_query for comprehensive text matching across all documents.

Features:
- Full-text search using PostgreSQL's native FTS
- Metadata-only search for Tier 5 fallback
- Language-aware search (English/French)
- Ranking by text similarity

Author: Developer 2 (AI/ML Engineer)
Created: 2025-12-12
"""

import logging
from typing import Dict, List, Optional, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

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
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search across regulations and sections.
        
        Uses PostgreSQL's ts_vector and ts_query for comprehensive text matching.
        This is a fallback method when Elasticsearch returns no results.
        
        Args:
            query: Search query text
            limit: Maximum number of results (default: 20)
            language: Text search language ('english' or 'french')
            filters: Optional filters (language, jurisdiction, programs)
        
        Returns:
            List of matching documents with scores
        """
        try:
            db = self._get_db()
            
            # Convert query to tsquery format
            # Simple approach: split on whitespace and combine with & (AND)
            query_terms = query.strip().split()
            ts_query = ' & '.join(query_terms)
            
            # Determine which config to use
            ts_config = 'english' if language == 'english' else 'french'
            
            # Build filter clauses
            filter_sql = ""
            filter_params = {}
            
            if filters:
                conditions = []
                
                if 'language' in filters:
                    conditions.append("r.language = :filter_language")
                    filter_params['filter_language'] = filters['language']
                
                if 'jurisdiction' in filters:
                    conditions.append("r.jurisdiction = :filter_jurisdiction")
                    filter_params['filter_jurisdiction'] = filters['jurisdiction']
                
                if 'programs' in filters:
                    # Programs is an array field, use array contains
                    conditions.append(":filter_program = ANY(r.programs)")
                    filter_params['filter_program'] = filters['programs'][0] if isinstance(filters['programs'], list) else filters['programs']
                
                if conditions:
                    filter_sql = " AND " + " AND ".join(conditions)
            
            # Search across both regulations and sections
            # Note: This assumes ts_vector columns exist (will be added in migration)
            sql = text(f"""
                WITH regulation_matches AS (
                    SELECT 
                        r.id,
                        r.title,
                        r.full_text as content,
                        r.citation,
                        '' as section_number,
                        r.jurisdiction,
                        r.programs,
                        r.language,
                        'regulation' as doc_type,
                        ts_rank(
                            to_tsvector(:{ts_config}, coalesce(r.title, '') || ' ' || coalesce(r.full_text, '')),
                            to_tsquery(:{ts_config}, :ts_query)
                        ) as rank
                    FROM regulations r
                    WHERE to_tsvector(:{ts_config}, coalesce(r.title, '') || ' ' || coalesce(r.full_text, '')) @@ to_tsquery(:{ts_config}, :ts_query)
                    {filter_sql}
                ),
                section_matches AS (
                    SELECT 
                        s.id,
                        s.title,
                        s.content,
                        r.citation,
                        s.section_number,
                        r.jurisdiction,
                        r.programs,
                        r.language,
                        'section' as doc_type,
                        ts_rank(
                            to_tsvector(:{ts_config}, coalesce(s.title, '') || ' ' || coalesce(s.content, '')),
                            to_tsquery(:{ts_config}, :ts_query)
                        ) as rank
                    FROM sections s
                    JOIN regulations r ON s.regulation_id = r.id
                    WHERE to_tsvector(:{ts_config}, coalesce(s.title, '') || ' ' || coalesce(s.content, '')) @@ to_tsquery(:{ts_config}, :ts_query)
                    {filter_sql}
                )
                SELECT * FROM (
                    SELECT * FROM regulation_matches
                    UNION ALL
                    SELECT * FROM section_matches
                ) combined
                ORDER BY rank DESC
                LIMIT :limit
            """)
            
            # Execute query
            params = {
                'ts_config': ts_config,
                'ts_query': ts_query,
                'limit': limit,
                **filter_params
            }
            
            result = db.execute(sql, params)
            rows = result.fetchall()
            
            # Format results
            documents = []
            for row in rows:
                documents.append({
                    'id': str(row.id),
                    'title': row.title,
                    'content': row.content[:1500] if row.content else '',  # Truncate for RAG
                    'citation': row.citation or '',
                    'section_number': row.section_number or '',
                    'jurisdiction': row.jurisdiction or '',
                    'programs': row.programs or [],
                    'language': row.language or 'en',
                    'document_type': row.doc_type,
                    'score': float(row.rank)
                })
            
            logger.info(f"PostgreSQL FTS found {len(documents)} documents for query: {query[:50]}...")
            return documents
            
        except Exception as e:
            logger.error(f"PostgreSQL full-text search failed: {e}")
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
        documents that match the metadata filters (program, jurisdiction, language).
        
        Args:
            filters: Metadata filters (must include at least one)
            limit: Maximum number of results
        
        Returns:
            List of documents matching metadata filters
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
            
            if 'programs' in filters:
                programs = filters['programs'] if isinstance(filters['programs'], list) else [filters['programs']]
                conditions.append(":program = ANY(r.programs)")
                params['program'] = programs[0]
            
            if not conditions:
                logger.warning("metadata_only_search: No valid filters provided")
                return []
            
            where_clause = " AND ".join(conditions)
            
            # Query for regulations matching metadata
            sql = text(f"""
                SELECT 
                    r.id,
                    r.title,
                    r.full_text as content,
                    r.citation,
                    r.jurisdiction,
                    r.programs,
                    r.language,
                    'regulation' as doc_type
                FROM regulations r
                WHERE {where_clause}
                ORDER BY r.created_at DESC
                LIMIT :limit
            """)
            
            result = db.execute(sql, params)
            rows = result.fetchall()
            
            # Format results
            documents = []
            for row in rows:
                documents.append({
                    'id': str(row.id),
                    'title': row.title,
                    'content': row.content[:1500] if row.content else '',
                    'citation': row.citation or '',
                    'section_number': '',
                    'jurisdiction': row.jurisdiction or '',
                    'programs': row.programs or [],
                    'language': row.language or 'en',
                    'document_type': row.doc_type,
                    'score': 0.5  # Low confidence - metadata match only
                })
            
            logger.info(f"Metadata-only search found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Metadata-only search failed: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check PostgreSQL search health.
        
        Returns:
            Health status dictionary
        """
        try:
            db = self._get_db()
            
            # Check if we can query the database
            result = db.execute(text("SELECT COUNT(*) FROM regulations"))
            reg_count = result.scalar()
            
            result = db.execute(text("SELECT COUNT(*) FROM sections"))
            sec_count = result.scalar()
            
            return {
                'status': 'healthy',
                'regulations_count': reg_count,
                'sections_count': sec_count,
                'total_documents': reg_count + sec_count,
                'fts_indexes': 'pending_migration'  # Will be updated after migration
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


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
    print("PostgreSQL Search Service - Test")
    print("=" * 80)
    
    service = PostgresSearchService()
    
    # Health check
    print("\n1. Health Check:")
    health = service.health_check()
    print(f"   Status: {health.get('status')}")
    print(f"   Documents: {health.get('total_documents', 0)}")
    
    # Test full-text search
    print("\n2. Full-Text Search Test:")
    query = "employment insurance eligibility"
    results = service.full_text_search(query, limit=5)
    print(f"   Query: '{query}'")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results[:3], 1):
        print(f"   {i}. {doc['title'][:60]}... (score: {doc['score']:.3f})")
    
    # Test metadata-only search
    print("\n3. Metadata-Only Search Test:")
    filters = {'language': 'en', 'jurisdiction': 'federal'}
    results = service.metadata_only_search(filters, limit=5)
    print(f"   Filters: {filters}")
    print(f"   Results: {len(results)}")
    for i, doc in enumerate(results[:3], 1):
        print(f"   {i}. {doc['title'][:60]}...")
    
    print("\n" + "=" * 80)
    print("Test complete!")
