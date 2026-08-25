"""Dependencies for checklists API."""

from collections.abc import Generator
from typing import Annotated

from checklists_api.database import SessionLocal
from fastapi import Depends
from sqlalchemy.orm import Session


# Using Generator to ensure the session is closed after use
def get_db() -> Generator[Session]:
    """Yield a database session and ensure it's closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbDep = Annotated[Session, Depends(get_db)]
