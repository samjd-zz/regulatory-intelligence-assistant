"""
API routes for knowledge graph operations.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from database import get_db
from utils.neo4j_client import get_neo4j_client, Neo4jClient
from services.graph_builder import GraphBuilder
from models.document_models import Document, DocumentType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


class GraphBuildRequest(BaseModel):
    """Request to build graph for specific documents."""
    document_ids: Optional[List[UUID]] = Field(None, description="Specific document IDs to process")
    document_types: Optional[List[DocumentType]] = Field(None, description="Document types to process")
    limit: Optional[int] = Field(None, description="Maximum number of documents to process", ge=1, le=1000)


class GraphBuildResponse(BaseModel):
    """Response from graph building operation."""
    status: str
    message: str
    stats: Dict[str, Any]


class GraphStatsResponse(BaseModel):
    """Graph statistics response."""
    nodes: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    summary: Dict[str, int]


@router.post("/build", response_model=GraphBuildResponse)
async def build_graph(
    request: GraphBuildRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Build knowledge graph from processed documents.
    
    This operation runs in the background and processes documents asynchronously.
    """
    try:
        builder = GraphBuilder(db, neo4j)
        
        # Build query
        query = db.query(Document).filter_by(is_processed=True)
        
        if request.document_ids:
            query = query.filter(Document.id.in_(request.document_ids))
        
        if request.document_types:
            query = query.filter(Document.document_type.in_(request.document_types))
        
        if request.limit:
            query = query.limit(request.limit)
        
        document_count = query.count()
        
        if document_count == 0:
            raise HTTPException(
                status_code=404,
                detail="No processed documents found matching criteria"
            )
        
        # Start background task
        background_tasks.add_task(
            _build_graph_background,
            db,
            neo4j,
            request
        )
        
        return GraphBuildResponse(
            status="started",
            message=f"Graph building started for {document_count} documents",
            stats={"documents_queued": document_count}
        )
        
    except Exception as e:
        logger.error(f"Error starting graph build: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build/{document_id}", response_model=GraphBuildResponse)
async def build_document_graph(
    document_id: UUID,
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Build knowledge graph for a single document.
    
    This operation runs synchronously and returns immediately.
    """
    try:
        # Check document exists
        document = db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if not document.is_processed:
            raise HTTPException(
                status_code=400,
                detail="Document has not been processed yet"
            )
        
        # Build graph
        builder = GraphBuilder(db, neo4j)
        stats = builder.build_document_graph(document_id)
        
        return GraphBuildResponse(
            status="completed",
            message=f"Graph built successfully for {document.title}",
            stats=stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building graph for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_stats(
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Get statistics about the knowledge graph.
    
    Returns counts of nodes and relationships by type.
    """
    try:
        stats = neo4j.get_graph_stats()
        
        # Calculate summary
        total_nodes = sum(item.get('node_count', 0) for item in stats.get('nodes', []))
        total_relationships = sum(item.get('rel_count', 0) for item in stats.get('relationships', []))
        
        return GraphStatsResponse(
            nodes=stats.get('nodes', []),
            relationships=stats.get('relationships', []),
            summary={
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "node_types": len(stats.get('nodes', [])),
                "relationship_types": len(stats.get('relationships', []))
            }
        )
        
    except Exception as e:
        logger.error(f"Error fetching graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_graph(
    query: str,
    limit: int = 10,
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Search the knowledge graph using full-text search.
    
    Searches across legislation titles and section content.
    """
    try:
        # Search legislation
        leg_query = """
        CALL db.index.fulltext.queryNodes('legislation_fulltext', $query)
        YIELD node, score
        RETURN node, score, labels(node) as labels
        ORDER BY score DESC
        LIMIT $limit
        """
        
        results = neo4j.execute_query(
            leg_query,
            {"query": query, "limit": limit}
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/legislation/{legislation_id}/related")
async def get_related_legislation(
    legislation_id: UUID,
    relationship_type: Optional[str] = None,
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Get legislation and regulations related to a specific legislation.
    
    Optionally filter by relationship type (IMPLEMENTS, INTERPRETS, SUPERSEDES).
    """
    try:
        related = neo4j.find_related_nodes(
            "Legislation",
            str(legislation_id),
            rel_type=relationship_type,
            direction="both"
        )
        
        return {
            "legislation_id": str(legislation_id),
            "relationship_type": relationship_type,
            "related_items": related,
            "count": len(related)
        }
        
    except Exception as e:
        logger.error(f"Error fetching related legislation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/section/{section_id}/references")
async def get_section_references(
    section_id: UUID,
    max_depth: int = 2,
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Get all sections referenced by a specific section.
    
    Follows REFERENCES relationships up to max_depth levels.
    """
    try:
        query = f"""
        MATCH (s:Section {{id: $section_id}})-[:REFERENCES*1..{max_depth}]-(related:Section)
        RETURN related, labels(related) as labels
        """
        
        results = neo4j.execute_query(
            query,
            {"section_id": str(section_id)}
        )
        
        return {
            "section_id": str(section_id),
            "max_depth": max_depth,
            "references": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error fetching section references: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_graph(
    confirm: bool = False,
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Clear all nodes and relationships from the graph.
    
    **WARNING**: This is a destructive operation!
    Set confirm=true to proceed.
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear the graph"
        )
    
    try:
        query = "MATCH (n) DETACH DELETE n"
        result = neo4j.execute_write(query)
        
        return {
            "status": "success",
            "message": "Graph cleared successfully",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error clearing graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_graph_background(
    db: Session,
    neo4j: Neo4jClient,
    request: GraphBuildRequest
):
    """
    Background task to build graph.
    
    This runs asynchronously and doesn't return results to the caller.
    """
    try:
        logger.info("Starting background graph building...")
        
        builder = GraphBuilder(db, neo4j)
        
        # Build query
        query = db.query(Document).filter_by(is_processed=True)
        
        if request.document_ids:
            query = query.filter(Document.id.in_(request.document_ids))
        
        if request.document_types:
            query = query.filter(Document.document_type.in_(request.document_types))
        
        if request.limit:
            query = query.limit(request.limit)
        
        documents = query.all()
        
        # Process each document
        for doc in documents:
            try:
                builder.build_document_graph(doc.id)
                logger.info(f"Built graph for: {doc.title}")
            except Exception as e:
                logger.error(f"Failed to build graph for {doc.title}: {e}")
        
        # Create inter-document relationships
        builder.create_inter_document_relationships()
        
        logger.info("Background graph building completed")
        
    except Exception as e:
        logger.error(f"Background graph building failed: {e}")
