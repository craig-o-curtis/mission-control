"""SQLAlchemy models for tasks API."""

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from tasks_api.database import Base

# This type/class is used to create the database tables.


class Task(Base):
    """Task model representing the tasks table."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(String(255), index=True)
    priority: Mapped[int | None] = mapped_column(Integer, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    seeded: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
