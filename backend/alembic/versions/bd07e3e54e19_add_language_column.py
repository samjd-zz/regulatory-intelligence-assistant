"""add_language_column

Revision ID: bd07e3e54e19
Revises: e5863c09fece
Create Date: 2025-11-30 22:29:27.829630

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd07e3e54e19'
down_revision = 'e5863c09fece'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column to regulations table
    op.add_column('regulations', sa.Column('language', sa.String(length=10), nullable=False, server_default='en'))
    
    # Create index on language column for better query performance
    op.create_index(op.f('ix_regulations_language'), 'regulations', ['language'], unique=False)


def downgrade() -> None:
    # Drop index first
    op.drop_index(op.f('ix_regulations_language'), table_name='regulations')
    
    # Drop language column
    op.drop_column('regulations', 'language')
