"""SQLAlchemy models for tasks API."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from tasks_api.database import Base

# This type/class is used to create the database tables.


class Task(Base):
    """Task model representing the tasks table (mission checklist items)."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    checklist_item: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(String(255), index=True)
    criticality: Mapped[int | None] = mapped_column(Integer, index=True)
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    mission_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
