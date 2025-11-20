"""
FastAPI application for Regulatory Intelligence Assistant.
Provides health checks and will include API routes for all services.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
from dotenv import load_dotenv
from typing import Dict, Any
import logging

# Import database utilities
from database import get_db, engine

# Import routers
from routes.compliance import router as compliance_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Regulatory Intelligence Assistant API",
    description="AI-powered platform to navigate complex laws, policies, and regulations",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(compliance_router)


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint - API status."""
    return {
        "name": "Regulatory Intelligence Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


# Health check endpoints
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """General health check endpoint."""
    return {"status": "healthy", "service": "api"}


@app.get("/health/postgres")
async def health_check_postgres(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check for PostgreSQL database.
    Tests connection and returns database info.
    """
    try:
        # Test database connection with a simple query
        result = db.execute(text("SELECT version()"))
        version = result.scalar()
        
        # Get table count
        result = db.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """))
        table_count = result.scalar()
        
        return {
            "status": "healthy",
            "service": "postgresql",
            "database": os.getenv("POSTGRES_DB", "regulatory_db"),
            "tables": table_count,
            "version": version.split()[1] if version else "unknown",
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"PostgreSQL connection failed: {str(e)}",
        )


@app.get("/health/neo4j")
async def health_check_neo4j() -> Dict[str, Any]:
    """
    Health check for Neo4j graph database.
    Tests connection and returns graph info.
    """
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password123")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions[0] as version, edition")
            record = result.single()
            
            # Get node and relationship counts
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]
            
            driver.close()
            
            return {
                "status": "healthy",
                "service": "neo4j",
                "version": record["version"] if record else "unknown",
                "edition": record["edition"] if record else "unknown",
                "nodes": node_count,
                "relationships": rel_count,
            }
    except ImportError:
        logger.warning("Neo4j driver not installed")
        return {
            "status": "unavailable",
            "service": "neo4j",
            "message": "Neo4j driver not installed. Run: pip install neo4j",
        }
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Neo4j connection failed: {str(e)}",
        )


@app.get("/health/elasticsearch")
async def health_check_elasticsearch() -> Dict[str, Any]:
    """
    Health check for Elasticsearch.
    Tests connection and returns cluster info.
    """
    try:
        from elasticsearch import Elasticsearch
        
        es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        es = Elasticsearch([es_url])
        
        # Test connection
        if not es.ping():
            raise Exception("Elasticsearch ping failed")
        
        # Get cluster info
        info = es.info()
        health = es.cluster.health()
        
        # Get index count
        indices = es.cat.indices(format="json")
        index_count = len(indices) if indices else 0
        
        return {
            "status": "healthy",
            "service": "elasticsearch",
            "cluster_name": info.get("cluster_name", "unknown"),
            "version": info.get("version", {}).get("number", "unknown"),
            "cluster_status": health.get("status", "unknown"),
            "indices": index_count,
            "nodes": health.get("number_of_nodes", 0),
        }
    except ImportError:
        logger.warning("Elasticsearch client not installed")
        return {
            "status": "unavailable",
            "service": "elasticsearch",
            "message": "Elasticsearch client not installed. Run: pip install elasticsearch",
        }
    except Exception as e:
        logger.error(f"Elasticsearch health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Elasticsearch connection failed: {str(e)}",
        )


@app.get("/health/redis")
async def health_check_redis() -> Dict[str, Any]:
    """
    Health check for Redis cache.
    Tests connection and returns server info.
    """
    try:
        import redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        r.ping()
        
        # Get server info
        info = r.info()
        
        return {
            "status": "healthy",
            "service": "redis",
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
        }
    except ImportError:
        logger.warning("Redis client not installed")
        return {
            "status": "unavailable",
            "service": "redis",
            "message": "Redis client not installed. Run: pip install redis",
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {str(e)}",
        )


@app.get("/health/all")
async def health_check_all(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check for all services.
    Returns status of PostgreSQL, Neo4j, Elasticsearch, and Redis.
    """
    services = {}
    overall_healthy = True
    
    # PostgreSQL
    try:
        postgres = await health_check_postgres(db)
        services["postgres"] = postgres
    except HTTPException as e:
        services["postgres"] = {"status": "unhealthy", "error": e.detail}
        overall_healthy = False
    
    # Neo4j
    try:
        neo4j = await health_check_neo4j()
        services["neo4j"] = neo4j
    except HTTPException as e:
        services["neo4j"] = {"status": "unhealthy", "error": e.detail}
        overall_healthy = False
    
    # Elasticsearch
    try:
        elasticsearch = await health_check_elasticsearch()
        services["elasticsearch"] = elasticsearch
    except HTTPException as e:
        services["elasticsearch"] = {"status": "unhealthy", "error": e.detail}
        overall_healthy = False
    
    # Redis
    try:
        redis_check = await health_check_redis()
        services["redis"] = redis_check
    except HTTPException as e:
        services["redis"] = {"status": "unhealthy", "error": e.detail}
        overall_healthy = False
    
    return {
        "status": "healthy" if overall_healthy else "degraded",
        "services": services,
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Starting Regulatory Intelligence Assistant API...")
    logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
    logger.info(f"Debug mode: {os.getenv('DEBUG', 'False')}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Regulatory Intelligence Assistant API...")


if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
