"""
RAG API Routes - REST Endpoints for Legal Question Answering

This module provides REST API endpoints for RAG-based Q&A:
- Question answering with citations
- Confidence scoring
- Cache management
- Health checks

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.rag_service import RAGService, RAGAnswer

# Create router
router = APIRouter(prefix="/api/rag", tags=["RAG"])

# Initialize RAG service (singleton pattern)
rag_service = RAGService()


# Pydantic models for request/response

class QuestionRequest(BaseModel):
    """Request model for asking a question"""
    question: str = Field(..., description="Question to answer", min_length=5)
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters for context retrieval")
    num_context_docs: int = Field(5, description="Number of context documents to use", ge=1, le=20)
    use_cache: bool = Field(True, description="Use cached answers if available")
    temperature: float = Field(0.3, description="LLM temperature (0.0-1.0)", ge=0.0, le=1.0)
    max_tokens: int = Field(1024, description="Maximum tokens in answer", ge=100, le=4096)

    class Config:
        json_schema_extra = {
            "example": {
                "question": "Can a temporary resident apply for employment insurance?",
                "filters": {"jurisdiction": "federal"},
                "num_context_docs": 5,
                "use_cache": True,
                "temperature": 0.3
            }
        }


class CitationResponse(BaseModel):
    """Citation in the answer"""
    text: str
    document_id: Optional[str]
    document_title: Optional[str]
    section: Optional[str]
    confidence: float


class SourceDocumentResponse(BaseModel):
    """Source document used for context"""
    id: str
    title: str
    citation: Optional[str]
    section_number: Optional[str]
    score: float
    content_preview: Optional[str] = None


class AnswerResponse(BaseModel):
    """Response model for Q&A"""
    success: bool = True
    question: str
    answer: str
    citations: List[CitationResponse]
    confidence_score: float
    source_documents: List[SourceDocumentResponse]
    intent: Optional[str]
    processing_time_ms: float
    cached: bool
    metadata: Dict[str, Any]


class BatchQuestionRequest(BaseModel):
    """Request model for batch Q&A"""
    questions: List[str] = Field(..., min_items=1, max_items=10, description="List of questions")
    filters: Optional[Dict[str, Any]] = None
    num_context_docs: int = Field(5, ge=1, le=20)
    use_cache: bool = True


class BatchAnswerResponse(BaseModel):
    """Response model for batch Q&A"""
    success: bool = True
    answers: List[AnswerResponse]
    total_questions: int
    total_processing_time_ms: float


# API Endpoints

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question and get an AI-generated answer with citations.

    Uses Retrieval-Augmented Generation (RAG) to:
    1. Search for relevant regulatory documents
    2. Generate answer using Gemini API with document context
    3. Extract citations and calculate confidence score
    4. Cache result for future requests

    - **question**: Question to answer (min 5 characters)
    - **filters**: Optional search filters (jurisdiction, program, etc.)
    - **num_context_docs**: Number of documents to use as context (1-20, default: 5)
    - **use_cache**: Whether to use cached answers (default: true)
    - **temperature**: LLM sampling temperature (0.0-1.0, default: 0.3)
    - **max_tokens**: Maximum tokens in answer (100-4096, default: 1024)

    Returns answer with citations, confidence score, and source documents.
    """
    try:
        start_time = datetime.now()

        # Generate answer
        rag_answer = rag_service.answer_question(
            question=request.question,
            filters=request.filters,
            num_context_docs=request.num_context_docs,
            use_cache=request.use_cache,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Format citations
        citations = [
            CitationResponse(
                text=c.text,
                document_id=c.document_id,
                document_title=c.document_title,
                section=c.section,
                confidence=c.confidence
            )
            for c in rag_answer.citations
        ]

        # Format source documents
        source_docs = [
            SourceDocumentResponse(
                id=doc['id'],
                title=doc['title'],
                citation=doc.get('citation'),
                section_number=doc.get('section_number'),
                score=doc['score'],
                content_preview=doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
            )
            for doc in rag_answer.source_documents
        ]

        # Build response
        return AnswerResponse(
            question=rag_answer.question,
            answer=rag_answer.answer,
            citations=citations,
            confidence_score=rag_answer.confidence_score,
            source_documents=source_docs,
            intent=rag_answer.intent,
            processing_time_ms=rag_answer.processing_time_ms,
            cached=rag_answer.cached,
            metadata=rag_answer.metadata
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question answering failed: {str(e)}"
        )


@router.post("/ask/batch", response_model=BatchAnswerResponse)
async def ask_questions_batch(request: BatchQuestionRequest):
    """
    Ask multiple questions in batch.

    Processes up to 10 questions sequentially, with shared filters and settings.
    Each question is answered independently.

    - **questions**: List of questions (1-10)
    - **filters**: Optional search filters applied to all questions
    - **num_context_docs**: Number of context documents per question
    - **use_cache**: Whether to use cached answers

    Returns list of answers with individual citations and confidence scores.
    """
    try:
        start_time = datetime.now()

        answers = []

        for question in request.questions:
            rag_answer = rag_service.answer_question(
                question=question,
                filters=request.filters,
                num_context_docs=request.num_context_docs,
                use_cache=request.use_cache
            )

            # Format for response
            citations = [
                CitationResponse(
                    text=c.text,
                    document_id=c.document_id,
                    document_title=c.document_title,
                    section=c.section,
                    confidence=c.confidence
                )
                for c in rag_answer.citations
            ]

            source_docs = [
                SourceDocumentResponse(
                    id=doc['id'],
                    title=doc['title'],
                    citation=doc.get('citation'),
                    section_number=doc.get('section_number'),
                    score=doc['score'],
                    content_preview=doc.get('content', '')[:200] + "..."
                )
                for doc in rag_answer.source_documents
            ]

            answers.append(AnswerResponse(
                question=rag_answer.question,
                answer=rag_answer.answer,
                citations=citations,
                confidence_score=rag_answer.confidence_score,
                source_documents=source_docs,
                intent=rag_answer.intent,
                processing_time_ms=rag_answer.processing_time_ms,
                cached=rag_answer.cached,
                metadata=rag_answer.metadata
            ))

        total_time = (datetime.now() - start_time).total_seconds() * 1000

        return BatchAnswerResponse(
            answers=answers,
            total_questions=len(request.questions),
            total_processing_time_ms=total_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch question answering failed: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear the RAG answer cache.

    Removes all cached answers. Use this when regulatory documents are updated
    to ensure fresh answers are generated.

    Returns confirmation of cache clearing.
    """
    try:
        rag_service.clear_cache()

        return {
            "success": True,
            "message": "RAG answer cache cleared successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get statistics about the RAG answer cache.

    Returns cache size, TTL, and other metrics.
    """
    try:
        stats = rag_service.get_cache_stats()

        return {
            "success": True,
            "cache_stats": stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.get("/health")
async def rag_health_check():
    """
    Health check for RAG service.

    Checks status of all RAG components:
    - Search service (for context retrieval)
    - Gemini API (for answer generation)
    - NLP service (for query understanding)
    - Cache statistics

    Returns overall health status and component details.
    """
    try:
        health = rag_service.health_check()

        if health.get('status') == 'healthy':
            return health
        elif health.get('status') == 'degraded':
            # Service partially operational
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


@router.get("/info")
async def get_rag_info():
    """
    Get information about the RAG service configuration.

    Returns details about the RAG system including models, settings, and capabilities.
    """
    return {
        "service": "RAG (Retrieval-Augmented Generation)",
        "description": "AI-powered question answering for Canadian regulations",
        "components": {
            "retrieval": "Hybrid search (keyword + vector)",
            "generation": "Google Gemini API",
            "nlp": "Legal query parser with entity extraction"
        },
        "features": [
            "Citation extraction",
            "Confidence scoring",
            "Multi-document context",
            "Answer caching",
            "Uncertainty detection"
        ],
        "limits": {
            "max_context_docs": 20,
            "max_answer_tokens": 4096,
            "batch_size": 10,
            "cache_ttl_hours": 24
        }
    }
