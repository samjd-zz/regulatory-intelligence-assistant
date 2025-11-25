"""
Main data ingestion pipeline for Canadian regulatory data.
Orchestrates downloading, parsing, and loading into all systems.
"""
import asyncio
import logging
import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models.models import Regulation, Section, Amendment, Citation
from services.graph_builder import GraphBuilder
from services.graph_service import GraphService
from services.search_service import SearchService
from ingestion.canadian_law_xml_parser import CanadianLawXMLParser, ParsedRegulation

logger = logging.getLogger(__name__)


class DataIngestionPipeline:
    """
    Main pipeline for ingesting Canadian regulatory data.
    
    Pipeline stages:
    1. Download XML files from Open Canada dataset
    2. Parse XML with CanadianLawXMLParser
    3. Store in PostgreSQL (regulations, sections, amendments)
    4. Build knowledge graph in Neo4j
    5. Index in Elasticsearch
    6. Upload to Gemini API for RAG
    """
    
    def __init__(
        self,
        db_session: Session,
        graph_service: GraphService,
        search_service: SearchService,
        data_dir: str = "data/regulations"
    ):
        """
        Initialize the pipeline.
        
        Args:
            db_session: Database session
            graph_service: Neo4j graph service
            search_service: Elasticsearch search service
            data_dir: Directory for downloaded data
        """
        self.db = db_session
        self.graph_service = graph_service
        self.search_service = search_service
        self.data_dir = Path(data_dir)
        self.xml_parser = CanadianLawXMLParser()
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'regulations_created': 0,
            'sections_created': 0,
            'amendments_created': 0,
            'citations_created': 0,
            'graph_nodes_created': 0,
            'graph_relationships_created': 0,
            'elasticsearch_indexed': 0
        }
    
    async def ingest_from_directory(self, xml_dir: str, limit: Optional[int] = None):
        """
        Ingest all XML files from a directory.
        
        Args:
            xml_dir: Directory containing XML files
            limit: Maximum number of files to process (for testing)
        """
        xml_path = Path(xml_dir)
        
        if not xml_path.exists():
            raise ValueError(f"Directory not found: {xml_dir}")
        
        # Find all XML files
        xml_files = list(xml_path.glob("*.xml"))
        logger.info(f"Found {len(xml_files)} XML files in {xml_dir}")
        
        if limit:
            xml_files = xml_files[:limit]
            logger.info(f"Limited to {limit} files for processing")
        
        self.stats['total_files'] = len(xml_files)
        
        # Process each file
        for i, xml_file in enumerate(xml_files, 1):
            logger.info(f"[{i}/{len(xml_files)}] Processing {xml_file.name}")
            
            try:
                await self.ingest_xml_file(str(xml_file))
                self.stats['successful'] += 1
            except Exception as e:
                logger.error(f"Failed to ingest {xml_file.name}: {e}", exc_info=True)
                self.stats['failed'] += 1
            
            # Commit after each file
            self.db.commit()
            
            # Log progress every 10 files
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(xml_files)} files processed")
                self._log_stats()
        
        # Final statistics
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 60)
        self._log_stats()
    
    async def ingest_xml_file(self, xml_path: str) -> Dict[str, Any]:
        """
        Ingest a single XML file through the entire pipeline.
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Ingesting: {xml_path}")
        
        # Stage 1: Parse XML
        try:
            parsed_reg = self.xml_parser.parse_file(xml_path)
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            raise
        
        # Check if already exists (by content hash)
        content_hash = self._calculate_content_hash(parsed_reg.full_text)
        existing = self.db.query(Regulation).filter_by(
            content_hash=content_hash
        ).first()
        
        if existing:
            logger.info(f"Regulation already exists: {parsed_reg.title}")
            self.stats['skipped'] += 1
            return {'status': 'skipped', 'regulation_id': str(existing.id)}
        
        # Stage 2: Store in PostgreSQL
        regulation = await self._store_in_postgres(parsed_reg, content_hash)
        self.stats['regulations_created'] += 1
        
        # Stage 3: Build knowledge graph
        try:
            graph_result = await self._build_knowledge_graph(regulation, parsed_reg)
            self.stats['graph_nodes_created'] += graph_result.get('nodes_created', 0)
            self.stats['graph_relationships_created'] += graph_result.get('relationships_created', 0)
        except Exception as e:
            logger.error(f"Knowledge graph creation failed: {e}")
            # Continue even if graph fails
        
        # Stage 4: Index in Elasticsearch
        try:
            await self._index_in_elasticsearch(regulation, parsed_reg)
            self.stats['elasticsearch_indexed'] += 1
        except Exception as e:
            logger.error(f"Elasticsearch indexing failed: {e}")
            # Continue even if ES fails
        
        # Stage 5: Upload to Gemini (optional, for RAG)
        # This will be handled separately as Gemini has API rate limits
        
        logger.info(f"Successfully ingested: {parsed_reg.title}")
        
        return {
            'status': 'success',
            'regulation_id': str(regulation.id),
            'title': regulation.title,
            'sections': len(parsed_reg.sections)
        }
    
    async def _store_in_postgres(
        self,
        parsed_reg: ParsedRegulation,
        content_hash: str
    ) -> Regulation:
        """
        Store parsed regulation in PostgreSQL.
        
        Args:
            parsed_reg: Parsed regulation data
            content_hash: Content hash for deduplication
            
        Returns:
            Created Regulation object
        """
        logger.info(f"Storing in PostgreSQL: {parsed_reg.title}")
        
        # Parse effective date
        effective_date = None
        if parsed_reg.enabled_date:
            try:
                effective_date = datetime.strptime(
                    parsed_reg.enabled_date, '%Y-%m-%d'
                ).date()
            except ValueError:
                logger.warning(f"Could not parse date: {parsed_reg.enabled_date}")
        
        # Create regulation record
        regulation = Regulation(
            title=parsed_reg.title,
            jurisdiction=parsed_reg.jurisdiction,
            authority=parsed_reg.chapter,
            effective_date=effective_date,
            status='active',
            full_text=parsed_reg.full_text,
            content_hash=content_hash,
            extra_metadata=parsed_reg.metadata
        )
        
        self.db.add(regulation)
        self.db.flush()  # Get ID
        
        # Create sections
        section_map = {}  # Map section number to DB object
        
        for parsed_section in parsed_reg.sections:
            section = Section(
                regulation_id=regulation.id,
                section_number=parsed_section.number,
                title=parsed_section.title,
                content=parsed_section.content,
                extra_metadata={
                    'level': parsed_section.level,
                    'section_id': parsed_section.section_id
                }
            )
            
            self.db.add(section)
            self.db.flush()
            
            section_map[parsed_section.number] = section
            self.stats['sections_created'] += 1
            
            # Add subsections as separate sections
            for subsection in parsed_section.subsections:
                sub = Section(
                    regulation_id=regulation.id,
                    section_number=subsection.number,
                    title=subsection.title,
                    content=subsection.content,
                    extra_metadata={
                        'level': subsection.level,
                        'section_id': subsection.section_id,
                        'parent_number': parsed_section.number
                    }
                )
                
                self.db.add(sub)
                self.db.flush()
                
                section_map[subsection.number] = sub
                self.stats['sections_created'] += 1
        
        # Create amendments
        for parsed_amendment in parsed_reg.amendments:
            try:
                amendment_date = datetime.strptime(
                    parsed_amendment.date, '%Y-%m-%d'
                ).date()
            except ValueError:
                logger.warning(f"Could not parse amendment date: {parsed_amendment.date}")
                continue
            
            amendment = Amendment(
                regulation_id=regulation.id,
                amendment_type='modified',
                effective_date=amendment_date,
                description=parsed_amendment.description,
                extra_metadata={
                    'bill_number': parsed_amendment.bill_number
                }
            )
            
            self.db.add(amendment)
            self.stats['amendments_created'] += 1
        
        # Create citations (cross-references)
        for parsed_ref in parsed_reg.cross_references:
            source_section = section_map.get(parsed_ref.source_section)
            target_section = section_map.get(parsed_ref.target_section)
            
            if source_section and target_section:
                citation = Citation(
                    section_id=source_section.id,
                    cited_section_id=target_section.id,
                    citation_text=parsed_ref.citation_text
                )
                
                self.db.add(citation)
                self.stats['citations_created'] += 1
        
        self.db.flush()
        
        logger.info(f"Stored {len(section_map)} sections, "
                   f"{len(parsed_reg.amendments)} amendments, "
                   f"{len(parsed_reg.cross_references)} citations")
        
        return regulation
    
    async def _build_knowledge_graph(
        self,
        regulation: Regulation,
        parsed_reg: ParsedRegulation
    ) -> Dict[str, int]:
        """
        Build knowledge graph in Neo4j.
        
        Args:
            regulation: Regulation DB object
            parsed_reg: Parsed regulation data
            
        Returns:
            Dictionary with counts of created nodes/relationships
        """
        logger.info(f"Building knowledge graph for: {parsed_reg.title}")
        
        # Use GraphBuilder to create graph structure
        from services.graph_builder import GraphBuilder
        
        graph_builder = GraphBuilder(self.graph_service, self.db)
        
        # Build regulation subgraph (this is a synchronous method)
        result = graph_builder.build_regulation_subgraph(str(regulation.id))
        
        logger.info(f"Created {result.get('nodes_created', 0)} nodes, "
                   f"{result.get('relationships_created', 0)} relationships")
        
        return result
    
    async def _index_in_elasticsearch(
        self,
        regulation: Regulation,
        parsed_reg: ParsedRegulation
    ) -> None:
        """
        Index regulation in Elasticsearch.
        
        Args:
            regulation: Regulation DB object
            parsed_reg: Parsed regulation data
        """
        logger.info(f"Indexing in Elasticsearch: {parsed_reg.title}")
        
        # Index the full regulation
        doc = {
            'id': str(regulation.id),
            'regulation_id': str(regulation.id),
            'title': regulation.title,
            'content': regulation.full_text,
            'document_type': 'regulation',
            'jurisdiction': regulation.jurisdiction,
            'authority': regulation.authority,
            'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
            'status': regulation.status,
            'metadata': {
                'chapter': parsed_reg.chapter,
                'act_type': parsed_reg.act_type,
                **parsed_reg.metadata
            }
        }
        
        # index_document is synchronous
        self.search_service.index_document(
            doc_id=str(regulation.id),
            document=doc
        )
        
        # Index individual sections for better search granularity
        sections = self.db.query(Section).filter_by(
            regulation_id=regulation.id
        ).all()
        
        for section in sections:
            section_doc = {
                'id': str(section.id),
                'regulation_id': str(regulation.id),
                'section_id': str(section.id),
                'section_number': section.section_number,
                'title': section.title or regulation.title,
                'content': section.content,
                'document_type': 'section',
                'jurisdiction': regulation.jurisdiction,
                'regulation_title': regulation.title,
                'metadata': section.extra_metadata or {}
            }
            
            self.search_service.index_document(
                doc_id=str(section.id),
                document=section_doc
            )
        
        logger.info(f"Indexed 1 regulation + {len(sections)} sections")
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _log_stats(self):
        """Log current statistics."""
        logger.info("Statistics:")
        logger.info(f"  Total files: {self.stats['total_files']}")
        logger.info(f"  Successful: {self.stats['successful']}")
        logger.info(f"  Failed: {self.stats['failed']}")
        logger.info(f"  Skipped: {self.stats['skipped']}")
        logger.info(f"  Regulations created: {self.stats['regulations_created']}")
        logger.info(f"  Sections created: {self.stats['sections_created']}")
        logger.info(f"  Amendments created: {self.stats['amendments_created']}")
        logger.info(f"  Citations created: {self.stats['citations_created']}")
        logger.info(f"  Graph nodes: {self.stats['graph_nodes_created']}")
        logger.info(f"  Graph relationships: {self.stats['graph_relationships_created']}")
        logger.info(f"  ES documents indexed: {self.stats['elasticsearch_indexed']}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get ingestion statistics."""
        return self.stats.copy()
    
    async def validate_ingestion(self) -> Dict[str, Any]:
        """
        Validate that ingestion was successful.
        
        Returns:
            Validation report
        """
        logger.info("Validating ingestion...")
        
        # Check PostgreSQL
        reg_count = self.db.query(Regulation).count()
        section_count = self.db.query(Section).count()
        amendment_count = self.db.query(Amendment).count()
        
        # Check Neo4j (get_graph_stats is synchronous)
        graph_stats = self.graph_service.get_graph_stats()
        
        # Check Elasticsearch
        es_stats = self.search_service.get_index_stats() if self.search_service else {}
        
        validation = {
            'postgres': {
                'regulations': reg_count,
                'sections': section_count,
                'amendments': amendment_count
            },
            'neo4j': graph_stats,
            'elasticsearch': es_stats,
            'ingestion_stats': self.stats
        }
        
        logger.info("Validation complete:")
        logger.info(json.dumps(validation, indent=2))
        
        return validation


