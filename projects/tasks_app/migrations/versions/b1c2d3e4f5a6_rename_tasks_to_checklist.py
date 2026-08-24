"""rename tasks columns to checklist-item fields

Renames the generic task columns to the Mission Control checklist vocabulary
and adds the new grouping/notes columns:
  title       -> checklist_item
  priority     -> criticality
  completed    -> executed
  + mission_id (int, nullable)
  + notes      (string, nullable)

Revision ID: b1c2d3e4f5a6
Revises: a7b3c9d1e2f4
Create Date: 2026-08-24 15:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | None = "a7b3c9d1e2f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.alter_column(
            "title",
            new_column_name="checklist_item",
            existing_type=sa.String(length=255),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "priority",
            new_column_name="criticality",
            existing_type=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "completed",
            new_column_name="executed",
            existing_type=sa.Boolean(),
            existing_nullable=True,
        )
        batch_op.add_column(sa.Column("mission_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.String(length=255), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("tasks") as batch_op:
        batch_op.drop_column("notes")
        batch_op.drop_column("mission_id")
        batch_op.alter_column(
            "executed",
            new_column_name="completed",
            existing_type=sa.Boolean(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "criticality",
            new_column_name="priority",
            existing_type=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "checklist_item",
            new_column_name="title",
            existing_type=sa.String(length=255),
            existing_nullable=True,
        )
