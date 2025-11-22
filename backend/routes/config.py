"""
Configuration Management API Routes

Provides REST API endpoints for viewing and managing system configuration.

Features:
- View current configuration
- Validate configuration
- Update feature flags
- Get environment info
- Configuration health checks

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from config.model_config import (
    config_manager,
    get_config,
    is_feature_enabled,
    ModelConfiguration,
    Environment
)
from config.config_validator import ConfigurationValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/config", tags=["Configuration"])


# === Request/Response Models ===

class FeatureFlagUpdate(BaseModel):
    """Request to update feature flags"""
    feature_name: str
    enabled: bool

    class Config:
        json_schema_extra = {
            "example": {
                "feature_name": "enable_query_suggestions",
                "enabled": true
            }
        }


class ConfigurationResponse(BaseModel):
    """Response with configuration details"""
    environment: str
    config: Dict[str, Any]
    config_version: str


class ValidationResponse(BaseModel):
    """Response with validation results"""
    valid: bool
    error_count: int
    warning_count: int
    errors: list
    warnings: list
    info: list


# === API Endpoints ===

@router.get("/", response_model=ConfigurationResponse)
async def get_configuration():
    """
    Get current system configuration

    Returns complete configuration including NLP, Gemini, Elasticsearch,
    Search, RAG settings, and feature flags.

    Note: Sensitive values (API keys, passwords) are excluded.
    """
    try:
        config = get_config()

        return ConfigurationResponse(
            environment=config.environment.value,
            config=config.to_dict(),
            config_version=config.config_version
        )

    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.get("/nlp")
async def get_nlp_configuration():
    """
    Get NLP model configuration

    Returns settings for entity extraction, query parsing,
    and NLP performance parameters.
    """
    try:
        config = get_config()
        return {
            "success": True,
            "config": config.nlp.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to get NLP config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/gemini")
async def get_gemini_configuration():
    """
    Get Gemini API configuration

    Returns settings for Gemini API including model parameters,
    rate limits, and caching settings.

    Note: API key is excluded for security.
    """
    try:
        config = get_config()
        gemini_config = config.gemini.to_dict()

        return {
            "success": True,
            "config": gemini_config,
            "is_configured": config.gemini.is_configured
        }

    except Exception as e:
        logger.error(f"Failed to get Gemini config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/elasticsearch")
async def get_elasticsearch_configuration():
    """
    Get Elasticsearch configuration

    Returns settings for Elasticsearch including index settings,
    search parameters, and performance tuning.

    Note: Credentials are excluded for security.
    """
    try:
        config = get_config()
        es_config = config.elasticsearch.to_dict()

        return {
            "success": True,
            "config": es_config,
            "is_configured": config.elasticsearch.is_configured
        }

    except Exception as e:
        logger.error(f"Failed to get Elasticsearch config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search")
async def get_search_configuration():
    """
    Get search and ranking configuration

    Returns settings for relevance scoring, filtering,
    faceted search, and highlighting.
    """
    try:
        config = get_config()
        return {
            "success": True,
            "config": config.search.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to get search config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rag")
async def get_rag_configuration():
    """
    Get RAG (Retrieval-Augmented Generation) configuration

    Returns settings for context retrieval, citation extraction,
    confidence scoring, and answer generation.
    """
    try:
        config = get_config()
        return {
            "success": True,
            "config": config.rag.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to get RAG config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/features")
async def get_feature_flags():
    """
    Get all feature flags

    Returns status of all experimental, beta, and production features.
    """
    try:
        config = get_config()
        return {
            "success": True,
            "features": config.features.to_dict()
        }

    except Exception as e:
        logger.error(f"Failed to get feature flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/features/{feature_name}")
async def check_feature(feature_name: str):
    """
    Check if a specific feature is enabled

    Args:
        feature_name: Name of the feature flag

    Returns whether the feature is currently enabled.
    """
    try:
        enabled = is_feature_enabled(feature_name)

        return {
            "success": True,
            "feature": feature_name,
            "enabled": enabled
        }

    except Exception as e:
        logger.error(f"Failed to check feature {feature_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/validate", response_model=ValidationResponse)
async def validate_configuration():
    """
    Validate current configuration

    Checks configuration for errors, warnings, and provides suggestions
    for improvement. Validates:
    - Schema correctness
    - Value constraints
    - Security settings
    - Performance tuning
    - Environment consistency
    """
    try:
        config = get_config()
        validator = ConfigurationValidator()
        result = validator.validate(config)

        return ValidationResponse(
            valid=result.valid,
            error_count=result.error_count,
            warning_count=result.warning_count,
            errors=[str(e) for e in result.errors],
            warnings=[str(w) for w in result.warnings],
            info=[str(i) for i in result.info]
        )

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/reload")
async def reload_configuration():
    """
    Reload configuration from environment and files

    Useful after updating environment variables or configuration files.

    Note: This is a runtime operation and changes will be lost on restart
    unless persisted to environment or configuration files.
    """
    try:
        config_manager.reload()

        return {
            "success": True,
            "message": "Configuration reloaded successfully",
            "environment": get_config().environment.value,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}"
        )


@router.get("/environment")
async def get_environment_info():
    """
    Get current environment information

    Returns deployment environment and environment-specific settings.
    """
    try:
        config = get_config()

        return {
            "success": True,
            "environment": config.environment.value,
            "config_version": config.config_version,
            "last_updated": config.last_updated,
            "gemini_configured": config.gemini.is_configured,
            "elasticsearch_configured": config.elasticsearch.is_configured
        }

    except Exception as e:
        logger.error(f"Failed to get environment info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/health")
async def configuration_health_check():
    """
    Health check for configuration service

    Returns configuration status and any critical issues.
    """
    try:
        config = get_config()
        validator = ConfigurationValidator()
        result = validator.validate(config)

        health_status = "healthy" if result.valid else "degraded"

        if result.error_count > 0:
            health_status = "unhealthy"

        return {
            "status": health_status,
            "service": "configuration",
            "environment": config.environment.value,
            "config_valid": result.valid,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "critical_issues": [str(e) for e in result.errors[:5]],  # First 5 errors
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Configuration health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "configuration",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
