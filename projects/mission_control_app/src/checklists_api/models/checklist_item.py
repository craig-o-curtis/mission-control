"""SQLAlchemy models for checklists API."""

from checklists_api.database import Base
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

# This type/class is used to create the database tables.


class ChecklistItem(Base):
    """ChecklistItem model representing the checklist_items table
    (mission checklist items)."""

    __tablename__ = "checklist_items"

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
