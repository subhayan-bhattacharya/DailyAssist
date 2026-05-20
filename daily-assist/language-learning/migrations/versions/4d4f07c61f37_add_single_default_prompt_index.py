"""add_single_default_prompt_index

Revision ID: 4d4f07c61f37
Revises: 9b7f7fd8d6e1
Create Date: 2026-05-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4d4f07c61f37"
down_revision: Union[str, Sequence[str], None] = "9b7f7fd8d6e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ensure the prompts table can have only one active default prompt."""
    op.execute(
        """
        WITH ranked_defaults AS (
            SELECT
                id,
                row_number() OVER (ORDER BY created_at DESC NULLS LAST, id DESC) AS row_num
            FROM prompts
            WHERE is_default = TRUE
        )
        UPDATE prompts
        SET is_default = FALSE
        WHERE id IN (
            SELECT id
            FROM ranked_defaults
            WHERE row_num > 1
        )
        """
    )
    op.create_index(
        "uq_prompts_single_default",
        "prompts",
        ["is_default"],
        unique=True,
        postgresql_where=sa.text("is_default = TRUE"),
    )


def downgrade() -> None:
    """Remove the single-default prompt constraint."""
    op.drop_index("uq_prompts_single_default", table_name="prompts")
