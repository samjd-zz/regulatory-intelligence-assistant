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
from config.program_mappings import get_program_detector

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
        self.program_detector = get_program_detector()
        
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
    
    def _determine_node_type(self, title: str) -> str:
        """
        Determine if a regulation should be classified as Legislation or Regulation.
        Uses the same logic as graph_builder.py to ensure consistency.
        
        Args:
            title: Title of the regulation
            
        Returns:
            'Legislation' if it's an Act/Loi, otherwise 'Regulation'
        """
        title_lower = title.lower()
        
        # Acts and Lois (French for laws) are considered Legislation
        if ' act' in title_lower or title_lower.startswith('act ') or title_lower.endswith(' act'):
            return 'Legislation'
        if ' loi' in title_lower or title_lower.startswith('loi ') or title_lower.endswith(' loi'):
            return 'Legislation'
        
        # Everything else is a Regulation (rules, regulations, etc.)
        return 'Regulation'
    
    async def ingest_from_directory(self, xml_dir: str, limit: Optional[int] = None, force: bool = False):
        """
        Ingest all XML files from a directory (including subdirectories).
        Automatically detects language from directory structure (en/ or fr/).
        
        Args:
            xml_dir: Directory containing XML files (may have en/ and fr/ subdirectories)
            limit: Maximum number of files to process (for testing)
            force: If True, skip duplicate checking and re-ingest all files
        """
        xml_path = Path(xml_dir)
        
        if not xml_path.exists():
            raise ValueError(f"Directory not found: {xml_dir}")
        
        # FORCE MODE CLEANUP: Clear Neo4j and Elasticsearch before re-ingestion
        if force:
            logger.warning("=" * 80)
            logger.warning("FORCE MODE: Clearing Neo4j and Elasticsearch data before re-ingestion")
            logger.warning("=" * 80)
            
            # Clear Neo4j knowledge graph
            try:
                logger.info("Clearing Neo4j knowledge graph...")
                clear_result = self.graph_service.clear_all_data()
                if clear_result.get('status') == 'success':
                    logger.info("✓ Neo4j data cleared successfully")
                else:
                    logger.error(f"✗ Neo4j clear failed: {clear_result.get('message')}")
            except Exception as e:
                logger.error(f"✗ Failed to clear Neo4j data: {e}")
            
            # Recreate Elasticsearch index (deletes and recreates)
            try:
                logger.info("Recreating Elasticsearch index...")
                if self.search_service.create_index(force_recreate=True):
                    logger.info("✓ Elasticsearch index recreated successfully")
                else:
                    logger.error("✗ Elasticsearch index recreation failed")
            except Exception as e:
                logger.error(f"✗ Failed to recreate Elasticsearch index: {e}")
            
            logger.warning("=" * 80)
            logger.warning("Cleanup complete. Starting fresh ingestion...")
            logger.warning("=" * 80)
        
        # Find all XML files recursively (to handle en/ and fr/ subdirectories)
        xml_files = list(xml_path.rglob("*.xml"))
        logger.info(f"Found {len(xml_files)} XML files in {xml_dir} (including subdirectories)")
        
        if limit:
            xml_files = xml_files[:limit]
            logger.info(f"Limited to {limit} files for processing")
        
        self.stats['total_files'] = len(xml_files)
        
        # Process each file
        for i, xml_file in enumerate(xml_files, 1):
            logger.info(f"[{i}/{len(xml_files)}] Processing {xml_file.name}")
            
            try:
                await self.ingest_xml_file(str(xml_file), force=force)
                self.stats['successful'] += 1
                
                # Commit after successful ingestion
                try:
                    self.db.commit()
                    logger.debug(f"Committed {xml_file.name} successfully")
                except Exception as commit_error:
                    logger.error(f"Failed to commit after {xml_file.name}: {commit_error}")
                    self.db.rollback()
                    self.stats['failed'] += 1
                    self.stats['successful'] -= 1  # Revert the success count
                    # Continue processing other files
                    
            except Exception as e:
                logger.error(f"Failed to ingest {xml_file.name}: {e}", exc_info=True)
                self.stats['failed'] += 1
                
                # Rollback the failed transaction to clean up the session
                try:
                    self.db.rollback()
                    logger.debug(f"Rolled back failed transaction for {xml_file.name}")
                except Exception as rollback_error:
                    logger.error(f"Rollback also failed: {rollback_error}")
                    # Session is in bad state, try to recover by starting fresh
                    try:
                        self.db.close()
                        # Reopen session using the session maker from database module
                        from database import SessionLocal
                        self.db = SessionLocal()
                        logger.info("Recovered database session after rollback failure")
                    except Exception as recovery_error:
                        logger.critical(f"Failed to recover session: {recovery_error}")
                        raise
            
            # Log progress every 10 files
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{len(xml_files)} files processed")
                self._log_stats()
        
        # Final commit to ensure all data is persisted
        try:
            self.db.commit()
            logger.info("Final commit successful")
        except Exception as e:
            logger.error(f"Final commit failed: {e}")
            self.db.rollback()
            raise
        
        # Final statistics
        logger.info("=" * 60)
        logger.info("INGESTION COMPLETE")
        logger.info("=" * 60)
        self._log_stats()
    
    async def ingest_xml_file(self, xml_path: str, force: bool = False) -> Dict[str, Any]:
        """
        Ingest a single XML file through the entire pipeline.
        
        Args:
            xml_path: Path to XML file
            force: If True, skip duplicate checking and re-ingest
            
        Returns:
            Dictionary with ingestion results
        """
        logger.info(f"Ingesting: {xml_path}")
        
        # Detect language from path (en/ or fr/ subdirectory)
        language = 'en'  # default to English
        xml_path_obj = Path(xml_path)
        # Check if path contains /en/ or /fr/ directory
        if '/fr/' in str(xml_path) or '\\fr\\' in str(xml_path):
            language = 'fr'
        elif any(part == 'fr' for part in xml_path_obj.parts):
            language = 'fr'
        elif '/en/' in str(xml_path) or '\\en\\' in str(xml_path):
            language = 'en'
        elif any(part == 'en' for part in xml_path_obj.parts):
            language = 'en'
        
        logger.info(f"Detected language: {language}")
        
        # Stage 1: Parse XML
        try:
            parsed_reg = self.xml_parser.parse_file(xml_path)
        except Exception as e:
            logger.error(f"XML parsing failed: {e}")
            raise
        
        # Check if already exists (by content hash and title)
        content_hash = self._calculate_content_hash(parsed_reg.full_text)
        
        # Track if this is a duplicate by title+jurisdiction (for graph/ES deduplication)
        is_title_duplicate = False
        
        if not force:
            # Check for duplicates using multiple criteria for robustness
            existing = self.db.query(Regulation).filter(
                Regulation.content_hash == content_hash
            ).first()
            
            # Also check by title and jurisdiction as a fallback
            if not existing and parsed_reg.title:
                existing = self.db.query(Regulation).filter(
                    Regulation.title == parsed_reg.title,
                    Regulation.jurisdiction == parsed_reg.jurisdiction
                ).first()
            
            if existing:
                logger.info(f"Regulation already exists (id={existing.id}): {parsed_reg.title}")
                self.stats['skipped'] += 1
                return {'status': 'skipped', 'regulation_id': str(existing.id)}
        else:
            # Force mode: Check for duplicates by BOTH content_hash AND title+jurisdiction
            # This ensures Neo4j/ES respect PostgreSQL's deduplication strategy
            
            # First check by content_hash
            existing_by_hash = self.db.query(Regulation).filter(
                Regulation.content_hash == content_hash
            ).first()
            
            # Then check by title+jurisdiction (PostgreSQL's deduplication strategy)
            existing_by_title = None
            if parsed_reg.title:
                existing_by_title = self.db.query(Regulation).filter(
                    Regulation.title == parsed_reg.title,
                    Regulation.jurisdiction == parsed_reg.jurisdiction
                ).first()
            
            # Delete existing regulation if found by hash
            if existing_by_hash:
                logger.info(f"Force mode: Deleting existing regulation by hash: {parsed_reg.title}")
                self.db.delete(existing_by_hash)
                self.db.flush()
            
            # Mark as duplicate if another regulation with same title+jurisdiction exists
            # (but different content_hash). This prevents Neo4j/ES from indexing duplicates.
            if existing_by_title and existing_by_title.content_hash != content_hash:
                is_title_duplicate = True
                logger.info(
                    f"Detected title+jurisdiction duplicate (different content_hash): "
                    f"{parsed_reg.title} (existing_id={existing_by_title.id})"
                )
        
        # Stage 2: Store in PostgreSQL
        regulation = await self._store_in_postgres(parsed_reg, content_hash, language)
        self.stats['regulations_created'] += 1
        
        # Stage 3: Build knowledge graph (skip if title+jurisdiction duplicate)
        if not is_title_duplicate:
            try:
                graph_result = await self._build_knowledge_graph(regulation, parsed_reg)
                self.stats['graph_nodes_created'] += graph_result.get('nodes_created', 0)
                self.stats['graph_relationships_created'] += graph_result.get('relationships_created', 0)
            except Exception as e:
                logger.error(f"Knowledge graph creation failed: {e}")
                # Continue even if graph fails
        else:
            logger.info(
                f"Skipping graph creation for title+jurisdiction duplicate: "
                f"{parsed_reg.title} (regulation_id={regulation.id})"
            )
        
        # Stage 4: Index in Elasticsearch (skip if title+jurisdiction duplicate)
        if not is_title_duplicate:
            try:
                await self._index_in_elasticsearch(regulation, parsed_reg)
                self.stats['elasticsearch_indexed'] += 1
            except Exception as e:
                logger.error(f"Elasticsearch indexing failed: {e}")
                # Continue even if ES fails
        else:
            logger.info(
                f"Skipping ES indexing for title+jurisdiction duplicate: "
                f"{parsed_reg.title} (regulation_id={regulation.id})"
            )
        
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
        content_hash: str,
        language: str = 'en'
    ) -> Regulation:
        """
        Store parsed regulation in PostgreSQL.
        
        Args:
            parsed_reg: Parsed regulation data
            content_hash: Content hash for deduplication
            language: Language of the regulation (en or fr)
            
        Returns:
            Created Regulation object
        """
        logger.info(f"Storing in PostgreSQL: {parsed_reg.title} (language: {language})")
        
        # Parse effective date
        effective_date = None
        if parsed_reg.enabled_date:
            try:
                effective_date = datetime.strptime(
                    parsed_reg.enabled_date, '%Y-%m-%d'
                ).date()
            except ValueError:
                logger.warning(f"Could not parse date: {parsed_reg.enabled_date}")
        
        # Detect applicable government programs
        detected_programs = self.program_detector.detect_programs(
            title=parsed_reg.title,
            content=parsed_reg.full_text[:2000]  # Use first 2000 chars for detection
        )
        
        
        # Use federal jurisdiction if parsed jurisdiction is missing or generic
        final_jurisdiction = parsed_reg.jurisdiction
        if not final_jurisdiction or final_jurisdiction == 'unknown':
            final_jurisdiction = "federal"
            logger.info(f"Using default jurisdiction: federal")
        
        # Log detected programs
        if detected_programs:
            logger.info(f"Detected programs: {detected_programs}")
        
        # Merge detected programs and jurisdiction into metadata
        metadata = parsed_reg.metadata.copy() if parsed_reg.metadata else {}
        metadata['programs'] = detected_programs
        
        # Create regulation record
        regulation = Regulation(
            title=parsed_reg.title,
            jurisdiction=final_jurisdiction,
            authority=parsed_reg.chapter,
            language=language,
            effective_date=effective_date,
            status='active',
            full_text=parsed_reg.full_text,
            content_hash=content_hash,
            extra_metadata=metadata
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
        from utils.neo4j_client import get_neo4j_client
        
        # Get Neo4j client (GraphBuilder expects neo4j_client, not graph_service)
        neo4j_client = get_neo4j_client()
        
        # Fix: GraphBuilder expects (db, neo4j_client), not (graph_service, db)
        graph_builder = GraphBuilder(self.db, neo4j_client)
        
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
        
        # Extract programs from metadata
        programs = regulation.extra_metadata.get('programs', []) if regulation.extra_metadata else []
        
        # Determine node type (Legislation vs Regulation) using same logic as graph builder
        node_type = self._determine_node_type(regulation.title)
        
        # Index the full regulation
        doc = {
            'id': str(regulation.id),
            'regulation_id': str(regulation.id),
            'title': regulation.title,
            'content': regulation.full_text,
            'document_type': 'regulation',  # Generic doc type for backward compatibility
            'node_type': node_type,  # Legislation or Regulation
            'jurisdiction': regulation.jurisdiction,
            'authority': regulation.authority,
            'citation': parsed_reg.chapter or regulation.authority or f"{regulation.title}",
            'legislation_name': regulation.title,
            'language': regulation.language or 'en',  # Add language field
            'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
            'status': regulation.status,
            'programs': programs,  # Add programs field for filtering
            'metadata': {
                'chapter': parsed_reg.chapter,
                'act_type': parsed_reg.act_type,
                'programs': programs,
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
        
        # Extract citation and programs for sections (same as regulation)
        section_citation = parsed_reg.chapter or regulation.authority or f"{regulation.title}"
        
        for section in sections:
            section_doc = {
                'id': str(section.id),
                'regulation_id': str(regulation.id),
                'section_id': str(section.id),
                'section_number': section.section_number,
                'title': section.title or regulation.title,
                'content': section.content,
                'document_type': 'section',
                'node_type': node_type,  # Inherit node type from parent regulation
                'jurisdiction': regulation.jurisdiction,
                'authority': regulation.authority,
                'citation': section_citation,
                'legislation_name': regulation.title,
                'regulation_title': regulation.title,
                'language': regulation.language or 'en',  # Inherit language from regulation
                'programs': programs,  # Inherit programs from regulation
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
    
    def sync_regulations_to_elasticsearch(self) -> int:
        """
        Re-index all existing regulations from PostgreSQL to Elasticsearch.
        Useful when Elasticsearch mapping or indexing logic changes.
        
        Returns:
            Number of regulations indexed
        """
        logger.info("Re-indexing regulations to Elasticsearch...")
        
        regulations = self.db.query(Regulation).all()
        logger.info(f"Found {len(regulations)} regulations to re-index")
        
        indexed_count = 0
        
        for regulation in regulations:
            try:
                # Extract citation and programs from extra_metadata
                citation = regulation.authority
                programs = []
                if regulation.extra_metadata:
                    citation = (
                        regulation.extra_metadata.get('chapter') or
                        regulation.extra_metadata.get('act_number') or
                        regulation.authority or
                        regulation.title
                    )
                    programs = regulation.extra_metadata.get('programs', [])
                
                # Index the regulation
                doc = {
                    'id': str(regulation.id),
                    'regulation_id': str(regulation.id),
                    'title': regulation.title,
                    'content': regulation.full_text,
                    'document_type': 'regulation',
                    'jurisdiction': regulation.jurisdiction,
                    'authority': regulation.authority,
                    'citation': citation,
                    'legislation_name': regulation.title,
                    'language': regulation.language or 'en',  # Add language field
                    'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
                    'status': regulation.status,
                    'programs': programs,  # Add programs field
                    'metadata': regulation.extra_metadata or {}
                }
                
                self.search_service.index_document(
                    doc_id=str(regulation.id),
                    document=doc
                )
                
                # Also re-index all sections for this regulation
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
                        'authority': regulation.authority,
                        'citation': citation,
                        'legislation_name': regulation.title,
                        'regulation_title': regulation.title,
                        'language': regulation.language or 'en',  # Inherit language from regulation
                        'programs': programs,  # Inherit programs from regulation
                        'metadata': section.extra_metadata or {}
                    }
                    
                    self.search_service.index_document(
                        doc_id=str(section.id),
                        document=section_doc
                    )
                
                indexed_count += 1
                
                if indexed_count % 10 == 0:
                    logger.info(f"Indexed {indexed_count}/{len(regulations)} regulations")
                    
            except Exception as e:
                logger.error(f"Failed to index regulation {regulation.id}: {e}")
        
        logger.info(f"Successfully re-indexed {indexed_count} regulations")
        return indexed_count
    
    async def validate_ingestion(self) -> Dict[str, Any]:
        """
        Validate that ingestion was successful.
        
        Returns:
            Validation report
        """
        logger.info("Validating ingestion...")
        
        # Ensure all changes are committed before validation
        try:
            self.db.commit()
        except Exception as e:
            logger.warning(f"Commit before validation failed: {e}")
        
        # Create a fresh session for validation to ensure we see committed data
        from database import SessionLocal
        validation_db = SessionLocal()
        
        try:
            # Check PostgreSQL with fresh session
            reg_count = validation_db.query(Regulation).count()
            section_count = validation_db.query(Section).count()
            amendment_count = validation_db.query(Amendment).count()
            
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
        finally:
            # Close validation session
            validation_db.close()


async def main():
    """Main entry point for data ingestion."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest Canadian regulatory data')
    parser.add_argument('xml_dir', help='Directory containing XML files')
    parser.add_argument('--limit', type=int, help='Limit number of files to process')
    parser.add_argument('--validate', action='store_true', help='Validate after ingestion')
    parser.add_argument('--force', action='store_true', help='Force re-ingestion, skip duplicate checking')
    
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
        logger.info("Starting ingestion...")
        await pipeline.ingest_from_directory(
            xml_dir=args.xml_dir,
            limit=args.limit,
            force=args.force
        )
        logger.info("Ingestion completed, now committing main session...")
        
        # Ensure final commit in main session (pipeline already committed, but be explicit)
        try:
            db.commit()
            logger.info("✓ Main session final commit successful")
        except Exception as e:
            logger.error(f"✗ Main session commit FAILED: {e}", exc_info=True)
        
        # Validate if requested
        if args.validate:
            validation = await pipeline.validate_ingestion()
            print("\nValidation Report:")
            print(json.dumps(validation, indent=2))
        
        logger.info("Ingestion pipeline completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        # Close session without rollback (data already committed)
        db.close()
        if neo4j_client:
            neo4j_client.close()


if __name__ == '__main__':
    asyncio.run(main())
