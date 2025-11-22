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
from services.document_parser import DocumentParser
from models.document_models import Document, DocumentType

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
        FOR (l:Legislation) ON EACH [l.title, l.full_text]
        """,
        """
        CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
        FOR (s:Section) ON EACH [s.title, s.content]
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
    Clear all nodes and relationships from the graph.
    
    Args:
        neo4j: Neo4j client instance
        confirm: Confirmation flag
    """
    if not confirm:
        logger.warning("Clear graph called without confirmation - skipping")
        return
    
    logger.warning("CLEARING ALL DATA FROM NEO4J GRAPH...")
    
    query = "MATCH (n) DETACH DELETE n"
    result = neo4j.execute_write(query)
    
    logger.info("Graph cleared successfully")


def populate_from_postgresql(
    db: Session,
    neo4j: Neo4jClient,
    limit: int = None,
    document_types: list = None
):
    """
    Populate Neo4j graph from PostgreSQL documents.
    
    Args:
        db: SQLAlchemy database session
        neo4j: Neo4j client instance
        limit: Maximum number of documents to process
        document_types: List of document types to include
    """
    logger.info("Starting graph population from PostgreSQL...")
    
    # Build query
    query = db.query(Document).filter_by(is_processed=True)
    
    if document_types:
        query = query.filter(Document.document_type.in_(document_types))
    
    if limit:
        query = query.limit(limit)
    
    documents = query.all()
    logger.info(f"Found {len(documents)} documents to process")
    
    # Initialize graph builder
    builder = GraphBuilder(db, neo4j)
    
    # Process each document
    stats = {
        "total": len(documents),
        "successful": 0,
        "failed": 0,
        "total_nodes": 0,
        "total_relationships": 0,
        "errors": []
    }
    
    for i, doc in enumerate(documents, 1):
        logger.info(f"Processing document {i}/{len(documents)}: {doc.title}")
        
        try:
            result = builder.build_document_graph(doc.id)
            
            stats["successful"] += 1
            stats["total_nodes"] += result.get("nodes_created", 0)
            stats["total_relationships"] += result.get("relationships_created", 0)
            
            logger.info(
                f"  ✓ Created {result.get('nodes_created', 0)} nodes, "
                f"{result.get('relationships_created', 0)} relationships"
            )
            
        except Exception as e:
            logger.error(f"  ✗ Failed to process {doc.title}: {e}")
            stats["failed"] += 1
            stats["errors"].append({
                "document": doc.title,
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
    logger.info(f"Total documents processed: {stats['total']}")
    logger.info(f"Successful: {stats['successful']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Total nodes created: {stats['total_nodes']}")
    logger.info(f"Total relationships created: {stats['total_relationships']}")
    
    if stats['errors']:
        logger.warning(f"\nErrors encountered: {len(stats['errors'])}")
        for error in stats['errors'][:5]:  # Show first 5 errors
            logger.warning(f"  - {error['document']}: {error['error']}")
    
    return stats


def upload_sample_documents(db: Session, count: int = 50):
    """
    Create sample documents for testing.
    
    Args:
        db: SQLAlchemy database session
        count: Number of sample documents to create
    """
    logger.info(f"Creating {count} sample documents...")
    
    from datetime import datetime, timedelta
    import uuid
    
    sample_docs = [
        {
            "title": "Employment Insurance Act",
            "type": DocumentType.LEGISLATION,
            "jurisdiction": "federal",
            "authority": "Parliament of Canada",
            "content": """
            Section 7: Eligibility Requirements
            (1) A person is eligible for benefits if they have accumulated 
            sufficient insurable hours of employment.
            
            Section 8: Benefit Period
            (1) The benefit period begins the Sunday of the week in which 
            the interruption of earnings occurs.
            
            Section 9: Rate of Benefits
            (1) The rate of weekly benefits is 55% of average insurable earnings.
            """
        },
        {
            "title": "Canada Pension Plan",
            "type": DocumentType.LEGISLATION,
            "jurisdiction": "federal",
            "authority": "Parliament of Canada",
            "content": """
            Section 44: Retirement Pension
            (1) A retirement pension shall be paid to a contributor who has 
            reached 60 years of age.
            
            Section 45: Amount of Retirement Pension
            (1) The amount of the monthly retirement pension is calculated 
            based on contributory period.
            """
        },
        {
            "title": "Old Age Security Act",
            "type": DocumentType.LEGISLATION,
            "jurisdiction": "federal",
            "authority": "Parliament of Canada",
            "content": """
            Section 3: Eligibility
            (1) A person who has attained 65 years of age and is a Canadian 
            citizen or legal resident is entitled to an old age pension.
            
            Section 5: Amount of Pension
            (1) The amount is determined by the Governor in Council.
            """
        },
        {
            "title": "Employment Insurance Regulations",
            "type": DocumentType.REGULATION,
            "jurisdiction": "federal",
            "authority": "Governor in Council",
            "content": """
            Section 2: Insurable Hours
            (1) Hours of work are insurable if performed under a contract 
            of service.
            
            Section 3: Earnings
            (1) Insurable earnings are the total amount of earnings paid.
            """
        },
        {
            "title": "Immigration and Refugee Protection Act",
            "type": DocumentType.LEGISLATION,
            "jurisdiction": "federal",
            "authority": "Parliament of Canada",
            "content": """
            Section 11: Application
            (1) A foreign national must apply for authorization to enter Canada.
            
            Section 20: Work Permits
            (1) Work permits may be issued to foreign nationals.
            """
        },
    ]
    
    # Replicate samples to reach desired count
    created_count = 0
    base_date = datetime(2020, 1, 1)
    
    while created_count < count:
        for sample in sample_docs:
            if created_count >= count:
                break
            
            doc = Document(
                id=uuid.uuid4(),
                title=f"{sample['title']} (Version {created_count + 1})",
                document_type=sample['type'],
                jurisdiction=sample['jurisdiction'],
                authority=sample['authority'],
                full_text=sample['content'],
                file_format="txt",
                file_size=len(sample['content']),
                file_hash=str(uuid.uuid4()),
                effective_date=base_date + timedelta(days=created_count * 30),
                status="active",
                is_processed=True,
                processed_date=datetime.utcnow()
            )
            
            db.add(doc)
            created_count += 1
    
    db.commit()
    logger.info(f"✓ Created {created_count} sample documents")
    
    # Parse documents to create sections
    logger.info("Parsing documents to create sections...")
    parser = DocumentParser(db)
    
    docs = db.query(Document).filter_by(is_processed=True).all()
    for doc in docs:
        try:
            # Create basic sections from content
            if doc.full_text:
                sections = doc.full_text.split("Section ")
                for i, section_text in enumerate(sections[1:], 1):
                    lines = section_text.strip().split("\n", 1)
                    if len(lines) >= 2:
                        from models.document_models import DocumentSection
                        section = DocumentSection(
                            id=uuid.uuid4(),
                            document_id=doc.id,
                            section_number=str(i),
                            section_title=lines[0].strip(),
                            content=lines[1].strip() if len(lines) > 1 else lines[0],
                            order_index=i-1,
                            level=0
                        )
                        db.add(section)
        except Exception as e:
            logger.warning(f"Failed to parse {doc.title}: {e}")
    
    db.commit()
    logger.info("✓ Sections created")


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
        help="Maximum number of documents to process"
    )
    
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["legislation", "regulation", "policy", "guideline", "directive"],
        help="Document types to include"
    )
    
    parser.add_argument(
        "--create-samples",
        type=int,
        default=0,
        help="Create N sample documents before populating"
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
        
        # Create sample documents if requested
        if args.create_samples > 0:
            upload_sample_documents(db, args.create_samples)
        
        # Convert document types to enum if provided
        doc_types = None
        if args.types:
            doc_types = [DocumentType(t) for t in args.types]
        
        # Populate graph
        stats = populate_from_postgresql(
            db,
            neo4j,
            limit=args.limit,
            document_types=doc_types
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
