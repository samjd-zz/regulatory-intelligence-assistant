"""
API Version Information Endpoints

Provides information about API versions, deprecations, and changelogs.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
import logging

from utils.api_versioning import get_version_manager, create_version_info_response

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["API Version"])


@router.get("/version")
async def get_api_version_info():
    """
    Get API version information

    Returns information about all supported API versions,
    deprecated versions, and the current default version.

    **Response includes:**
    - List of supported versions
    - Deprecated versions with sunset dates
    - Default version
    - Changelogs for each version

    **Example Response:**
    ```json
    {
      "api_name": "Regulatory Intelligence Assistant API",
      "versions": {
        "supported_versions": [
          {
            "version": "1.0.0",
            "release_date": "2025-11-22",
            "deprecated": false,
            "changelog": "Initial MVP release"
          }
        ],
        "deprecated_versions": [],
        "default_version": "1.0.0"
      },
      "documentation": "/docs"
    }
    ```
    """
    return create_version_info_response()


@router.get("/api/version")
async def get_api_version_info_alt():
    """
    Get API version information (alternative endpoint)

    Same as /version but under /api/ path for consistency.
    """
    return create_version_info_response()


@router.get("/api/{version}/version")
async def get_specific_version_info(version: str, request: Request):
    """
    Get information about a specific API version

    **Path Parameters:**
    - `version`: Version identifier (e.g., 'v1', 'v2')

    **Returns:**
    Detailed information about the requested version including:
    - Version number
    - Release date
    - Deprecation status
    - Sunset date (if applicable)
    - Changelog

    **Example:**
    ```
    GET /api/v1/version
    ```
    """
    manager = get_version_manager()

    # Normalize version string
    if not version.startswith('v'):
        version = f"v{version}"

    version_info = manager.registry.get_version(version)

    if not version_info:
        return {
            "error": f"Version {version} not found",
            "supported_versions": [v.version_string for v in manager.registry.get_supported_versions()]
        }

    return {
        "version": version_info.to_dict(),
        "is_current_request_version": hasattr(request.state, 'api_version') and
                                       request.state.api_version.version_string == version_info.version_string
    }


@router.get("/health/version")
async def version_health_check():
    """
    Health check for versioning system

    Verifies that version management is working correctly.
    """
    try:
        manager = get_version_manager()

        supported_versions = manager.registry.get_supported_versions()
        default_version = manager.registry.get_default_version()

        return {
            "status": "healthy",
            "service": "api_versioning",
            "total_versions": len(manager.registry.get_all_versions()),
            "supported_versions": len(supported_versions),
            "default_version": default_version.version_string if default_version else None
        }

    except Exception as e:
        logger.error(f"Version health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "api_versioning",
            "error": str(e)
        }
