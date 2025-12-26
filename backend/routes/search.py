"""
Search API Routes - REST Endpoints for Regulatory Document Search

This module provides REST API endpoints for:
- Keyword search (BM25)
- Vector search (semantic similarity)
- Hybrid search (combined keyword + vector)
- Document indexing and management
- Search statistics and health checks

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database import SessionLocal
from services.search_service import SearchService
from services.query_parser import LegalQueryParser
from services.legal_nlp import EntityType
from services.query_history_service import QueryHistoryService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/search", tags=["Search"])

# Initialize services (singleton pattern)
search_service = SearchService()
query_parser = LegalQueryParser(use_spacy=False)
query_history_service = QueryHistoryService()


# Pydantic models for request/response

class SearchRequest(BaseModel):
    """Request model for search queries"""
    query: str = Field(..., description="Search query text", min_length=1)
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    size: int = Field(10, description="Number of results to return", ge=1, le=100)
    from_: int = Field(0, description="Offset for pagination", ge=0, alias="from")
    parse_query: bool = Field(True, description="Use NLP to parse query and extract filters")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Can a temporary resident apply for employment insurance?",
                "filters": {"jurisdiction": "federal"},
                "size": 10,
                "from": 0,
                "parse_query": True
            }
        }


class HybridSearchRequest(SearchRequest):
    """Request model for hybrid search with configurable weights"""
    keyword_weight: float = Field(0.5, description="Weight for keyword search", ge=0.0, le=1.0)
    vector_weight: float = Field(0.5, description="Weight for vector search", ge=0.0, le=1.0)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "employment insurance eligibility",
                "keyword_weight": 0.6,
                "vector_weight": 0.4,
                "size": 10
            }
        }


class SearchResultHit(BaseModel):
    """Individual search result"""
    id: str
    score: float
    source: Dict[str, Any]
    highlights: Optional[Dict[str, List[str]]] = None
    score_breakdown: Optional[Dict[str, float]] = None


class SearchResponse(BaseModel):
    """Response model for search results"""
    success: bool = True
    hits: List[SearchResultHit]
    total: int
    max_score: Optional[float] = None
    search_type: str
    query_info: Optional[Dict[str, Any]] = None
    processing_time_ms: float


class DocumentIndexRequest(BaseModel):
    """Request model for indexing a document"""
    id: str = Field(..., description="Unique document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    document_type: str = Field(..., description="Document type (legislation, regulation, etc.)")
    jurisdiction: Optional[str] = Field(None, description="Jurisdiction (federal, provincial)")
    program: Optional[str] = Field(None, description="Related program")
    legislation_name: Optional[str] = None
    citation: Optional[str] = None
    section_number: Optional[str] = None
    effective_date: Optional[str] = None
    status: Optional[str] = Field("in_force", description="Document status")
    tags: Optional[List[str]] = None
    person_types: Optional[List[str]] = None
    requirements: Optional[List[str]] = None
    summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ei-act-s7",
                "title": "Employment Insurance Act - Section 7",
                "content": "Benefits are payable to persons who have lost employment...",
                "document_type": "legislation",
                "jurisdiction": "federal",
                "program": "employment_insurance",
                "legislation_name": "Employment Insurance Act",
                "citation": "S.C. 1996, c. 23, s. 7",
                "section_number": "7",
                "status": "in_force"
            }
        }


class BulkIndexRequest(BaseModel):
    """Request model for bulk indexing"""
    documents: List[DocumentIndexRequest] = Field(..., min_items=1, max_items=1000)
    generate_embeddings: bool = Field(True, description="Generate embeddings for documents")


class IndexResponse(BaseModel):
    """Response model for indexing operations"""
    success: bool
    document_id: Optional[str] = None
    message: str
    processing_time_ms: float


class BulkIndexResponse(BaseModel):
    """Response model for bulk indexing"""
    success: bool
    indexed_count: int
    failed_count: int
    processing_time_ms: float


class IndexStatsResponse(BaseModel):
    """Response model for index statistics"""
    index_name: str
    document_count: int
    size_in_bytes: int
    number_of_shards: int


# API Endpoints

@router.post("/keyword", response_model=SearchResponse)
async def keyword_search(request: SearchRequest):
    """
    Perform keyword-based search using BM25 algorithm.

    Uses legal-specific text analysis with synonym expansion and fuzzy matching.
    Best for exact term matching and known terminology.

    - **query**: Search query text
    - **filters**: Optional filters (jurisdiction, program, etc.)
    - **size**: Number of results (1-100)
    - **from**: Pagination offset
    - **parse_query**: Use NLP to extract filters from query
    """
    db = SessionLocal()
    try:
        start_time = datetime.now()

        # Parse query with NLP if requested
        filters = request.filters or {}
        query_info = None
        parsed = None

        if request.parse_query:
            parsed = query_parser.parse_query(request.query)
            
            # Only apply program filters if entity confidence is high (> 0.8)
            # This prevents false negatives from low-confidence program detection
            parsed_filters = parsed.filters.copy()
            if 'program' in parsed_filters:
                # Check confidence of program entities
                program_entities = parsed.get_entities_by_type(EntityType.PROGRAM)
                if program_entities:
                    max_confidence = max(e.confidence for e in program_entities)
                    if max_confidence < 0.8:
                        # Remove low-confidence program filter
                        del parsed_filters['program']
                        logger.info(f"Skipped low-confidence program filter (confidence: {max_confidence:.2f})")
            
            # Merge high-confidence parsed filters with provided filters
            filters.update(parsed_filters)
            query_info = {
                "intent": parsed.intent.value,
                "intent_confidence": parsed.intent_confidence,
                "keywords": parsed.keywords,
                "entities": [e.to_dict() for e in parsed.entities[:5]]  # Limit for response size
            }

        # Perform search
        results = search_service.keyword_search(
            query=request.query,
            filters=filters,
            size=request.size,
            from_=request.from_
        )

        # Format response
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Log query history (non-blocking)
        try:
            user = query_history_service.get_default_citizen_user(db)
            if user:
                entities = query_history_service.extract_entities_from_parsed_query(parsed) if parsed else {}
                intent = query_info.get('intent') if query_info else None
                formatted_results = query_history_service.format_search_results(results)
                
                query_history_service.log_query(
                    db=db,
                    user_id=user.id,
                    query=request.query,
                    entities=entities,
                    intent=intent,
                    results=formatted_results
                )
        except Exception as e:
            logger.error(f"Failed to log query history: {e}")

        return SearchResponse(
            hits=[SearchResultHit(**hit) for hit in results['hits']],
            total=results['total'],
            max_score=results.get('max_score'),
            search_type=results['search_type'],
            query_info=query_info,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Keyword search failed: {str(e)}"
        )
    finally:
        db.close()


@router.post("/vector", response_model=SearchResponse)
async def vector_search(request: SearchRequest):
    """
    Perform vector-based semantic search using embeddings.

    Uses sentence transformers to understand query meaning beyond exact words.
    Best for conceptual searches and finding similar content.

    - **query**: Search query text
    - **filters**: Optional filters
    - **size**: Number of results (1-100)
    - **from**: Pagination offset
    - **parse_query**: Use NLP to extract filters from query
    """
    db = SessionLocal()
    try:
        start_time = datetime.now()

        # Parse query with NLP if requested
        filters = request.filters or {}
        query_info = None
        parsed = None

        if request.parse_query:
            parsed = query_parser.parse_query(request.query)
            
            # Only apply program filters if entity confidence is high (> 0.8)
            parsed_filters = parsed.filters.copy()
            if 'program' in parsed_filters:
                program_entities = parsed.get_entities_by_type(EntityType.PROGRAM)
                if program_entities:
                    max_confidence = max(e.confidence for e in program_entities)
                    if max_confidence < 0.8:
                        del parsed_filters['program']
                        logger.info(f"Skipped low-confidence program filter (confidence: {max_confidence:.2f})")
            
            filters.update(parsed_filters)
            query_info = {
                "intent": parsed.intent.value,
                "intent_confidence": parsed.intent_confidence,
                "keywords": parsed.keywords
            }

        # Perform search
        results = search_service.vector_search(
            query=request.query,
            filters=filters,
            size=request.size,
            from_=request.from_
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Log query history (non-blocking)
        try:
            user = query_history_service.get_default_citizen_user(db)
            if user:
                entities = query_history_service.extract_entities_from_parsed_query(parsed) if parsed else {}
                intent = query_info.get('intent') if query_info else None
                formatted_results = query_history_service.format_search_results(results)
                
                query_history_service.log_query(
                    db=db,
                    user_id=user.id,
                    query=request.query,
                    entities=entities,
                    intent=intent,
                    results=formatted_results
                )
        except Exception as e:
            logger.error(f"Failed to log query history: {e}")

        return SearchResponse(
            hits=[SearchResultHit(**hit) for hit in results['hits']],
            total=results['total'],
            max_score=results.get('max_score'),
            search_type=results['search_type'],
            query_info=query_info,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )
    finally:
        db.close()


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    """
    Perform hybrid search combining keyword and vector search.

    Combines BM25 keyword matching with semantic vector search for best results.
    Configurable weights allow tuning for specific use cases.

    - **query**: Search query text
    - **keyword_weight**: Weight for BM25 search (0.0-1.0)
    - **vector_weight**: Weight for semantic search (0.0-1.0)
    - **filters**: Optional filters
    - **size**: Number of results (1-100)
    - **parse_query**: Use NLP to extract filters from query
    """
    db = SessionLocal()
    try:
        start_time = datetime.now()

        # Parse query with NLP if requested
        filters = request.filters or {}
        query_info = None
        parsed = None

        if request.parse_query:
            parsed = query_parser.parse_query(request.query)
            
            # Only apply program filters if entity confidence is high (> 0.8)
            parsed_filters = parsed.filters.copy()
            if 'program' in parsed_filters:
                program_entities = parsed.get_entities_by_type(EntityType.PROGRAM)
                if program_entities:
                    max_confidence = max(e.confidence for e in program_entities)
                    if max_confidence < 0.8:
                        del parsed_filters['program']
                        logger.info(f"Skipped low-confidence program filter (confidence: {max_confidence:.2f})")
            
            filters.update(parsed_filters)
            query_info = {
                "intent": parsed.intent.value,
                "intent_confidence": parsed.intent_confidence,
                "keywords": parsed.keywords,
                "entities": [e.to_dict() for e in parsed.entities[:5]]
            }

        # Perform search
        results = search_service.hybrid_search(
            query=request.query,
            filters=filters,
            size=request.size,
            from_=request.from_,
            keyword_weight=request.keyword_weight,
            vector_weight=request.vector_weight
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Log query history (non-blocking)
        try:
            user = query_history_service.get_default_citizen_user(db)
            if user:
                entities = query_history_service.extract_entities_from_parsed_query(parsed) if parsed else {}
                intent = query_info.get('intent') if query_info else None
                formatted_results = query_history_service.format_search_results(results)
                
                query_history_service.log_query(
                    db=db,
                    user_id=user.id,
                    query=request.query,
                    entities=entities,
                    intent=intent,
                    results=formatted_results
                )
        except Exception as e:
            logger.error(f"Failed to log query history: {e}")

        return SearchResponse(
            hits=[SearchResultHit(**hit) for hit in results['hits']],
            total=results['total'],
            search_type=results['search_type'],
            query_info=query_info,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hybrid search failed: {str(e)}"
        )
    finally:
        db.close()


@router.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """
    Retrieve a single document by ID.

    - **doc_id**: Unique document identifier
    """
    try:
        document = search_service.get_document(doc_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}"
            )

        return {
            "success": True,
            "id": doc_id,
            "document": document
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.get("/regulation/{regulation_id}")
async def get_regulation(regulation_id: str):
    """
    Get full regulation details including all sections.

    - **regulation_id**: Regulation UUID
    """
    from database import SessionLocal
    from models.models import Regulation, Section
    from uuid import UUID
    
    db = SessionLocal()
    
    try:
        # Parse UUID
        try:
            reg_uuid = UUID(regulation_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid regulation ID format"
            )
        
        # Get regulation
        regulation = db.query(Regulation).filter_by(id=reg_uuid).first()
        
        if not regulation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Regulation not found: {regulation_id}"
            )
        
        # Get all sections
        sections = db.query(Section).filter_by(
            regulation_id=reg_uuid
        ).order_by(Section.section_number).all()
        
        # Extract citation from extra_metadata if available
        citation = None
        if regulation.extra_metadata:
            citation = regulation.extra_metadata.get('act_number') or \
                      regulation.extra_metadata.get('chapter')
        if not citation:
            citation = regulation.authority
        
        return {
            "success": True,
            "id": str(regulation.id),
            "title": regulation.title,
            "citation": citation,
            "jurisdiction": regulation.jurisdiction,
            "authority": regulation.authority,
            "effective_date": regulation.effective_date.isoformat() if regulation.effective_date else None,
            "status": regulation.status,
            "full_text": regulation.full_text,
            "sections": [
                {
                    "id": str(s.id),
                    "number": s.section_number,
                    "title": s.title,
                    "content": s.content
                }
                for s in sections
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve regulation: {str(e)}"
        )
    finally:
        db.close()


@router.post("/index", response_model=IndexResponse)
async def index_document(request: DocumentIndexRequest):
    """
    Index a single regulatory document.

    Automatically generates embeddings for vector search.

    - **id**: Unique document ID
    - **title**: Document title
    - **content**: Document content/text
    - **document_type**: Type (legislation, regulation, program_guide, etc.)
    - Additional metadata fields
    """
    try:
        start_time = datetime.now()

        # Convert request to dictionary
        doc_dict = request.model_dump(exclude={'id'})

        # Index document
        success = search_service.index_document(
            doc_id=request.id,
            document=doc_dict,
            generate_embedding=True
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        if success:
            return IndexResponse(
                success=True,
                document_id=request.id,
                message="Document indexed successfully",
                processing_time_ms=processing_time
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to index document"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document indexing failed: {str(e)}"
        )


@router.post("/index/bulk", response_model=BulkIndexResponse)
async def bulk_index_documents(request: BulkIndexRequest):
    """
    Bulk index multiple documents for efficient processing.

    Maximum 1000 documents per request.

    - **documents**: List of documents to index
    - **generate_embeddings**: Whether to generate embeddings (default: true)
    """
    try:
        start_time = datetime.now()

        # Convert documents to list of dicts
        docs = []
        for doc_req in request.documents:
            doc_dict = doc_req.model_dump()
            docs.append(doc_dict)

        # Bulk index
        success_count, failed_count = search_service.bulk_index_documents(
            documents=docs,
            generate_embeddings=request.generate_embeddings
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return BulkIndexResponse(
            success=failed_count == 0,
            indexed_count=success_count,
            failed_count=failed_count,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk indexing failed: {str(e)}"
        )


@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document from the index.

    - **doc_id**: Document ID to delete
    """
    try:
        success = search_service.delete_document(doc_id)

        if success:
            return {
                "success": True,
                "message": f"Document {doc_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {doc_id}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/index/create")
