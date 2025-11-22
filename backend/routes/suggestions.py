"""
Query Suggestion API Routes

REST API endpoints for query suggestions and autocomplete.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from services.query_suggestions import (
    get_suggestion_engine,
    QuerySuggestion
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/suggestions", tags=["Query Suggestions"])


# === Request/Response Models ===

class SuggestionResponse(BaseModel):
    """Response with query suggestions"""
    query: str
    suggestions: List[Dict[str, Any]]
    count: int

    class Config:
        json_schema_extra = {
            "example": {
                "query": "employment",
                "suggestions": [
                    {
                        "text": "employment insurance eligibility",
                        "score": 0.95,
                        "category": "popular"
                    }
                ],
                "count": 1
            }
        }


class TrendingQueriesResponse(BaseModel):
    """Response with trending queries"""
    trending_queries: List[Dict[str, Any]]
    period_hours: int
    count: int


class RecordQueryRequest(BaseModel):
    """Request to record a query"""
    query: str = Field(..., min_length=2, max_length=500)


# === API Endpoints ===

@router.get("/autocomplete", response_model=SuggestionResponse)
async def autocomplete(
    q: str = Query(..., min_length=1, max_length=200, description="Query prefix"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions")
):
    """
    Get autocomplete suggestions for query prefix

    Returns ranked suggestions based on:
    - Popular queries matching prefix
    - Query history
    - Template-based suggestions
    - Typo corrections

    **Example:**
    ```
    GET /api/suggestions/autocomplete?q=employ&limit=5
    ```

    Returns suggestions like:
    - employment insurance eligibility
    - employment insurance application
    - employment permit requirements
    """
    try:
        engine = get_suggestion_engine()

        suggestions = engine.get_suggestions(
            query=q,
            max_results=limit,
            include_templates=True
        )

        return SuggestionResponse(
            query=q,
            suggestions=[s.to_dict() for s in suggestions],
            count=len(suggestions)
        )

    except Exception as e:
        logger.error(f"Autocomplete failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/", response_model=SuggestionResponse)
async def get_suggestions(
    query: str = Query(..., min_length=2, max_length=500),
    max_results: int = Query(10, ge=1, le=50),
    include_templates: bool = Query(True)
):
    """
    Get comprehensive query suggestions

    Similar to autocomplete but supports longer/complete queries
    and provides more detailed suggestions including templates.

    **Query Parameters:**
    - `query`: User's search query
    - `max_results`: Maximum number of suggestions (1-50)
    - `include_templates`: Include template-based suggestions

    **Returns:**
    Ranked list of suggestions with scores and categories.
    """
    try:
        engine = get_suggestion_engine()

        suggestions = engine.get_suggestions(
            query=query,
            max_results=max_results,
            include_templates=include_templates
        )

        return SuggestionResponse(
            query=query,
            suggestions=[s.to_dict() for s in suggestions],
            count=len(suggestions)
        )

    except Exception as e:
        logger.error(f"Get suggestions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.post("/record")
async def record_query(request: RecordQueryRequest):
    """
    Record a user query for suggestion learning

    Call this when a user submits a search query to improve
    future suggestions based on query history.

    **Request Body:**
    ```json
    {
      "query": "employment insurance eligibility"
    }
    ```

    **Returns:**
    Success confirmation.
    """
    try:
        engine = get_suggestion_engine()
        engine.record_query(request.query)

        return {
            "success": True,
            "message": "Query recorded successfully"
        }

    except Exception as e:
        logger.error(f"Record query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record query: {str(e)}"
        )


@router.get("/trending", response_model=TrendingQueriesResponse)
async def get_trending_queries(
    hours: int = Query(24, ge=1, le=168, description="Look back hours"),
    top_n: int = Query(10, ge=1, le=50, description="Number of results")
):
    """
    Get trending queries from recent history

    Returns most frequently searched queries in the specified time period.
    Useful for showing "Popular Searches" or "Trending Now" sections.

    **Query Parameters:**
    - `hours`: Look back this many hours (1-168)
    - `top_n`: Return top N queries (1-50)

    **Example:**
    ```
    GET /api/suggestions/trending?hours=24&top_n=10
    ```

    Returns the top 10 queries from the last 24 hours.
    """
    try:
        engine = get_suggestion_engine()

        trending = engine.get_trending_queries(
            hours=hours,
            top_n=top_n
        )

        return TrendingQueriesResponse(
            trending_queries=trending,
            period_hours=hours,
            count=len(trending)
        )

    except Exception as e:
        logger.error(f"Get trending failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trending queries: {str(e)}"
        )


@router.get("/popular/{category}")
async def get_popular_by_category(
    category: str,
    top_n: int = Query(10, ge=1, le=50)
):
    """
    Get popular queries by category/intent

    Returns most common queries for a specific intent category.

    **Categories:**
    - eligibility
    - application
    - benefits
    - requirements
    - process
    - status
    - general

    **Example:**
    ```
    GET /api/suggestions/popular/eligibility?top_n=5
    ```

    Returns top 5 eligibility-related queries.
    """
    try:
        # Validate category
        valid_categories = {
            'eligibility', 'application', 'benefits',
            'requirements', 'process', 'status', 'general'
        }

        if category not in valid_categories:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {', '.join(valid_categories)}"
            )

        engine = get_suggestion_engine()

        popular = engine.get_popular_by_category(
            category=category,
            top_n=top_n
        )

        return {
            "success": True,
            "category": category,
            "queries": popular,
            "count": len(popular)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get popular by category failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular queries: {str(e)}"
        )


@router.get("/health")
async def suggestions_health():
    """
    Health check for suggestion service

    Returns service status and basic statistics.
    """
    try:
        engine = get_suggestion_engine()

        # Get basic stats
        stats = {
            "total_history_queries": len(engine.query_history),
            "unique_queries": len(engine.query_counts),
            "typo_correction_enabled": engine.enable_typo_correction
        }

        return {
            "status": "healthy",
            "service": "query_suggestions",
            "stats": stats
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "query_suggestions",
            "error": str(e)
        }
