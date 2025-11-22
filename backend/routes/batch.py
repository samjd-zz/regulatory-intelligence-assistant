"""
Batch Processing API Routes

Provides REST API endpoints for batch operations including:
- Bulk document indexing
- Batch search operations
- Bulk RAG question answering
- Batch NLP processing
- Job progress tracking

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from utils.regulatory_batch import (
    RegulatoryBatchAPI,
    DocumentBatchItem,
    SearchBatchItem,
    RAGBatchItem,
    NLPBatchItem
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/batch", tags=["Batch Operations"])

# Initialize batch API
batch_api = RegulatoryBatchAPI()


# === Request/Response Models ===

class DocumentBatchRequest(BaseModel):
    """Request for batch document indexing"""
    documents: List[Dict[str, Any]] = Field(..., description="Documents to index")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "title": "Employment Insurance Act - Section 7",
                        "content": "Benefits are payable...",
                        "jurisdiction": "federal",
                        "document_type": "act",
                        "authority": "Parliament of Canada"
                    }
                ]
            }
        }


class SearchBatchRequest(BaseModel):
    """Request for batch search operations"""
    queries: List[Dict[str, Any]] = Field(..., description="Search queries")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "queries": [
                    {
                        "query": "employment insurance eligibility",
                        "search_type": "hybrid",
                        "size": 10
                    },
                    {
                        "query": "pension benefits",
                        "search_type": "keyword",
                        "size": 5
                    }
                ]
            }
        }


class RAGBatchRequest(BaseModel):
    """Request for batch RAG question answering"""
    questions: List[str] = Field(..., description="Questions to answer")
    num_context_docs: int = Field(5, description="Context documents per question")
    use_cache: bool = Field(True, description="Use cached answers if available")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "questions": [
                    "What is the Canada Pension Plan?",
                    "Who is eligible for employment insurance?"
                ],
                "num_context_docs": 5,
                "use_cache": true
            }
        }


class NLPBatchRequest(BaseModel):
    """Request for batch NLP processing"""
    texts: List[str] = Field(..., description="Texts to process")
    extract_entities: bool = Field(True, description="Extract named entities")
    parse_query: bool = Field(True, description="Parse as legal query")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "texts": [
                    "Can permanent residents apply for employment insurance?",
                    "What are the pension eligibility requirements?"
                ],
                "extract_entities": true,
                "parse_query": true
            }
        }


class BatchJobResponse(BaseModel):
    """Response for batch job submission"""
    success: bool = True
    job_id: str
    message: str
    total_items: int
    submitted_at: str


class BatchProgressResponse(BaseModel):
    """Response for batch job progress"""
    job_id: str
    status: str
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    progress_percentage: float
    success_rate: float
    elapsed_time_seconds: float
    estimated_completion: Optional[str] = None
    error_count: int = 0


class BatchResultResponse(BaseModel):
    """Response for completed batch job"""
    job_id: str
    total_items: int
    successful_items: int
    failed_items: int
    success_rate: float
    execution_time_seconds: float
    results: List[Any]
    failures: List[Dict[str, Any]]


# === API Endpoints ===

@router.post("/documents/index", response_model=BatchResultResponse, status_code=status.HTTP_200_OK)
async def batch_index_documents(request: DocumentBatchRequest):
    """
    Index multiple regulatory documents in batch

    Processes documents in parallel with automatic retry on failures.
    Returns results including successful and failed documents.

    - **documents**: List of documents with metadata and content
    - **job_id**: Optional identifier for tracking (auto-generated if not provided)

    Returns indexing results for all documents.
    """
    try:
        # Convert to DocumentBatchItem objects
        doc_items = []
        for doc in request.documents:
            item = DocumentBatchItem(
                title=doc.get('title', ''),
                content=doc.get('content', ''),
                jurisdiction=doc.get('jurisdiction', 'unknown'),
                document_type=doc.get('document_type', 'regulation'),
                authority=doc.get('authority'),
                effective_date=doc.get('effective_date'),
                citation=doc.get('citation'),
                metadata=doc.get('metadata', {})
            )
            doc_items.append(item)

        # Process batch
        result = batch_api.batch_index_documents(doc_items, job_id=request.job_id)

        return BatchResultResponse(
            job_id=result.job_id,
            total_items=result.total_items,
            successful_items=result.success_count,
            failed_items=result.failure_count,
            success_rate=result.success_rate,
            execution_time_seconds=result.execution_time_seconds,
            results=[r.__dict__ for r in result.successful_results],
            failures=result.failed_items
        )

    except Exception as e:
        logger.error(f"Batch document indexing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch indexing failed: {str(e)}"
        )


@router.post("/search", response_model=BatchResultResponse, status_code=status.HTTP_200_OK)
async def batch_search(request: SearchBatchRequest):
    """
    Execute multiple search queries in batch

    Processes search queries in parallel for improved throughput.
    Supports keyword, vector, and hybrid search.

    - **queries**: List of search queries with parameters
    - **job_id**: Optional identifier for tracking

    Returns search results for all queries.
    """
    try:
        # Convert to SearchBatchItem objects
        search_items = []
        for query in request.queries:
            item = SearchBatchItem(
                query=query.get('query', ''),
                filters=query.get('filters'),
                size=query.get('size', 10),
                search_type=query.get('search_type', 'hybrid')
            )
            search_items.append(item)

        # Process batch
        result = batch_api.batch_search(search_items, job_id=request.job_id)

        return BatchResultResponse(
            job_id=result.job_id,
            total_items=result.total_items,
            successful_items=result.success_count,
            failed_items=result.failure_count,
            success_rate=result.success_rate,
            execution_time_seconds=result.execution_time_seconds,
            results=[r.__dict__ for r in result.successful_results],
            failures=result.failed_items
        )

    except Exception as e:
        logger.error(f"Batch search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch search failed: {str(e)}"
        )


@router.post("/rag/answer", response_model=BatchResultResponse, status_code=status.HTTP_200_OK)
async def batch_answer_questions(request: RAGBatchRequest):
    """
    Answer multiple questions using RAG in batch

    Processes questions in parallel with rate limiting to respect API quotas.
    Uses caching to improve performance for repeated questions.

    - **questions**: List of questions to answer
    - **num_context_docs**: Number of context documents per question
    - **use_cache**: Whether to use cached answers
    - **job_id**: Optional identifier for tracking

    Returns answers with citations for all questions.
    """
    try:
        # Convert to RAGBatchItem objects
        question_items = [
            RAGBatchItem(
                question=q,
                num_context_docs=request.num_context_docs,
                use_cache=request.use_cache
            )
            for q in request.questions
        ]

        # Process batch
        result = batch_api.batch_answer_questions(question_items, job_id=request.job_id)

        return BatchResultResponse(
            job_id=result.job_id,
            total_items=result.total_items,
            successful_items=result.success_count,
            failed_items=result.failure_count,
            success_rate=result.success_rate,
            execution_time_seconds=result.execution_time_seconds,
            results=[r.__dict__ for r in result.successful_results],
            failures=result.failed_items
        )

    except Exception as e:
        logger.error(f"Batch RAG processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch RAG processing failed: {str(e)}"
        )


@router.post("/nlp/process", response_model=BatchResultResponse, status_code=status.HTTP_200_OK)
async def batch_nlp_processing(request: NLPBatchRequest):
    """
    Process multiple texts with NLP in batch

    Extracts entities and parses legal queries in parallel.
    Uses process-based parallelism for CPU-intensive NLP operations.

    - **texts**: List of texts to process
    - **extract_entities**: Extract named entities
    - **parse_query**: Parse as legal query
    - **job_id**: Optional identifier for tracking

    Returns NLP results for all texts.
    """
    try:
        # Convert to NLPBatchItem objects
        nlp_items = [
            NLPBatchItem(
                text=text,
                extract_entities=request.extract_entities,
                parse_query=request.parse_query
            )
            for text in request.texts
        ]

        # Process batch
        result = batch_api.batch_nlp_processing(nlp_items, job_id=request.job_id)

        return BatchResultResponse(
            job_id=result.job_id,
            total_items=result.total_items,
            successful_items=result.success_count,
            failed_items=result.failure_count,
            success_rate=result.success_rate,
            execution_time_seconds=result.execution_time_seconds,
            results=[r.__dict__ for r in result.successful_results],
            failures=result.failed_items
        )

    except Exception as e:
        logger.error(f"Batch NLP processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch NLP processing failed: {str(e)}"
        )


@router.get("/jobs/{job_id}/progress", response_model=BatchProgressResponse)
async def get_batch_job_progress(
    job_id: str,
    job_type: str = "document"
):
    """
    Get progress for a batch job

    Tracks processing status including completed items, failures,
    and estimated completion time.

    - **job_id**: Job identifier
    - **job_type**: Type of job (document, search, rag, nlp)

    Returns current progress information.
    """
    try:
        progress = batch_api.get_job_progress(job_id, job_type)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )

        return BatchProgressResponse(
            job_id=progress.job_id,
            status=progress.status.value,
            total_items=progress.total_items,
            processed_items=progress.processed_items,
            successful_items=progress.successful_items,
            failed_items=progress.failed_items,
            progress_percentage=progress.progress_percentage,
            success_rate=progress.success_rate,
            elapsed_time_seconds=progress.elapsed_time_seconds,
            estimated_completion=progress.estimated_completion.isoformat() if progress.estimated_completion else None,
            error_count=len(progress.error_messages)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job progress: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job progress: {str(e)}"
        )


@router.get("/health")
async def batch_service_health():
    """
    Health check for batch processing service

    Returns service status and current workload.
    """
    try:
        return {
            "status": "healthy",
            "service": "batch_processing",
            "processors": {
                "document": "available",
                "search": "available",
                "rag": "available",
                "nlp": "available"
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "degraded",
            "service": "batch_processing",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
