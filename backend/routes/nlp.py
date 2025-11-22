"""
NLP API Routes - Natural Language Processing Endpoints for Legal Queries

This module provides REST API endpoints for:
- Entity extraction from legal text
- Query parsing and intent classification
- Query expansion with synonyms
- Batch processing

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

from services.legal_nlp import (
    LegalEntityExtractor,
    EntityType,
    ExtractedEntity,
    extract_legal_entities
)
from services.query_parser import (
    LegalQueryParser,
    QueryExpander,
    QueryIntent,
    ParsedQuery,
    parse_legal_query
)

# Create router
router = APIRouter(prefix="/api/nlp", tags=["NLP"])

# Initialize NLP services (singleton pattern)
entity_extractor = LegalEntityExtractor(use_spacy=False)
query_parser = LegalQueryParser(use_spacy=False)
query_expander = QueryExpander()


# Pydantic models for request/response

class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction"""
    text: str = Field(..., description="Text to extract entities from", min_length=1)
    entity_types: Optional[List[str]] = Field(
        None,
        description="List of entity types to extract (person_type, program, jurisdiction, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Can a temporary resident apply for employment insurance?",
                "entity_types": ["person_type", "program"]
            }
        }


class EntityResponse(BaseModel):
    """Response model for extracted entities"""
    text: str
    entity_type: str
    normalized: str
    confidence: float
    start_pos: int
    end_pos: int
    context: Optional[str] = None
    metadata: Optional[Dict] = None


