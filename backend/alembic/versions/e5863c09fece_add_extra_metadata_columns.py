"""add_extra_metadata_columns

Revision ID: e5863c09fece
Revises: 002
Create Date: 2025-11-26 17:27:24.399770

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e5863c09fece'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add extra_metadata column to regulations table
    op.add_column('regulations', 
        sa.Column('extra_metadata', postgresql.JSONB, server_default='{}')
    )
    
    # Add extra_metadata column to sections table
    op.add_column('sections', 
        sa.Column('extra_metadata', postgresql.JSONB, server_default='{}')
    )
    
    # Add extra_metadata column to amendments table
    op.add_column('amendments', 
        sa.Column('extra_metadata', postgresql.JSONB, server_default='{}')
    )
    
    # Add extra_metadata column to workflow_sessions table
    op.add_column('workflow_sessions', 
        sa.Column('extra_metadata', postgresql.JSONB, server_default='{}')
    )
    
    # Add extra_metadata column to alerts table
    op.add_column('alerts', 
        sa.Column('extra_metadata', postgresql.JSONB, server_default='{}')
    )


def downgrade() -> None:
    # Remove extra_metadata columns in reverse order
    op.drop_column('alerts', 'extra_metadata')
    op.drop_column('workflow_sessions', 'extra_metadata')
    op.drop_column('amendments', 'extra_metadata')
    op.drop_column('sections', 'extra_metadata')
    op.drop_column('regulations', 'extra_metadata')
