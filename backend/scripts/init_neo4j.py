"""
Initialize Neo4j knowledge graph with schema and sample data.
Run this script to set up the graph database.
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
# In Docker: /app/scripts -> /app
# Locally: /path/to/backend/scripts -> /path/to/backend
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.neo4j_client import get_neo4j_client
from services.graph_service import get_graph_service
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_schema():
    """Initialize Neo4j schema with constraints and indexes."""
    logger.info("Initializing Neo4j schema...")
    
    client = get_neo4j_client()
    
    # Read Cypher script
    script_path = Path(__file__).parent / 'init_graph.cypher'
    with open(script_path, 'r') as f:
        cypher_script = f.read()
    
    # Execute each statement separately
    statements = [s.strip() for s in cypher_script.split(';') if s.strip() and not s.strip().startswith('//')]
    
    for statement in statements:
        # Skip empty statements and comments
        if not statement or statement.startswith('//'):
            continue
            
        # Skip verification queries (but allow fulltext index creation)
        if statement.startswith('CALL db.') and 'CREATE FULLTEXT' not in statement:
            continue
            
        try:
            # Clean up the statement (remove comments and extra whitespace)
            clean_statement = ' '.join(line.strip() for line in statement.split('\n') 
                                     if line.strip() and not line.strip().startswith('//'))
            if clean_statement:
                client.execute_write(clean_statement)
                logger.info(f"Executed: {clean_statement[:50]}...")
        except Exception as e:
            logger.warning(f"Statement may have failed (might already exist): {e}")
            logger.debug(f"Failed statement: {statement[:100]}...")
    
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