async def main():
    """Main entry point for data ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest Canadian regulatory data')
    parser.add_argument('xml_dir', help='Directory containing XML files')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--validate', action='store_true', help='Validate after ingestion')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create database session
    from database import SessionLocal
    db = SessionLocal()
    
    neo4j_client = None
    
    try:
        # Initialize services
        from utils.neo4j_client import Neo4jClient
        
        neo4j_client = Neo4jClient()
        graph_service = GraphService(neo4j_client)
        
        # Initialize SearchService
        logger.info("Initializing SearchService...")
        search_service = SearchService()
        
        # Create Elasticsearch index if it doesn't exist
        if not search_service.create_index(force_recreate=False):
            logger.warning("Failed to create Elasticsearch index, continuing anyway")
        
        # Create pipeline
        pipeline = DataIngestionPipeline(
            db_session=db,
            graph_service=graph_service,
            search_service=search_service,
            data_dir="data/regulations"
        )
        
        # Run ingestion
        await pipeline.ingest_from_directory(
            xml_dir=args.xml_dir,
            limit=args.limit
        )
        
        # Validate if requested
        if args.validate:
            validation = await pipeline.validate_ingestion()
            print("\nValidation Report:")
            print(json.dumps(validation, indent=2))
        
        logger.info("Ingestion pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
        if neo4j_client:
            neo4j_client.close()


if __name__ == '__main__':
    asyncio.run(main())
