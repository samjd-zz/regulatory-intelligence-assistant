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
    
    try:
        # Get all regulations
        regulations = db.query(Regulation).all()
        print(f"Found {len(regulations)} regulations to index")
        
        indexed_count = 0
        section_count = 0
        
        for i, regulation in enumerate(regulations, 1):
            try:
                # Extract citation from extra_metadata
                citation = regulation.authority
                if regulation.extra_metadata:
                    citation = (
                        regulation.extra_metadata.get('chapter') or
                        regulation.extra_metadata.get('act_number') or
                        regulation.authority or
                        regulation.title
                    )
                
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
                    'effective_date': regulation.effective_date.isoformat() if regulation.effective_date else None,
                    'status': regulation.status,
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
