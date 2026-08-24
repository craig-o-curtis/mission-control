from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from tasks_api.config import DATABASE_URL


def _get_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(DATABASE_URL, connect_args=_get_connect_args(DATABASE_URL))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# This is the base class for all models
class Base(DeclarativeBase):
    pass


def _ensure_seeded_column() -> None:
    """Add the ``seeded`` column to ``tasks`` if a previous deployment created the
    table before this column existed.

    ``Base.metadata.create_all`` only creates missing tables; it does not alter
    existing ones. This idempotent step keeps the app self-healing on platforms
    without a deploy shell (e.g. Render), so no manual migration is required.
    """
    inspector = inspect(engine)
    if "tasks" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("tasks")}
    if "seeded" in existing:
        return
    with engine.begin() as conn:
        conn.execute(
            text("ALTER TABLE tasks ADD COLUMN seeded BOOLEAN NOT NULL DEFAULT FALSE")
        )


# This function
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_seeded_column()
