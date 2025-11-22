"""
API Versioning Support

FastAPI-based API versioning with:
- URL path versioning (/api/v1/, /api/v2/)
- Header-based versioning (Accept-Version header)
- Semantic versioning (MAJOR.MINOR.PATCH)
- Version deprecation warnings
- Backward compatibility support
- Version routing and fallback

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.routing import APIRoute
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, date
import logging
import re

logger = logging.getLogger(__name__)


# === Version Information ===

@dataclass
class APIVersion:
    """API version information"""
    major: int
    minor: int
    patch: int
    release_date: date
    deprecated: bool = False
    deprecation_date: Optional[date] = None
    sunset_date: Optional[date] = None
    changelog: str = ""

    @property
    def version_string(self) -> str:
        """Get version as string (e.g., '1.2.3')"""
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def is_deprecated(self) -> bool:
        """Check if version is deprecated"""
        if not self.deprecated:
            return False

        if self.deprecation_date:
            return datetime.now().date() >= self.deprecation_date

        return self.deprecated

    @property
    def is_sunset(self) -> bool:
        """Check if version has reached sunset (no longer supported)"""
        if not self.sunset_date:
            return False

        return datetime.now().date() >= self.sunset_date

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'version': self.version_string,
            'release_date': self.release_date.isoformat(),
            'deprecated': self.is_deprecated,
            'deprecation_date': self.deprecation_date.isoformat() if self.deprecation_date else None,
            'sunset_date': self.sunset_date.isoformat() if self.sunset_date else None,
            'changelog': self.changelog
        }


# === Version Registry ===

class APIVersionRegistry:
    """Registry of all API versions"""

    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.default_version: Optional[str] = None

    def register(self, version: APIVersion, is_default: bool = False):
        """
        Register an API version

        Args:
            version: APIVersion instance
            is_default: Whether this is the default version
        """
        version_key = f"v{version.major}"
        self.versions[version_key] = version

        if is_default or self.default_version is None:
            self.default_version = version_key

        logger.info(f"Registered API version {version.version_string}")

    def get_version(self, version_string: str) -> Optional[APIVersion]:
        """
        Get version by string (e.g., 'v1' or '1' or '1.0.0')

        Args:
            version_string: Version identifier

        Returns:
            APIVersion or None if not found
        """
        # Normalize version string
        if not version_string.startswith('v'):
            version_string = f"v{version_string}"

        # Extract major version only (v1, v2, etc.)
        match = re.match(r'v(\d+)', version_string)
        if match:
            version_key = f"v{match.group(1)}"
            return self.versions.get(version_key)

        return None

    def get_default_version(self) -> Optional[APIVersion]:
        """Get the default API version"""
        if self.default_version:
            return self.versions.get(self.default_version)
        return None

    def get_all_versions(self) -> List[APIVersion]:
        """Get all registered versions"""
        return list(self.versions.values())

    def get_supported_versions(self) -> List[APIVersion]:
        """Get only supported (not sunset) versions"""
        return [v for v in self.versions.values() if not v.is_sunset]


# === Version Extraction ===

class VersionExtractor:
    """Extract API version from request"""

    @staticmethod
    def from_path(path: str) -> Optional[str]:
        """
        Extract version from URL path

        Examples:
            /api/v1/search → v1
            /api/v2/documents → v2
        """
        match = re.search(r'/api/(v\d+)/', path)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def from_header(request: Request, header_name: str = "Accept-Version") -> Optional[str]:
        """
        Extract version from HTTP header

        Args:
            request: FastAPI request
            header_name: Header name (default: Accept-Version)

        Returns:
            Version string or None
        """
        version = request.headers.get(header_name)
        if version:
            # Normalize to vX format
            if not version.startswith('v'):
                version = f"v{version}"
            return version
        return None

    @staticmethod
    def from_query_param(request: Request, param_name: str = "version") -> Optional[str]:
        """
        Extract version from query parameter

        Args:
            request: FastAPI request
            param_name: Query parameter name

        Returns:
            Version string or None
        """
        version = request.query_params.get(param_name)
        if version:
            if not version.startswith('v'):
                version = f"v{version}"
            return version
        return None


# === Versioned Route ===

class VersionedAPIRoute(APIRoute):
    """
    Custom APIRoute that handles versioning

    Adds version information to request state and response headers
    """

    def __init__(
        self,
        *args,
        version_registry: APIVersionRegistry,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.version_registry = version_registry

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # Extract version
            version_string = (
                VersionExtractor.from_path(request.url.path) or
                VersionExtractor.from_header(request) or
                "v1"  # Default
            )

            # Get version info
            version = self.version_registry.get_version(version_string)

            if not version:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"API version {version_string} not found"
                )

            # Check if sunset
            if version.is_sunset:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail=f"API version {version_string} is no longer supported. "
                           f"Sunset date: {version.sunset_date}"
                )

            # Store version in request state
            request.state.api_version = version

            # Call original handler
            response = await original_route_handler(request)

            # Add version headers to response
            response.headers["X-API-Version"] = version.version_string

            if version.is_deprecated:
                response.headers["X-API-Deprecated"] = "true"
                if version.deprecation_date:
                    response.headers["X-API-Deprecation-Date"] = version.deprecation_date.isoformat()
                if version.sunset_date:
                    response.headers["X-API-Sunset-Date"] = version.sunset_date.isoformat()

                # Add deprecation warning to response (if JSON)
                if isinstance(response, Response) and hasattr(response, 'body'):
                    warning_msg = (
                        f"API version {version.version_string} is deprecated. "
                        f"Please migrate to the latest version."
                    )
                    logger.warning(warning_msg)

            return response

        return custom_route_handler


# === Version Manager ===

class APIVersionManager:
    """
    Centralized API version management

    Usage:
        version_manager = APIVersionManager()
        version_manager.register_version(...)
        app = FastAPI(route_class=version_manager.get_route_class())
    """

    def __init__(self):
        self.registry = APIVersionRegistry()

    def register_version(
        self,
        major: int,
        minor: int,
        patch: int,
        release_date: date,
        is_default: bool = False,
        deprecated: bool = False,
        deprecation_date: Optional[date] = None,
        sunset_date: Optional[date] = None,
        changelog: str = ""
    ):
        """Register a new API version"""
        version = APIVersion(
            major=major,
            minor=minor,
            patch=patch,
            release_date=release_date,
            deprecated=deprecated,
            deprecation_date=deprecation_date,
            sunset_date=sunset_date,
            changelog=changelog
        )

        self.registry.register(version, is_default=is_default)

    def get_route_class(self) -> type:
        """
        Get custom route class with versioning support

        Use this with FastAPI:
            app = FastAPI(route_class=version_manager.get_route_class())
        """
        registry = self.registry

        class VersionedRoute(VersionedAPIRoute):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, version_registry=registry, **kwargs)

        return VersionedRoute

    def get_version_info(self) -> Dict[str, Any]:
        """Get information about all versions"""
        return {
            'supported_versions': [v.to_dict() for v in self.registry.get_supported_versions()],
            'deprecated_versions': [v.to_dict() for v in self.registry.get_all_versions() if v.is_deprecated],
            'default_version': self.registry.get_default_version().version_string if self.registry.get_default_version() else None
        }


# === Global Version Manager ===

_version_manager: Optional[APIVersionManager] = None


def get_version_manager() -> APIVersionManager:
    """Get or create global version manager"""
    global _version_manager

    if _version_manager is None:
        _version_manager = APIVersionManager()

        # Register default versions for Regulatory Intelligence Assistant
        _version_manager.register_version(
            major=1,
            minor=0,
            patch=0,
            release_date=date(2025, 11, 22),
            is_default=True,
            deprecated=False,
            changelog="Initial MVP release for G7 GovAI Challenge"
        )

        # Future version example (commented out)
        # _version_manager.register_version(
        #     major=2,
        #     minor=0,
        #     patch=0,
        #     release_date=date(2025, 12, 1),
        #     is_default=True,
        #     deprecated=False,
        #     changelog="Added multi-hop reasoning and advanced graph search"
        # )

    return _version_manager


# === Version Info Endpoint Helper ===

def create_version_info_response() -> Dict[str, Any]:
    """Create response for /version endpoint"""
    manager = get_version_manager()

    return {
        "api_name": "Regulatory Intelligence Assistant API",
        "versions": manager.get_version_info(),
        "documentation": "/docs",
        "timestamp": datetime.now().isoformat()
    }


# === Example Usage ===

if __name__ == "__main__":
    from fastapi import FastAPI

    # Initialize version manager
    version_manager = get_version_manager()

    # Create FastAPI app with versioning
    app = FastAPI(
        title="Regulatory Intelligence Assistant API",
        route_class=version_manager.get_route_class()
    )

    @app.get("/api/v1/search")
    async def search_v1(request: Request):
        """Search endpoint - version 1"""
        version = request.state.api_version
        return {
            "version": version.version_string,
            "results": ["result1", "result2"]
        }

    @app.get("/version")
    async def get_version_info():
        """Get API version information"""
        return create_version_info_response()

    print("API versioning enabled!")
    print(f"Default version: {version_manager.registry.get_default_version().version_string}")
