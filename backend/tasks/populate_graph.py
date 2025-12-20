"""
Task script to populate Neo4j knowledge graph with regulatory documents.
Can be run standalone or as part of a background job.
"""
import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from database import SessionLocal
from utils.neo4j_client import Neo4jClient
from services.graph_builder import GraphBuilder
from models import Regulation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_neo4j_constraints(neo4j: Neo4jClient):
    """
    Create Neo4j constraints and indexes.
    
    Args:
        neo4j: Neo4j client instance
    """
    logger.info("Setting up Neo4j constraints and indexes...")
    
    constraints = [
        "CREATE CONSTRAINT legislation_id IF NOT EXISTS FOR (l:Legislation) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
        "CREATE CONSTRAINT regulation_id IF NOT EXISTS FOR (r:Regulation) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT policy_id IF NOT EXISTS FOR (p:Policy) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT program_id IF NOT EXISTS FOR (prog:Program) REQUIRE prog.id IS UNIQUE",
        "CREATE CONSTRAINT situation_id IF NOT EXISTS FOR (sit:Situation) REQUIRE sit.id IS UNIQUE",
    ]
    
    indexes = [
        "CREATE INDEX legislation_title IF NOT EXISTS FOR (l:Legislation) ON (l.title)",
        "CREATE INDEX legislation_jurisdiction IF NOT EXISTS FOR (l:Legislation) ON (l.jurisdiction)",
        "CREATE INDEX legislation_status IF NOT EXISTS FOR (l:Legislation) ON (l.status)",
        "CREATE INDEX section_number IF NOT EXISTS FOR (s:Section) ON (s.section_number)",
        "CREATE INDEX program_name IF NOT EXISTS FOR (p:Program) ON (p.name)",
    ]
    
    # Full-text indexes  
    fulltext_indexes = [
        """
        CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
        FOR (l:Legislation) ON EACH [l.title, l.full_text, l.act_number]
        """,
        """
        CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS
        FOR (r:Regulation) ON EACH [r.title, r.full_text]
        """,
        """
        CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
        FOR (s:Section) ON EACH [s.title, s.content, s.section_number]
        """
    ]
    
    for query in constraints + indexes + fulltext_indexes:
        try:
            neo4j.execute_write(query)
            logger.info(f"Executed: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Constraint/index may already exist: {e}")


def clear_graph(neo4j: Neo4jClient, confirm: bool = False):
    """
    Clear all nodes and relationships from the graph in batches.
    
    Args:
        neo4j: Neo4j client instance
        confirm: Confirmation flag
    """
    if not confirm:
        logger.warning("Clear graph called without confirmation - skipping")
        return
    
    logger.warning("CLEARING ALL DATA FROM NEO4J GRAPH...")
    
    # Delete in batches to avoid memory issues
    batch_size = 10000
    total_deleted = 0
    
    while True:
        query = f"""
        MATCH (n)
        WITH n LIMIT {batch_size}
        DETACH DELETE n
        RETURN count(n) as deleted
        """
        
        result = neo4j.execute_query(query)
        deleted = result[0]["deleted"] if result else 0
        
        if deleted == 0:
            break
        
        total_deleted += deleted
        logger.info(f"Deleted {deleted} nodes (total: {total_deleted})...")
    
    logger.info(f"Graph cleared successfully - {total_deleted} nodes deleted")


def populate_from_postgresql(
    db: Session,
    neo4j: Neo4jClient,
    limit: int = None,
    batch_size: int = 100
):
    """
    Populate Neo4j graph from PostgreSQL regulations.
    
    Args:
        db: SQLAlchemy database session
        neo4j: Neo4j client instance
        limit: Maximum number of regulations to process
        batch_size: Number of regulations to process before logging progress
    """
    logger.info("Starting graph population from PostgreSQL...")
    
    # Build query
    query = db.query(Regulation)
    
    if limit:
        query = query.limit(limit)
    
    regulations = query.all()
    logger.info(f"Found {len(regulations)} regulations to process")
    
    # Initialize graph builder
    builder = GraphBuilder(db, neo4j)
    
    # Process each regulation
    stats = {
        "total": len(regulations),
        "successful": 0,
        "failed": 0,
        "total_nodes": 0,
        "total_relationships": 0,
        "errors": []
    }
    
    for i, regulation in enumerate(regulations, 1):
        logger.info(f"Processing regulation {i}/{len(regulations)}: {regulation.title[:60]}...")
        
        try:
            result = builder.build_document_graph(regulation.id)
            
            stats["successful"] += 1
            stats["total_nodes"] += result.get("nodes_created", 0)
            stats["total_relationships"] += result.get("relationships_created", 0)
            
            # Log progress every batch_size regulations
            if i % batch_size == 0:
                logger.info(
                    f"  Progress: {i}/{len(regulations)} | "
                    f"Nodes: {stats['total_nodes']} | "
                    f"Relationships: {stats['total_relationships']}"
                )
            
        except Exception as e:
            logger.error(f"  ✗ Failed to process {regulation.title[:60]}: {e}")
            stats["failed"] += 1
            stats["errors"].append({
                "regulation": regulation.title,
                "error": str(e)
            })
    
    # Create inter-document relationships
    logger.info("\nCreating inter-document relationships...")
    try:
        builder.create_inter_document_relationships()
        logger.info("✓ Inter-document relationships created")
    except Exception as e:
        logger.error(f"✗ Failed to create inter-document relationships: {e}")
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("GRAPH POPULATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total regulations processed: {stats['total']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total nodes created: {stats['total_nodes']}")
    logger.info(f"Total relationships created: {stats['total_relationships']}")
    
    if stats['errors']:
        logger.warning(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            logger.warning(f"  - {error['regulation']}: {error['error']}")
    
    return stats


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Populate Neo4j knowledge graph with regulatory documents"
    )
    
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing graph before populating (DESTRUCTIVE)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of regulations to process"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of regulations to process before logging progress (default: 100)"
    )
    
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Only setup constraints and indexes, don't populate"
    )
    
    args = parser.parse_args()
    
    # Initialize connections
    logger.info("Initializing database connections...")
    db = SessionLocal()
    neo4j = Neo4jClient()
    neo4j.connect()
    
    try:
        # Verify Neo4j connectivity
        if not neo4j.verify_connectivity():
            logger.error("Failed to connect to Neo4j")
            return 1
        
        logger.info("✓ Connected to Neo4j")
        
        # Setup constraints and indexes
        setup_neo4j_constraints(neo4j)
        
        if args.setup_only:
            logger.info("Setup complete. Exiting.")
            return 0
        
        # Clear graph if requested
        if args.clear:
            confirm = input("Are you sure you want to CLEAR THE GRAPH? (yes/no): ")
            if confirm.lower() == "yes":
                clear_graph(neo4j, confirm=True)
            else:
                logger.info("Graph clear cancelled")
                return 1
        
        # Populate graph
        stats = populate_from_postgresql(
            db,
            neo4j,
            limit=args.limit,
            batch_size=args.batch_size
        )
        
        # Print Neo4j graph stats
        logger.info("\nFetching final graph statistics...")
        graph_stats = neo4j.get_graph_stats()
        logger.info(f"Graph statistics: {graph_stats}")
        
        logger.info("\n✓ Graph population complete!")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
        
    finally:
        db.close()
        neo4j.close()


if __name__ == "__main__":
    sys.exit(main())
