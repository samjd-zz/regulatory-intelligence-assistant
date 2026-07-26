"""merge heads

Revision ID: f8a9c3d2e1b4
Revises: 51bb217e6f66, a2171c414458
Create Date: 2025-12-12 12:42:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8a9c3d2e1b4'
down_revision = ('51bb217e6f66', 'a2171c414458')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration - no changes needed
    pass


def downgrade() -> None:
    # This is a merge migration - no changes needed
    pass
