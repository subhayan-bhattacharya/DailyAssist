"""add_flashcard_views_word_viewed_at_index

Revision ID: 6a36ec1ddf5a
Revises: 4d4f07c61f37
Create Date: 2026-06-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '6a36ec1ddf5a'
down_revision: Union[str, Sequence[str], None] = '4d4f07c61f37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        """
        CREATE INDEX idx_flashcard_views_word_viewed_at
        ON flashcard_views (word_id, viewed_at DESC)
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_flashcard_views_word_viewed_at', table_name='flashcard_views')
