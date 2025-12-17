#!/usr/bin/env python3
"""
Overnight Neo4j Re-indexing Script

Safely clears and re-populates Neo4j with the full regulatory dataset.
Designed to handle large datasets without Java heap errors using batched operations.

Usage:
    python scripts/reindex_neo4j_overnight.py [--batch-size 50] [--max-retries 3] [--dry-run]
"""

import sys
import os
import time
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.models import Regulation, Section
from utils.neo4j_client import get_neo4j_client
from services.graph_service import get_graph_service
from tasks.populate_graph import setup_neo4j_constraints

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('neo4j_reindex.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Neo4jReindexer:
    """Safe overnight Neo4j re-indexing with progress tracking."""
    
    def __init__(self, batch_size: int = 50, max_retries: int = 3):
        """
        Initialize reindexer.
        
        Args:
            batch_size: Number of documents to process per batch
            max_retries: Maximum retry attempts for failed batches
        """
        self.batch_size = batch_size
        self.max_retries = max_retries
        self.db = SessionLocal()
        self.neo4j = get_neo4j_client()
        self.graph_service = get_graph_service()
        self.progress_file = Path('neo4j_reindex_progress.json')
        
    def get_dataset_stats(self) -> Dict[str, int]:
        """Get statistics about the dataset to be processed."""
        reg_count = self.db.query(Regulation).count()
        section_count = self.db.query(Section).count()
        
        return {
            'total_regulations': reg_count,
            'total_sections': section_count,
            'total_documents': reg_count + section_count,
            'estimated_batches': (reg_count + self.batch_size - 1) // self.batch_size
        }
    
    def save_progress(self, progress: Dict[str, Any]) -> None:
        """Save progress to file for resumability."""
        progress['timestamp'] = datetime.utcnow().isoformat()
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def load_progress(self) -> Optional[Dict[str, Any]]:
        """Load progress from file if it exists."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")
        return None
    
    def clear_neo4j_safely(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Safely clear Neo4j using batched deletion.
        
        Args:
            dry_run: If True, just check what would be deleted
            
        Returns:
            Deletion statistics
        """
        logger.info("🗑️  Checking current Neo4j data...")
        
        # Get current stats
        current_stats = self.graph_service.get_graph_overview()
        total_nodes = sum(current_stats.get('nodes', {}).values())
        total_rels = sum(current_stats.get('relationships', {}).values())
        
        logger.info(f"Current Neo4j contains:")
        logger.info(f"  📊 Nodes: {total_nodes:,}")
        logger.info(f"  🔗 Relationships: {total_rels:,}")
        
        if dry_run:
            return {
                'dry_run': True,
                'nodes_to_delete': total_nodes,
                'relationships_to_delete': total_rels
            }
        
        if total_nodes == 0:
            logger.info("✅ Neo4j is already empty")
            return {'status': 'success', 'message': 'Already empty'}
        
        logger.warning(f"⚠️  About to DELETE {total_nodes:,} nodes and {total_rels:,} relationships")
        
        # Perform batched deletion
        start_time = time.time()
        result = self.graph_service.clear_all_data()
        elapsed = time.time() - start_time
        
        logger.info(f"✅ Deletion completed in {elapsed:.1f} seconds")
        return result
    
    def populate_in_batches(self, dry_run: bool = False, resume: bool = False) -> Dict[str, Any]:
        """
        Populate Neo4j in safe batches.
        
        Args:
            dry_run: If True, just show what would be processed
            resume: If True, try to resume from previous progress
            
        Returns:
            Population statistics
        """
        # Load previous progress if resuming
        progress = None
        if resume:
            progress = self.load_progress()
            if progress:
                logger.info(f"📂 Resuming from previous progress: {progress['processed_batches']}/{progress['total_batches']} batches")
        
        # Get dataset statistics
        stats = self.get_dataset_stats()
        logger.info(f"📊 Dataset Statistics:")
        logger.info(f"  📄 Regulations: {stats['total_regulations']:,}")
        logger.info(f"  📝 Sections: {stats['total_sections']:,}")
        logger.info(f"  🎯 Estimated batches: {stats['estimated_batches']:,} (batch size: {self.batch_size})")
        
        if dry_run:
            return {
                'dry_run': True,
                'dataset_stats': stats,
                'estimated_time_hours': stats['estimated_batches'] * 0.1  # Estimate 6 seconds per batch
            }
        
        # Initialize progress tracking
        start_offset = 0
        if progress and resume:
            start_offset = progress.get('processed_documents', 0)
            logger.info(f"🔄 Resuming from document {start_offset:,}")
        
        total_stats = {
            'total_processed': start_offset,
            'total_successful': 0,
            'total_failed': 0,
            'total_nodes_created': 0,
            'total_relationships_created': 0,
            'batches_completed': progress.get('processed_batches', 0) if progress else 0,
            'errors': [],
            'start_time': time.time()
        }
        
        # Process regulations in batches
        logger.info(f"🚀 Starting batch processing from offset {start_offset:,}")
        
        try:
            batch_num = total_stats['batches_completed'] + 1
            while True:
                # Get batch of regulations
                regulations = (self.db.query(Regulation)
                             .filter(Regulation.full_text.isnot(None))
                             .offset(start_offset)
                             .limit(self.batch_size)
                             .all())
                
                if not regulations:
                    logger.info("✅ All regulations processed")
                    break
                
                batch_start_time = time.time()
                logger.info(f"📦 Processing batch {batch_num:,}/{stats['estimated_batches']:,} "
                          f"({len(regulations)} regulations, offset {start_offset:,})")
                
                # Process batch with retries
                batch_success = False
                for retry in range(self.max_retries):
                    try:
                        # Process this batch of regulations directly
                        batch_stats = self._process_regulation_batch(regulations)
                        
                        # Update totals
                        total_stats['total_successful'] += batch_stats.get('successful', 0)
                        total_stats['total_failed'] += batch_stats.get('failed', 0)
                        total_stats['total_nodes_created'] += batch_stats.get('nodes_created', 0)
                        total_stats['total_relationships_created'] += batch_stats.get('relationships_created', 0)
                        
                        batch_success = True
                        break
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Batch {batch_num} retry {retry + 1}/{self.max_retries} failed: {e}")
                        if retry == self.max_retries - 1:
                            total_stats['errors'].append({
                                'batch': batch_num,
                                'offset': start_offset,
                                'error': str(e),
                                'timestamp': datetime.utcnow().isoformat()
                            })
                        else:
                            time.sleep(30)  # Wait before retry
                
                # Update progress
                if batch_success:
                    total_stats['batches_completed'] += 1
                    total_stats['total_processed'] += len(regulations)
                    
                    batch_elapsed = time.time() - batch_start_time
                    remaining_batches = stats['estimated_batches'] - total_stats['batches_completed']
                    estimated_remaining_hours = (remaining_batches * batch_elapsed) / 3600
                    
                    logger.info(f"✅ Batch {batch_num} completed in {batch_elapsed:.1f}s "
                              f"(~{estimated_remaining_hours:.1f}h remaining)")
                    
                    # Save progress
                    progress_data = {
                        'processed_batches': total_stats['batches_completed'],
                        'total_batches': stats['estimated_batches'],
                        'processed_documents': total_stats['total_processed'],
                        'successful': total_stats['total_successful'],
                        'failed': total_stats['total_failed'],
                        'nodes_created': total_stats['total_nodes_created'],
                        'relationships_created': total_stats['total_relationships_created']
                    }
                    self.save_progress(progress_data)
                    
                else:
                    logger.error(f"❌ Batch {batch_num} failed after {self.max_retries} retries")
                
                # Move to next batch
                start_offset += self.batch_size
                batch_num += 1
                
                # Small delay to prevent overwhelming Neo4j
                time.sleep(5)
                
        except KeyboardInterrupt:
            logger.warning("⚠️  Process interrupted by user")
            total_stats['interrupted'] = True
        
        except Exception as e:
            logger.error(f"💥 Fatal error during population: {e}")
            total_stats['fatal_error'] = str(e)
        
        finally:
            # Calculate final statistics
            total_elapsed = time.time() - total_stats['start_time']
            total_stats['total_time_hours'] = total_elapsed / 3600
            
            # Final Neo4j stats
            final_graph_stats = self.graph_service.get_graph_overview()
            total_stats['final_graph_stats'] = final_graph_stats
        
        return total_stats
    
    def run_full_reindex(self, dry_run: bool = False, resume: bool = False) -> Dict[str, Any]:
        """
        Run complete reindexing process.
        
        Args:
            dry_run: If True, just show what would be done
            resume: If True, try to resume from previous run
            
        Returns:
            Complete reindexing statistics
        """
        logger.info("🌙 Starting overnight Neo4j re-indexing...")
        logger.info(f"⚙️  Configuration: batch_size={self.batch_size}, max_retries={self.max_retries}")
        
        results = {
            'start_time': datetime.utcnow().isoformat(),
            'configuration': {
                'batch_size': self.batch_size,
                'max_retries': self.max_retries,
                'dry_run': dry_run,
                'resume': resume
            }
        }
        
        try:
            # Step 1: Check dataset
            dataset_stats = self.get_dataset_stats()
            results['dataset_stats'] = dataset_stats
            logger.info(f"📊 Dataset: {dataset_stats['total_documents']:,} documents to process")
            
            # Step 2: Clear Neo4j (unless resuming)
            if not resume:
                logger.info("🗑️  Step 1/3: Clearing existing Neo4j data...")
                clear_result = self.clear_neo4j_safely(dry_run=dry_run)
                results['clear_result'] = clear_result
            else:
                logger.info("🔄 Step 1/3: Skipping clear (resuming previous run)")
                results['clear_result'] = {'skipped': True, 'reason': 'resume'}
            
            # Step 3: Setup schema
            if not dry_run:
                logger.info("🏗️  Step 2/3: Setting up Neo4j schema...")
                setup_neo4j_constraints(self.neo4j)
                logger.info("✅ Schema setup complete")
            
            # Step 4: Populate data
            logger.info("📥 Step 3/3: Populating Neo4j with regulatory data...")
            populate_result = self.populate_in_batches(dry_run=dry_run, resume=resume)
            results['populate_result'] = populate_result
            
            results['end_time'] = datetime.utcnow().isoformat()
            results['status'] = 'completed'
            
            # Summary
            if not dry_run:
                logger.info("🎉 Neo4j re-indexing completed!")
                logger.info(f"📊 Final statistics:")
                logger.info(f"  ✅ Successful: {populate_result['total_successful']:,}")
                logger.info(f"  ❌ Failed: {populate_result['total_failed']:,}")
                logger.info(f"  🏗️  Nodes created: {populate_result['total_nodes_created']:,}")
                logger.info(f"  🔗 Relationships: {populate_result['total_relationships_created']:,}")
                logger.info(f"  ⏱️  Total time: {populate_result['total_time_hours']:.1f} hours")
            else:
                logger.info("🔍 Dry run completed - no changes made")
            
        except Exception as e:
            logger.error(f"💥 Fatal error during re-indexing: {e}")
            results['status'] = 'failed'
            results['error'] = str(e)
        
        finally:
            # Cleanup
            self.cleanup()
        
        return results
    
    def _process_regulation_batch(self, regulations: List['Regulation']) -> Dict[str, int]:
        """Process a batch of regulations directly using Cypher queries"""
        
        stats = {
            'successful': 0,
            'failed': 0,
            'nodes_created': 0,
            'relationships_created': 0
        }
        
        try:
            for regulation in regulations:
                try:
                    # Get sections for this regulation
                    sections = self.db.query(Section).filter(
                        Section.regulation_id == regulation.id
                    ).all()
                    
                    # Create regulation node
                    reg_query = """
                    MERGE (r:Regulation {id: $id})
                    SET r.title = $title,
                        r.jurisdiction = $jurisdiction,
                        r.authority = $authority,
                        r.language = $language,
                        r.status = $status,
                        r.full_text = $full_text,
                        r.effective_date = $effective_date,
                        r.created_at = $created_at,
                        r.updated_at = $updated_at
                    RETURN r
                    """
                    
                    reg_params = {
                        'id': str(regulation.id),
                        'title': regulation.title,
                        'jurisdiction': regulation.jurisdiction,
                        'authority': regulation.authority,
                        'language': regulation.language,
                        'status': regulation.status,
                        'full_text': regulation.full_text,
                        'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
                        'created_at': regulation.created_at.isoformat() if regulation.created_at else None,
                        'updated_at': regulation.updated_at.isoformat() if regulation.updated_at else None
                    }
                    
                    self.neo4j.execute_write(reg_query, reg_params)
                    stats['nodes_created'] += 1
                    
                    # Create section nodes and relationships
                    for section in sections:
                        try:
                            section_query = """
                            MATCH (r:Regulation {id: $regulation_id})
                            MERGE (s:Section {id: $section_id})
                            SET s.section_number = $section_number,
                                s.title = $title,
                                s.content = $content,
                                s.created_at = $created_at,
                                s.updated_at = $updated_at
                            MERGE (r)-[:HAS_SECTION]->(s)
                            RETURN s
                            """
                            
                            section_params = {
                                'regulation_id': str(regulation.id),
                                'section_id': str(section.id),
                                'section_number': section.section_number,
                                'title': section.title,
                                'content': section.content,
                                'created_at': section.created_at.isoformat() if section.created_at else None,
                                'updated_at': section.updated_at.isoformat() if section.updated_at else None
                            }
                            
                            self.neo4j.execute_write(section_query, section_params)
                            stats['nodes_created'] += 1
                            stats['relationships_created'] += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to process section {section.id}: {e}")
                            stats['failed'] += 1
                    
                    stats['successful'] += 1
                            
                except Exception as e:
                    logger.warning(f"Failed to process regulation {regulation.id}: {e}")
                    stats['failed'] += 1
                    
            return stats
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            raise

    def cleanup(self):
        """Clean up resources."""
        if self.db:
            self.db.close()
        if self.neo4j:
            self.neo4j.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Overnight Neo4j re-indexing")
    parser.add_argument('--batch-size', type=int, default=50, 
                       help='Number of documents per batch (default: 50)')
    parser.add_argument('--max-retries', type=int, default=3,
                       help='Maximum retries for failed batches (default: 3)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--resume', action='store_true', 
                       help='Resume from previous progress')
    
    args = parser.parse_args()
    
    # Create reindexer
    reindexer = Neo4jReindexer(
        batch_size=args.batch_size,
        max_retries=args.max_retries
    )
    
    # Run reindexing
    try:
        results = reindexer.run_full_reindex(
            dry_run=args.dry_run,
            resume=args.resume
        )
        
        # Save final results
        with open('neo4j_reindex_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        if results['status'] == 'completed':
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())