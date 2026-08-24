"""add seeded flag to tasks

Revision ID: a7b3c9d1e2f4
Revises: dd56d5669ec7
Create Date: 2026-08-24 13:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7b3c9d1e2f4"
down_revision: str | None = "dd56d5669ec7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column("seeded", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("tasks", "seeded")