async def create_index(force_recreate: bool = Query(False)):
    """
    Create or recreate the Elasticsearch index.

    - **force_recreate**: Delete existing index first (default: false)

    **Warning**: Setting force_recreate=true will delete all indexed documents!
    """
    try:
        success = search_service.create_index(force_recreate=force_recreate)

        if success:
            return {
                "success": True,
                "message": f"Index {search_service.INDEX_NAME} created successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create index"
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Index creation failed: {str(e)}"
        )


@router.get("/stats", response_model=IndexStatsResponse)
async def get_index_stats():
    """
    Get statistics about the search index.

    Returns document count, index size, and shard information.
    """
    try:
        stats = search_service.get_index_stats()

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to retrieve index statistics"
            )

        return IndexStatsResponse(**stats)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/health")
async def search_health_check():
    """
    Health check for search service.

    Returns status of Elasticsearch connection, index, and embedding model.
    """
    try:
        health = search_service.health_check()

        if health.get('status') == 'healthy':
            return health
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/analyze")
async def analyze_query(
    query: str = Query(..., description="Query to analyze"),
    extract_filters: bool = Query(True, description="Extract filters from query")
):
    """
    Analyze a query using NLP without performing search.

    Useful for understanding how a query will be processed.

    - **query**: Query text to analyze
    - **extract_filters**: Extract filters from entities
    """
    try:
        parsed = query_parser.parse_query(query)

        return {
            "success": True,
            "original_query": parsed.original_query,
            "normalized_query": parsed.normalized_query,
            "intent": parsed.intent.value,
            "intent_confidence": parsed.intent_confidence,
            "question_type": parsed.question_type,
            "keywords": parsed.keywords,
            "entities": [e.to_dict() for e in parsed.entities],
            "filters": parsed.filters if extract_filters else {},
            "entity_summary": parsed.metadata.get('entity_summary', {})
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query analysis failed: {str(e)}"
        )
