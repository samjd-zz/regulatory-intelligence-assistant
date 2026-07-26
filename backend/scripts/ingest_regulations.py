#!/usr/bin/env python3
"""
Script to ingest SOR/DORS regulations from the en-regs and fr-regs directories.
This script processes regulation XML files and loads them into PostgreSQL, Neo4j, and Elasticsearch.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from services.graph_service import GraphService
from services.search_service import SearchService
from ingestion.data_pipeline import DataIngestionPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Ingest regulations from en-regs and fr-regs directories."""
    logger.info("=" * 80)
    logger.info("SOR/DORS Regulations Ingestion")
    logger.info("=" * 80)
    
    db = SessionLocal()
    try:
        # Initialize services
        graph_service = GraphService()
        search_service = SearchService()
        
        pipeline = DataIngestionPipeline(
            db_session=db,
            graph_service=graph_service,
            search_service=search_service
        )
        
        # Ingest English regulations
        en_regs_dir = Path(__file__).parent.parent / "data/regulations/canadian_laws/en-regs"
        if en_regs_dir.exists():
            xml_files = list(en_regs_dir.glob("*.xml"))
            if xml_files:
                logger.info(f"\nIngesting {len(xml_files)} English regulations from {en_regs_dir}")
                await pipeline.ingest_from_directory(
                    str(en_regs_dir),
                    force=False
                )
            else:
                logger.info(f"No XML files found in {en_regs_dir}")
        else:
            logger.warning(f"Directory not found: {en_regs_dir}")
        
        # Ingest French regulations
        fr_regs_dir = Path(__file__).parent.parent / "data/regulations/canadian_laws/fr-regs"
        if fr_regs_dir.exists():
            xml_files = list(fr_regs_dir.glob("*.xml"))
            if xml_files:
                logger.info(f"\nIngesting {len(xml_files)} French regulations from {fr_regs_dir}")
                await pipeline.ingest_from_directory(
                    str(fr_regs_dir),
                    force=False
                )
            else:
                logger.info(f"No XML files found in {fr_regs_dir}")
        else:
            logger.warning(f"Directory not found: {fr_regs_dir}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Ingestion Complete!")
        logger.info("=" * 80)
        logger.info(f"Statistics: {pipeline.stats}")
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
