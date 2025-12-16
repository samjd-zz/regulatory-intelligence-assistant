#!/usr/bin/env python3
"""
Script to re-index existing regulations from PostgreSQL to Elasticsearch.
This is needed when the Elasticsearch mapping or indexing logic changes.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import SessionLocal
from models.models import Regulation, Section
from services.search_service import SearchService

def main():
    """Re-index all regulations and sections to Elasticsearch."""
    print("Starting re-indexing process...")
    
    # Initialize services
    db = SessionLocal()
    search_service = SearchService()
    
    # Ensure index exists with proper mappings
    print("Creating/recreating Elasticsearch index with proper mappings...")
    if not search_service.create_index(force_recreate=True):
        print("ERROR: Failed to create index. Exiting.")
        return
    print("Index created successfully with custom mappings")
    
    try:
        # Get all regulations
        regulations = db.query(Regulation).all()
        print(f"Found {len(regulations)} regulations to index")
        
        indexed_count = 0
        section_count = 0
        
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
                
                search_service.index_document(
                    doc_id=str(regulation.id),
                    document=doc
                )
                indexed_count += 1
                
                # Index sections
                sections = db.query(Section).filter_by(regulation_id=regulation.id).all()
                for section in sections:
                    section_doc = {
                        'id': str(section.id),
                        'section_id': str(section.id),
                        'regulation_id': str(regulation.id),
                        'section_number': section.section_number,
                        'title': section.title or regulation.title,
                        'content': section.content,
                        'document_type': 'section',
                        'jurisdiction': regulation.jurisdiction,
                        'authority': regulation.authority,
                        'citation': citation,
                        'legislation_name': regulation.title,
                        'language': regulation.language or 'en',  # Add language field to sections too
                        'programs': programs,  # Inherit programs from regulation
                        'metadata': section.extra_metadata or {}
                    }
                    
                    search_service.index_document(
                        doc_id=str(section.id),
                        document=section_doc
                    )
                    section_count += 1
                
                # Progress indicator
                if i % 100 == 0:
                    print(f"Progress: {i}/{len(regulations)} regulations indexed ({section_count} sections)")
                    
            except Exception as e:
                print(f"Error indexing regulation {regulation.id}: {str(e)}")
                continue
        
        print(f"\nRe-indexing complete!")
        print(f"Indexed {indexed_count} regulations")
        print(f"Indexed {section_count} sections")
        print(f"Total documents: {indexed_count + section_count}")
        
    except Exception as e:
        print(f"Error during re-indexing: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()
