"""add_fulltext_search_indexes

Revision ID: g2h4j5k6m7n8
Revises: f8a9c3d2e1b4
Create Date: 2025-12-12 12:43:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'g2h4j5k6m7n8'
down_revision = 'f8a9c3d2e1b4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add PostgreSQL full-text search support for Tier 4 fallback in multi-tier RAG system.
    
    This migration adds:
    1. Generated ts_vector columns for regulations and sections
    2. GIN indexes for fast full-text search
    3. Support for both English and French text search
    
    Performance: GIN indexes enable sub-second full-text searches across 270k+ documents.
    """
    
    # Add search_vector column to regulations table
    # Uses GENERATED ALWAYS to automatically update when title or full_text changes
    op.execute("""
        ALTER TABLE regulations 
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(full_text, '')), 'B')
        ) STORED;
    """)
    
    # Add search_vector column to sections table
    op.execute("""
        ALTER TABLE sections
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(content, '')), 'B')
        ) STORED;
    """)
    
    # Create GIN indexes for fast full-text search
    # GIN (Generalized Inverted Index) is optimized for full-text search
    op.execute("""
        CREATE INDEX ix_regulations_search_vector 
        ON regulations 
        USING gin(search_vector);
    """)
    
    op.execute("""
        CREATE INDEX ix_sections_search_vector 
        ON sections 
        USING gin(search_vector);
    """)
    
    # Add French language support columns (optional, for bilingual search)
    op.execute("""
        ALTER TABLE regulations 
        ADD COLUMN search_vector_fr tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('french', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('french', coalesce(full_text, '')), 'B')
        ) STORED;
    """)
    
    op.execute("""
        ALTER TABLE sections
        ADD COLUMN search_vector_fr tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('french', coalesce(title, '')), 'A') ||
            setweight(to_tsvector('french', coalesce(content, '')), 'B')
        ) STORED;
    """)
    
    # Create GIN indexes for French full-text search
    op.execute("""
        CREATE INDEX ix_regulations_search_vector_fr 
        ON regulations 
        USING gin(search_vector_fr);
    """)
    
    op.execute("""
        CREATE INDEX ix_sections_search_vector_fr 
        ON sections 
        USING gin(search_vector_fr);
    """)


def downgrade() -> None:
    """
    Remove full-text search indexes and columns.
    """
    # Drop French indexes
    op.execute("DROP INDEX IF EXISTS ix_sections_search_vector_fr;")
    op.execute("DROP INDEX IF EXISTS ix_regulations_search_vector_fr;")
    
    # Drop English indexes
    op.execute("DROP INDEX IF EXISTS ix_sections_search_vector;")
    op.execute("DROP INDEX IF EXISTS ix_regulations_search_vector;")
    
    # Drop French search_vector columns
    op.execute("ALTER TABLE sections DROP COLUMN IF EXISTS search_vector_fr;")
    op.execute("ALTER TABLE regulations DROP COLUMN IF EXISTS search_vector_fr;")
    
    # Drop English search_vector columns
    op.execute("ALTER TABLE sections DROP COLUMN IF EXISTS search_vector;")
    op.execute("ALTER TABLE regulations DROP COLUMN IF EXISTS search_vector;")
