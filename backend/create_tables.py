#!/usr/bin/env python3
"""
Script to create all database tables.
"""
import sys
sys.path.insert(0, '.')

from database import Base, engine

# Import all models to register them with Base
from models.document_models import (
    Document,
    DocumentSection,
    DocumentSubsection,
    DocumentClause,
    CrossReference,
    DocumentMetadata,
)

def create_tables():
    """Create all tables in the database."""
    print("Creating database tables...")
    Base.metadata.create_all(engine)
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    
    print(f"\n✅ Successfully created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table}")
    
    # Check for document tables specifically
    document_tables = [t for t in tables if 'document' in t or 'cross_reference' in t]
    if document_tables:
        print(f"\n📄 Document-related tables ({len(document_tables)}):")
        for table in document_tables:
            print(f"  ✅ {table}")
    else:
        print("\n⚠️  Warning: No document tables found!")

if __name__ == "__main__":
    create_tables()
