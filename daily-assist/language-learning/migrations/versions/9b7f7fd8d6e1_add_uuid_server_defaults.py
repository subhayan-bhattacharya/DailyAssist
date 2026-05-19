"""add_uuid_server_defaults

Revision ID: 9b7f7fd8d6e1
Revises: fc3d69d9eb72
Create Date: 2026-05-19 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b7f7fd8d6e1'
down_revision: Union[str, Sequence[str], None] = 'fc3d69d9eb72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_ID_TABLES = (
    "prompts",
    "words",
    "enrichment_jobs",
    "example_sentences",
    "flashcard_views",
    "daily_selections",
)


def upgrade() -> None:
    """Add database-side UUID defaults to match schema.sql."""
    for table_name in UUID_ID_TABLES:
        op.alter_column(
            table_name,
            "id",
            server_default=sa.text("gen_random_uuid()"),
            existing_type=sa.UUID(),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Remove database-side UUID defaults."""
    for table_name in UUID_ID_TABLES:
        op.alter_column(
            table_name,
            "id",
            server_default=None,
            existing_type=sa.UUID(),
            existing_nullable=False,
        )
