"""
Create document models

Revision ID: 002_document_models
Revises: 001_initial_schema
Create Date: 2024-11-22 03:50:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create document-related tables."""
    
    # Drop existing types if they exist (from failed migrations)
    op.execute("DROP TYPE IF EXISTS documenttype CASCADE")
    op.execute("DROP TYPE IF EXISTS documentstatus CASCADE")
    
    # Create enum types
    op.execute("CREATE TYPE documenttype AS ENUM ('legislation', 'regulation', 'policy', 'guideline', 'directive')")
    op.execute("CREATE TYPE documentstatus AS ENUM ('draft', 'active', 'amended', 'repealed', 'archived')")
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False, index=True),
        sa.Column('document_type', postgresql.ENUM('legislation', 'regulation', 'policy', 'guideline', 'directive', name='documenttype'), nullable=False, index=True),
        sa.Column('jurisdiction', sa.String(100), nullable=False, index=True),
        sa.Column('authority', sa.String(200), nullable=False),
        sa.Column('document_number', sa.String(100), unique=True, index=True),
        sa.Column('full_text', sa.Text),
        sa.Column('original_filename', sa.String(255)),
        sa.Column('file_format', sa.String(50)),
        sa.Column('file_size', sa.Integer),
        sa.Column('file_hash', sa.String(64), unique=True),
        sa.Column('effective_date', sa.DateTime, index=True),
        sa.Column('publication_date', sa.DateTime),
        sa.Column('last_amended_date', sa.DateTime),
        sa.Column('upload_date', sa.DateTime, nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'amended', 'repealed', 'archived', name='documentstatus'), nullable=False, index=True),
        sa.Column('document_metadata', postgresql.JSONB, default={}),
        sa.Column('is_processed', sa.Boolean, default=False, index=True),
        sa.Column('processed_date', sa.DateTime),
        sa.Column('processing_errors', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create document_sections table
    op.create_table(
        'document_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('section_number', sa.String(50), nullable=False, index=True),
        sa.Column('section_title', sa.String(500)),
        sa.Column('section_type', sa.String(50)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('parent_section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_sections.id', ondelete='CASCADE')),
        sa.Column('order_index', sa.Integer, default=0),
        sa.Column('level', sa.Integer, default=0),
        sa.Column('document_metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create document_subsections table
    op.create_table(
        'document_subsections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_sections.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('subsection_number', sa.String(50), nullable=False, index=True),
        sa.Column('subsection_title', sa.String(500)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('parent_subsection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_subsections.id', ondelete='CASCADE')),
        sa.Column('order_index', sa.Integer, default=0),
        sa.Column('level', sa.Integer, default=0),
        sa.Column('document_metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create document_clauses table
    op.create_table(
        'document_clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('subsection_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_subsections.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('clause_identifier', sa.String(50), nullable=False, index=True),
        sa.Column('clause_title', sa.String(500)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('order_index', sa.Integer, default=0),
        sa.Column('document_metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create cross_references table
    op.create_table(
        'cross_references',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('source_section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_sections.id', ondelete='CASCADE'), index=True),
        sa.Column('source_location', sa.String(200)),
        sa.Column('target_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), index=True),
        sa.Column('target_section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('document_sections.id', ondelete='CASCADE'), index=True),
        sa.Column('target_location', sa.String(200)),
        sa.Column('reference_type', sa.String(50)),
        sa.Column('citation_text', sa.Text),
        sa.Column('context', sa.Text),
        sa.Column('document_metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create document_metadata table
    op.create_table(
        'document_metadata',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('key', sa.String(100), nullable=False, index=True),
        sa.Column('value', sa.Text),
        sa.Column('value_type', sa.String(50)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False)
    )
    
    # Create indexes for better query performance
    op.create_index('idx_documents_upload_date', 'documents', ['upload_date'])
    op.create_index('idx_sections_document_order', 'document_sections', ['document_id', 'order_index'])
    op.create_index('idx_subsections_section_order', 'document_subsections', ['section_id', 'order_index'])
    op.create_index('idx_clauses_subsection_order', 'document_clauses', ['subsection_id', 'order_index'])


def downgrade() -> None:
    """Drop document-related tables."""
    
    # Drop tables in reverse order
    op.drop_index('idx_clauses_subsection_order')
    op.drop_index('idx_subsections_section_order')
    op.drop_index('idx_sections_document_order')
    op.drop_index('idx_documents_upload_date')
    
    op.drop_table('document_metadata')
    op.drop_table('cross_references')
    op.drop_table('document_clauses')
    op.drop_table('document_subsections')
    op.drop_table('document_sections')
    op.drop_table('documents')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS documentstatus')
    op.execute('DROP TYPE IF EXISTS documenttype')
