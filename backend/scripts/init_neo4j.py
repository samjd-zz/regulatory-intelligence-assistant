"""
Initialize Neo4j knowledge graph with schema and sample data.
Run this script to set up the graph database.
"""
import sys
import os

# Add backend directory to Python path
# In Docker: /app/scripts -> /app
# Locally: /path/to/backend/scripts -> /path/to/backend
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from utils.neo4j_client import get_neo4j_client
from utils.neo4j_indexes import setup_neo4j_constraints
from services.graph_service import get_graph_service
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_schema():
    """Initialize Neo4j schema with constraints and indexes."""
    logger.info("Initializing Neo4j schema...")

    client = get_neo4j_client()

    # Use the centralized constraint and index setup
    setup_neo4j_constraints(client)

    logger.info("✓ Schema initialization complete")


def main():
    """Main initialization function."""
    print("\n" + "="*60)
    print("Neo4j Knowledge Graph Initialization")
    print("="*60 + "\n")
    
    try:
        # Step 1: Initialize schema
        init_schema()
        
        # Sample data creation removed - using real regulatory dataset instead
        
        print("\n" + "="*60)
        print("✓ Neo4j initialization completed successfully!")
        print("="*60)
        print("\nYou can now:")
        print("1. View the graph in Neo4j Browser: http://localhost:7474")
        print("2. Run queries using the graph service")
        print("3. Test the health check: curl http://localhost:8000/health/neo4j")
        print("\n")
        
    except Exception as e:
        logger.error(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
