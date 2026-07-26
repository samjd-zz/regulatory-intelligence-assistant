"""increase_section_number_length

Revision ID: 51bb217e6f66
Revises: 1cca0f545f42
Create Date: 2025-12-01 18:35:05.443588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51bb217e6f66'
down_revision = '1cca0f545f42'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Increase section_number column length from 50 to 255 characters.
    
    This fixes an issue where some Canadian legal documents use full titles
    as section identifiers when Label elements are missing, causing overflow
    errors during ingestion.
    """
    # Increase section_number length
    op.alter_column(
        'sections',
        'section_number',
        existing_type=sa.String(50),
        type_=sa.String(255),
        existing_nullable=False
    )


def downgrade() -> None:
    """Revert section_number column length back to 50 characters."""
    # Note: This may fail if there are existing records with section_number > 50 chars
    op.alter_column(
        'sections',
        'section_number',
        existing_type=sa.String(255),
        type_=sa.String(50),
        existing_nullable=False
    )
