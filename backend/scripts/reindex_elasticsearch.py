#!/usr/bin/env python3
"""
Script to re-index existing regulations from PostgreSQL to Elasticsearch.
This is needed when the Elasticsearch mapping or indexing logic changes.

Usage:
    # Incremental update (default) - updates existing documents, adds new ones
    python backend/scripts/reindex_elasticsearch.py
    
    # Full recreation - deletes and rebuilds index from scratch
    python backend/scripts/reindex_elasticsearch.py --force-recreate
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.models import Regulation, Section
from services.search_service import SearchService

def determine_node_type(title: str) -> str:
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

def main():
    """Re-index all regulations and sections to Elasticsearch."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Re-index regulations from PostgreSQL to Elasticsearch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Incremental update (default) - updates existing documents, adds new ones
  python backend/scripts/reindex_elasticsearch.py
  
  # Full recreation - deletes and rebuilds index from scratch
  python backend/scripts/reindex_elasticsearch.py --force-recreate
  
Notes:
  - Incremental mode is faster and safer (no downtime)
  - Use --force-recreate when mappings change or for complete reset
  - Documents with same ID will be updated automatically
        """
    )
    parser.add_argument(
        '--force-recreate',
        action='store_true',
        help='Delete and recreate the index (default: update existing index)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=2500,
        help='Number of documents to index in each batch (default: 2500)'
    )
    args = parser.parse_args()
    
    print("=" * 80)
    print(f"Starting re-indexing process (force_recreate={args.force_recreate})")
    print("=" * 80)
    
    # Initialize services
    db = SessionLocal()
    search_service = SearchService()
    
    # Ensure index exists with proper mappings
    if args.force_recreate:
        print("\n⚠️  FORCE RECREATE MODE: Deleting and recreating index...")
        print("    This will cause temporary search downtime.")
    else:
        print("\n✓ INCREMENTAL UPDATE MODE: Updating existing index...")
        print("    Index will remain searchable during re-indexing.")
        print("    Documents with same ID will be updated automatically.")
    
    if not search_service.create_index(force_recreate=args.force_recreate):
        print("\n❌ ERROR: Failed to create/update index. Exiting.")
        return
    
    if args.force_recreate:
        print("✓ Index recreated successfully with custom mappings")
    else:
        print("✓ Index ready for updates")
    
    try:
        # Get all regulations
        regulations = db.query(Regulation).all()
        print(f"\nFound {len(regulations)} regulations to index")
        print(f"Batch size: {args.batch_size} documents per batch\n")
        
        # Batch processing
        batch = []
        indexed_regulations = 0
        indexed_sections = 0
        total_docs = 0
        failed_docs = 0
        
        def flush_batch():
            """Flush the current batch to Elasticsearch"""
            nonlocal total_docs, failed_docs
            if not batch:
                return
            
            success, failed = search_service.bulk_index_documents(
                documents=batch,
                generate_embeddings=True
            )
            total_docs += success
            failed_docs += failed
            
            if failed > 0:
                print(f"   ⚠️  Batch had {failed} failures")
            
            batch.clear()
        
        for i, regulation in enumerate(regulations, 1):
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
                
                # Determine node type (Legislation vs Regulation)
                node_type = determine_node_type(regulation.title)
                
                # Prepare the regulation document
                doc = {
                    'id': str(regulation.id),
                    'regulation_id': str(regulation.id),
                    'title': regulation.title,
                    'regulation_title': regulation.title,
                    'content': regulation.full_text,
                    'document_type': 'regulation',
                    'node_type': node_type,
                    'jurisdiction': regulation.jurisdiction,
                    'authority': regulation.authority,
                    'citation': citation,
                    'legislation_name': regulation.title,
                    'language': regulation.language or 'en',
                    'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
                    'status': regulation.status,
                    'programs': programs,
                    'metadata': regulation.extra_metadata or {}
                }
                
                batch.append(doc)
                indexed_regulations += 1
                
                # Add sections to batch
                sections = db.query(Section).filter_by(regulation_id=regulation.id).all()
                for section in sections:
                    section_doc = {
                        'id': str(section.id),
                        'section_id': str(section.id),
                        'regulation_id': str(regulation.id),
                        'section_number': section.section_number,
                        'title': section.title or regulation.title,
                        'regulation_title': regulation.title,
                        'content': section.content,
                        'document_type': 'section',
                        'node_type': node_type,
                        'jurisdiction': regulation.jurisdiction,
                        'authority': regulation.authority,
                        'citation': citation,
                        'legislation_name': regulation.title,
                        'language': regulation.language or 'en',
                        'programs': programs,
                        'metadata': section.extra_metadata or {}
                    }
                    
                    batch.append(section_doc)
                    indexed_sections += 1
                    
                    # Flush batch if it reaches the batch size
                    if len(batch) >= args.batch_size:
                        flush_batch()
                
                # Flush batch if it reaches the batch size (after adding regulation + sections)
                if len(batch) >= args.batch_size:
                    flush_batch()
                
                # Progress indicator
                if i % 10 == 0:
                    print(f"Progress: {i}/{len(regulations)} regulations processed "
                          f"({indexed_sections} sections, {total_docs} docs indexed)")
                    
            except Exception as e:
                print(f"Error processing regulation {regulation.id}: {str(e)}")
                continue
        
        # Flush any remaining documents in the batch
        if batch:
            print(f"\nFlushing final batch of {len(batch)} documents...")
            flush_batch()
        
        print("\n" + "=" * 80)
        print("Re-indexing complete!")
        print("=" * 80)
        print(f"✓ Processed {indexed_regulations} regulations")
        print(f"✓ Processed {indexed_sections} sections")
        print(f"✓ Successfully indexed: {total_docs} documents")
        if failed_docs > 0:
            print(f"⚠️  Failed: {failed_docs} documents")
        print(f"\nBatch size used: {args.batch_size} documents per batch")
        print("Note: Existing documents with same ID were updated automatically.")
        print("=" * 80)
        
    except Exception as e:
        print(f"Error during re-indexing: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()
