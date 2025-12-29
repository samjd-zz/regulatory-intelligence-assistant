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


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])



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


@router.get("/regulation/{regulation_id}/relationships")
async def get_regulation_relationships(
    regulation_id: UUID,
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """
    Get all relationships for a regulation including:
    - References (documents this regulation cites via its sections)
    - Referenced By (documents that cite this regulation via their sections)
    - Implements (parent legislation this regulation implements)
    """
    try:
        # Query for relationships at the Section level, then aggregate to Regulation level
        # Pattern based on: MATCH (s1:Section)-[:REFERENCES]->(s2:Section)
        #                   MATCH (doc1:Regulation)-[:HAS_SECTION]->(s1)
        #                   MATCH (doc2:Regulation)-[:HAS_SECTION]->(s2)
        query = """
        MATCH (r:Regulation {id: $regulation_id})
        
        // Find regulations referenced by this regulation's sections
        OPTIONAL MATCH (r)-[:HAS_SECTION]->(s:Section)-[:REFERENCES]->(refSec:Section)<-[:HAS_SECTION]-(refReg:Regulation)
        WHERE refReg.id <> r.id
        
        // Find regulations that reference this regulation's sections
        OPTIONAL MATCH (r)-[:HAS_SECTION]->(mySec:Section)<-[:REFERENCES]-(refBySec:Section)<-[:HAS_SECTION]-(refByReg:Regulation)
        WHERE refByReg.id <> r.id
        
        // Find legislation this regulation implements
        OPTIONAL MATCH (r)-[:IMPLEMENTS]->(impl)
        
        RETURN 
            [x IN collect(DISTINCT refReg) WHERE x IS NOT NULL | {id: x.id, title: x.title, type: labels(x)[0]}] as references,
            [x IN collect(DISTINCT refByReg) WHERE x IS NOT NULL | {id: x.id, title: x.title, type: labels(x)[0]}] as referenced_by,
            [x IN collect(DISTINCT impl) WHERE x IS NOT NULL | {id: x.id, title: x.title, type: labels(x)[0]}] as implements
        """
        
        results = neo4j.execute_query(
            query,
            {"regulation_id": str(regulation_id)}
        )
        
        if not results or len(results) == 0:
            return {
                "regulation_id": str(regulation_id),
                "references": [],
                "referenced_by": [],
                "implements": [],
                "counts": {
                    "references": 0,
                    "referenced_by": 0,
                    "implements": 0
                }
            }
        
        result = results[0]
        
        # Results are already filtered by the query, but ensure they're lists
        references = result.get('references', [])
        referenced_by = result.get('referenced_by', [])
        implements = result.get('implements', [])
        
        return {
            "regulation_id": str(regulation_id),
            "references": references,
            "referenced_by": referenced_by,
            "implements": implements,
            "counts": {
                "references": len(references),
                "referenced_by": len(referenced_by),
                "implements": len(implements)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching regulation relationships: {e}")
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
