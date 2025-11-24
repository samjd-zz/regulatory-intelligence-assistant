"""add document models

Revision ID: 002_document_models
Revises: 001_initial_schema
Create Date: 2025-11-24 16:18:00.000000

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
    # Create document_type enum
    document_type_enum = postgresql.ENUM(
        'LEGISLATION', 'REGULATION', 'POLICY', 'GUIDELINE', 
        'DIRECTIVE', 'ORDER', 'BYLAW', 'OTHER',
        name='documenttype',
        create_type=False
    )
    document_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create document_status enum
    document_status_enum = postgresql.ENUM(
        'DRAFT', 'ACTIVE', 'AMENDED', 'REPEALED', 'ARCHIVED',
        name='documentstatus',
        create_type=False
    )
    document_status_enum.create(op.get_bind(), checkfirst=True)
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('document_type', document_type_enum, nullable=False),
        sa.Column('document_number', sa.String(length=100), nullable=True),
        sa.Column('jurisdiction', sa.String(length=100), nullable=False),
        sa.Column('authority', sa.String(length=255), nullable=False),
        sa.Column('full_text', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('file_format', sa.String(length=20), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(length=64), nullable=True),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('upload_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', document_status_enum, nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_processed', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_documents_jurisdiction', 'documents', ['jurisdiction'], unique=False)
    op.create_index('idx_documents_type', 'documents', ['document_type'], unique=False)
    op.create_index('idx_documents_status', 'documents', ['status'], unique=False)
    op.create_index('idx_documents_processed', 'documents', ['is_processed'], unique=False)
    op.create_index('idx_documents_title_search', 'documents', ['title'], unique=False, postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'})
    op.create_index(op.f('ix_documents_file_hash'), 'documents', ['file_hash'], unique=True)
    op.create_index(op.f('ix_documents_title'), 'documents', ['title'], unique=False)
    
    # Create document_sections table
    op.create_table(
        'document_sections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('section_number', sa.String(length=100), nullable=True),
        sa.Column('section_title', sa.Text(), nullable=True),
        sa.Column('section_type', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_section_id'], ['document_sections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_sections_document', 'document_sections', ['document_id'], unique=False)
    op.create_index('idx_document_sections_number', 'document_sections', ['section_number'], unique=False)
    op.create_index('idx_document_sections_parent', 'document_sections', ['parent_section_id'], unique=False)
    op.create_index('idx_document_sections_order', 'document_sections', ['document_id', 'order_index'], unique=False)
    
    # Create document_subsections table
    op.create_table(
        'document_subsections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subsection_number', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['section_id'], ['document_sections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_subsections_section', 'document_subsections', ['section_id'], unique=False)
    op.create_index('idx_document_subsections_order', 'document_subsections', ['section_id', 'order_index'], unique=False)
    
    # Create document_clauses table
    op.create_table(
        'document_clauses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subsection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('clause_identifier', sa.String(length=100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('order_index', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['subsection_id'], ['document_subsections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_clauses_subsection', 'document_clauses', ['subsection_id'], unique=False)
    op.create_index('idx_document_clauses_order', 'document_clauses', ['subsection_id', 'order_index'], unique=False)
    
    # Create cross_references table
    op.create_table(
        'cross_references',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_location', sa.String(length=255), nullable=True),
        sa.Column('target_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_location', sa.String(length=255), nullable=True),
        sa.Column('reference_type', sa.String(length=50), nullable=True),
        sa.Column('citation_text', sa.Text(), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['source_document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_section_id'], ['document_sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_document_id'], ['documents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['target_section_id'], ['document_sections.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_cross_references_source_doc', 'cross_references', ['source_document_id'], unique=False)
    op.create_index('idx_cross_references_target_doc', 'cross_references', ['target_document_id'], unique=False)
    op.create_index('idx_cross_references_type', 'cross_references', ['reference_type'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('idx_cross_references_type', table_name='cross_references')
    op.drop_index('idx_cross_references_target_doc', table_name='cross_references')
    op.drop_index('idx_cross_references_source_doc', table_name='cross_references')
    op.drop_table('cross_references')
    
    op.drop_index('idx_document_clauses_order', table_name='document_clauses')
    op.drop_index('idx_document_clauses_subsection', table_name='document_clauses')
    op.drop_table('document_clauses')
    
    op.drop_index('idx_document_subsections_order', table_name='document_subsections')
    op.drop_index('idx_document_subsections_section', table_name='document_subsections')
    op.drop_table('document_subsections')
    
    op.drop_index('idx_document_sections_order', table_name='document_sections')
    op.drop_index('idx_document_sections_parent', table_name='document_sections')
    op.drop_index('idx_document_sections_number', table_name='document_sections')
    op.drop_index('idx_document_sections_document', table_name='document_sections')
    op.drop_table('document_sections')
    
    op.drop_index(op.f('ix_documents_title'), table_name='documents')
    op.drop_index(op.f('ix_documents_file_hash'), table_name='documents')
    op.drop_index('idx_documents_title_search', table_name='documents')
    op.drop_index('idx_documents_processed', table_name='documents')
    op.drop_index('idx_documents_status', table_name='documents')
    op.drop_index('idx_documents_type', table_name='documents')
    op.drop_index('idx_documents_jurisdiction', table_name='documents')
    op.drop_table('documents')
    
    # Drop enums
    sa.Enum(name='documentstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='documenttype').drop(op.get_bind(), checkfirst=True)
