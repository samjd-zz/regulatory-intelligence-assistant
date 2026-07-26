"""apply_cascade_delete_to_citations

Revision ID: 1cca0f545f42
Revises: e5863c09fece
Create Date: 2025-12-01 00:11:11.915642

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cca0f545f42'
down_revision = 'e5863c09fece'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add CASCADE DELETE to citations foreign keys
    # Drop existing constraints
    op.drop_constraint('citations_section_id_fkey', 'citations', type_='foreignkey')
    op.drop_constraint('citations_cited_section_id_fkey', 'citations', type_='foreignkey')
    
    # Re-add with CASCADE DELETE
    op.create_foreign_key(
        'citations_section_id_fkey',
        'citations', 'sections',
        ['section_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'citations_cited_section_id_fkey',
        'citations', 'sections',
        ['cited_section_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Revert to original constraints without CASCADE
    op.drop_constraint('citations_section_id_fkey', 'citations', type_='foreignkey')
    op.drop_constraint('citations_cited_section_id_fkey', 'citations', type_='foreignkey')
    
    op.create_foreign_key(
        'citations_section_id_fkey',
        'citations', 'sections',
        ['section_id'], ['id']
    )
    op.create_foreign_key(
        'citations_cited_section_id_fkey',
        'citations', 'sections',
        ['cited_section_id'], ['id']
    )