class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction"""
    success: bool = True
    entities: List[EntityResponse]
    entity_count: int
    entity_summary: Dict[str, int]
    processing_time_ms: float


class QueryParseRequest(BaseModel):
    """Request model for query parsing"""
    query: str = Field(..., description="Natural language query to parse", min_length=1)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Can a temporary resident apply for employment insurance?"
            }
        }


class ParsedQueryResponse(BaseModel):
    """Response model for parsed query"""
    success: bool = True
    original_query: str
    normalized_query: str
    intent: str
    intent_confidence: float
    entities: List[EntityResponse]
    keywords: List[str]
    question_type: Optional[str]
    filters: Dict
    metadata: Dict
    processing_time_ms: float


class BatchQueryParseRequest(BaseModel):
    """Request model for batch query parsing"""
    queries: List[str] = Field(..., description="List of queries to parse", min_items=1, max_items=100)

    class Config:
        json_schema_extra = {
            "example": {
                "queries": [
                    "Can I apply for EI?",
                    "What is CPP?",
                    "How to get OAS benefits?"
                ]
            }
        }


class BatchQueryParseResponse(BaseModel):
    """Response model for batch query parsing"""
    success: bool = True
    parsed_queries: List[ParsedQueryResponse]
    query_count: int
    intent_distribution: Dict[str, int]
    processing_time_ms: float


class QueryExpansionRequest(BaseModel):
    """Request model for query expansion"""
    query: str = Field(..., description="Query to expand with synonyms", min_length=1)
    max_expansions: int = Field(5, description="Maximum number of expanded queries", ge=1, le=10)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Can a temporary resident apply for EI?",
                "max_expansions": 5
            }
        }


class QueryExpansionResponse(BaseModel):
    """Response model for query expansion"""
    success: bool = True
    original_query: str
    expanded_queries: List[str]
    expansion_count: int
    processing_time_ms: float


# API Endpoints

@router.post("/extract-entities", response_model=EntityExtractionResponse)
async def extract_entities_endpoint(request: EntityExtractionRequest):
    """
    Extract legal entities from text.

    Extracts entities such as person types, programs, jurisdictions, requirements,
    dates, monetary amounts, and legislation references.

    - **text**: The text to analyze
    - **entity_types**: Optional list of specific entity types to extract

    Returns extracted entities with confidence scores and normalized forms.
    """
    try:
        start_time = datetime.now()

        # Parse entity types if provided
        entity_type_enums = None
        if request.entity_types:
            try:
                entity_type_enums = [EntityType(et) for et in request.entity_types]
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid entity type: {str(e)}"
                )

        # Extract entities
        entities = entity_extractor.extract_entities(
            request.text,
            entity_types=entity_type_enums
        )

        # Convert to response format
        entity_responses = [
            EntityResponse(
                text=e.text,
                entity_type=e.entity_type.value,
                normalized=e.normalized,
                confidence=e.confidence,
                start_pos=e.start_pos,
                end_pos=e.end_pos,
                context=e.context,
                metadata=e.metadata
            )
            for e in entities
        ]

        # Get summary
        entity_summary = entity_extractor.get_entity_summary(entities)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return EntityExtractionResponse(
            entities=entity_responses,
            entity_count=len(entities),
            entity_summary=entity_summary,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.post("/parse-query", response_model=ParsedQueryResponse)
async def parse_query_endpoint(request: QueryParseRequest):
    """
    Parse a natural language query to extract intent, entities, and keywords.

    Classifies the query intent (search, compliance, eligibility, etc.), extracts
    entities, identifies keywords, and detects question type.

    - **query**: The natural language query to parse

    Returns structured information about the query including intent, entities, and filters.
    """
    try:
        start_time = datetime.now()

        # Parse query
        parsed = query_parser.parse_query(request.query)

        # Convert entities to response format
        entity_responses = [
            EntityResponse(
                text=e.text,
                entity_type=e.entity_type.value,
                normalized=e.normalized,
                confidence=e.confidence,
                start_pos=e.start_pos,
                end_pos=e.end_pos,
                context=e.context,
                metadata=e.metadata
            )
            for e in parsed.entities
        ]

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return ParsedQueryResponse(
            original_query=parsed.original_query,
            normalized_query=parsed.normalized_query,
            intent=parsed.intent.value,
            intent_confidence=parsed.intent_confidence,
            entities=entity_responses,
            keywords=parsed.keywords,
            question_type=parsed.question_type,
            filters=parsed.filters,
            metadata=parsed.metadata,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query parsing failed: {str(e)}"
        )


@router.post("/parse-queries-batch", response_model=BatchQueryParseResponse)
async def parse_queries_batch_endpoint(request: BatchQueryParseRequest):
    """
    Parse multiple queries in batch for efficient processing.

    - **queries**: List of natural language queries to parse (max 100)

    Returns parsed information for all queries plus intent distribution statistics.
    """
    try:
        start_time = datetime.now()

        # Parse all queries
        parsed_queries = query_parser.batch_parse_queries(request.queries)

        # Convert to response format
        parsed_responses = []
        for parsed in parsed_queries:
            entity_responses = [
                EntityResponse(
                    text=e.text,
                    entity_type=e.entity_type.value,
                    normalized=e.normalized,
                    confidence=e.confidence,
                    start_pos=e.start_pos,
                    end_pos=e.end_pos,
                    context=e.context,
                    metadata=e.metadata
                )
                for e in parsed.entities
            ]

            parsed_responses.append(ParsedQueryResponse(
                original_query=parsed.original_query,
                normalized_query=parsed.normalized_query,
                intent=parsed.intent.value,
                intent_confidence=parsed.intent_confidence,
                entities=entity_responses,
                keywords=parsed.keywords,
                question_type=parsed.question_type,
                filters=parsed.filters,
                metadata=parsed.metadata,
                processing_time_ms=0  # Individual time not tracked in batch
            ))

        # Get intent distribution
        intent_distribution = query_parser.get_intent_distribution(parsed_queries)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return BatchQueryParseResponse(
            parsed_queries=parsed_responses,
            query_count=len(parsed_queries),
            intent_distribution=intent_distribution,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch query parsing failed: {str(e)}"
        )


@router.post("/expand-query", response_model=QueryExpansionResponse)
async def expand_query_endpoint(request: QueryExpansionRequest):
    """
    Expand a query with synonyms and related terms for better search recall.

    Generates query variations by replacing entities with their synonyms,
    useful for improving search results.

    - **query**: The original query to expand
    - **max_expansions**: Maximum number of expanded queries to return (default: 5)

    Returns the original query plus expanded variations.
    """
    try:
        start_time = datetime.now()

        # Expand query
        expanded = query_expander.expand_query(request.query)

        # Limit to requested number
        expanded = expanded[:request.max_expansions]

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return QueryExpansionResponse(
            original_query=request.query,
            expanded_queries=expanded,
            expansion_count=len(expanded),
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query expansion failed: {str(e)}"
        )


@router.get("/entity-types", response_model=Dict[str, List[str]])
async def get_entity_types():
    """
    Get list of supported entity types.

    Returns a dictionary of entity types and their descriptions.
    """
    return {
        "entity_types": [
            "person_type",
            "program",
            "jurisdiction",
            "organization",
            "legislation",
            "date",
            "money",
            "requirement"
        ],
        "descriptions": {
            "person_type": "Types of persons (citizen, permanent resident, temporary resident, etc.)",
            "program": "Government programs (EI, CPP, OAS, etc.)",
            "jurisdiction": "Jurisdictions (federal, provincial, municipal)",
            "organization": "Organizations and agencies",
            "legislation": "Acts, regulations, and laws",
            "date": "Dates and time references",
            "money": "Monetary amounts",
            "requirement": "Requirements and documents (SIN, work permit, etc.)"
        }
    }


@router.get("/intent-types", response_model=Dict[str, List[str]])
async def get_intent_types():
    """
    Get list of supported query intent types.

    Returns a dictionary of intent types and their descriptions.
    """
    return {
        "intent_types": [
            "search",
            "compliance",
            "interpretation",
            "eligibility",
            "procedure",
            "definition",
            "comparison",
            "unknown"
        ],
        "descriptions": {
            "search": "Finding relevant regulations or information",
            "compliance": "Checking if something meets requirements",
            "interpretation": "Understanding what a regulation means",
            "eligibility": "Checking if someone qualifies for something",
            "procedure": "How to do something or apply for something",
            "definition": "What does a term or concept mean",
            "comparison": "Comparing regulations or options",
            "unknown": "Cannot determine intent"
        }
    }


@router.get("/health")
async def nlp_health_check():
    """
    Health check endpoint for NLP service.

    Returns the status of NLP components.
    """
    return {
        "status": "healthy",
        "service": "NLP",
        "components": {
            "entity_extractor": "operational",
            "query_parser": "operational",
            "query_expander": "operational"
        },
        "timestamp": datetime.now().isoformat()
    }
