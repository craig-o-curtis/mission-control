import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, "src")

from checklists_api.config import DATABASE_URL
from checklists_api.database import Base

# When checklist_item.py and user.py are imported, their Table objects register
# themselves with Base.metadata via the declarative side effect.
# These imports are required for autogenerate to see the tables.
from checklists_api.models import checklist_item, user  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_connect_args() -> dict[str, object]:
    if DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def run_migrations_offline() -> None:
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connect_args = get_connect_args()
    config.set_main_option("sqlalchemy.url", DATABASE_URL)
    section = config.get_section(config.config_ini_section)
    if section is None:
        section = {}
    engine = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=DATABASE_URL.startswith("sqlite"),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
