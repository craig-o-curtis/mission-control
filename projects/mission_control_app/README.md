# Checklists App

## Architecture

Standard FastAPI project layout, split by responsibility so each file has one job:

| File              | Responsibility                                                                                            | Why it's separate                                                                                                      |
| ----------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `app.py`          | App factory — creates the `FastAPI()` instance, sets metadata, wires up routers                           | Single source of truth for the `app` object; both `main.py` and any ASGI server (uvicorn/gunicorn) import it from here |
| `main.py`         | CLI entry point (`checklists-api` script, see `pyproject.toml`); starts uvicorn with reload                    | Keeps `app.py` importable (e.g. in tests) without triggering DB init or starting a server                              |
| `config.py`       | Environment-driven settings (currently just `DATABASE_URL`, defaulting to local SQLite)                   | Centralizes config reads so nothing else touches `os.getenv` directly                                                  |
| `database.py`     | SQLAlchemy engine, session factory (`SessionLocal`), declarative `Base`, and `init_db()` (legacy, unused) | Table creation is now handled by Alembic migrations; `init_db()` kept for tests only                                   |
| `models.py`       | SQLAlchemy ORM models — the DB table shape                                                                | One class per table, isolated from the API contract                                                                    |
| `schemas.py`      | Pydantic models — the API's request/response shape (`ReadChecklistItemRequest`, `CreateChecklistItemRequest`)               | Lets the DB schema and public API contract evolve independently                                                        |
| `dependencies.py` | FastAPI `Depends` providers, e.g. `get_db` / `DbDep` for per-request DB sessions                          | Shared across routers via import instead of being redefined per file                                                   |
| `routers.py`      | `APIRouter` with endpoint handlers, grouped by resource (`/checklists`)                                        | Keeps route logic out of `app.py`; new resources get their own router module as the app grows                          |

This mirrors the common "layered" FastAPI convention: **routing** (routers) → **contracts** (schemas) → **persistence** (models/database) → **wiring** (dependencies/config), with `app.py` tying it together and `main.py` as the runnable entry point. It intentionally stops there — no service layer, no repository pattern, no DI container — because the app is small enough that those would add indirection without paying for itself yet. Reach for that structure later only if routers start doing non-trivial business logic beyond basic CRUD.

## Database

This app supports three backends, toggled entirely through `.env`:

| Backend        | Format                    | Storage                   | GUI                    | Best for                                        |
| -------------- | ------------------------- | ------------------------- | ---------------------- | ----------------------------------------------- |
| **SQLite**     | File (`data/checklistsapp.db`) | Local file                | None built-in          | Quick local development, zero setup             |
| **PostgreSQL** | Server (`localhost:5432`) | Docker volume `pgdata`    | pgAdmin4 (port `5050`) | Production-like features, JSON, complex queries |
| **MySQL**      | Server (`localhost:3306`) | Docker volume `mysqldata` | Adminer (port `8080`)  | Widely deployed, alternative to Postgres        |

Table creation is handled by Alembic migrations. After setting your `DATABASE_URL` in `.env`, run:

```bash
uv run alembic upgrade head
```

See [ALEMBIC.md](ALEMBIC.md) for all migration commands.

To switch databases, set or unset `DATABASE_URL` in `.env`:

```bash
# MySQL (requires running DB)
DATABASE_URL=mysql+pymysql://root:<.env.MYSQL_ROOT_PASSWORD>@localhost:3306/checklists_application_database

# PostgreSQL
DATABASE_URL=postgresql+psycopg://postgres:<.env.POSTGRES_PASSWORD>@localhost:5432/ChecklistsApplicationDatabase

# SQLite (default local file)
# DATABASE_URL=
```

## Run db

```bash
# Dive in to /data dir
cd projects/mission_control_app/data


# Run
sqlite3 checklistsapp.db

# Stop
.quit
```

## Tokens

Create with script:

```bash
openssl rand -hex 32
```

## SQL basics

### Create

```sql
CREATE TABLE checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    priority INTEGER,
    completed BOOLEAN DEFAULT FALSE
);
```

### Insert

```sql
INSERT INTO checklist_items (checklist_item, description, criticality, executed) VALUES ('Checklist Item 1', 'Description 1', 1, FALSE);

INSERT INTO checklist_items (checklist_item, description, criticality, executed) VALUES ('Checklist Item 2', 'Description 2', 5, FALSE);
```

### Select

```sql
SELECT * FROM checklist_items;

SELECT id, checklist_item, description, criticality, executed FROM checklist_items;

SELECT checklist_item, description, criticality, executed FROM checklist_items WHERE id = 1;

SELECT * FROM checklist_items WHERE executed = FALSE;
```

### Update

```sql
UPDATE checklist_items
SET checklist_item = 'Checklist Item 1 Updated'
WHERE id = 1;

UPDATE checklist_items
SET executed = TRUE
WHERE id = 1;
```

### Delete

```sql
DELETE FROM checklist_items
WHERE id = 1;
```

### Drop

```sql
DROP TABLE checklist_items;
```

## Testing

### Default (SQLite, no Docker required)

```bash
uv run pytest
```

Uses an in-memory SQLite database. Fast, zero setup.

### Against PostgreSQL

Requires a running Postgres instance (Docker or local):

```bash
docker compose -f docker-compose.postgres.yml up -d
TEST_DATABASE_URL=postgresql+psycopg://postgres:12345678@localhost:5432/ChecklistsApplicationDatabase uv run pytest
```

### Against MySQL

Requires a running MySQL instance (Docker or local):

```bash
docker compose -f docker-compose.mysql.yml up -d
TEST_DATABASE_URL=mysql+pymysql://root:12345678@localhost:3306/checklists_application_database uv run pytest
```

## Tips

### Output modes

```sql
-- Column
.mode column
select * from checklist_items;

-- Markdown
.mode markdown
select * from checklist_items;

-- Box
.mode box
select * from checklist_items;

-- Table
.mode table
select * from checklist_items;

-- Headers on
.headers on
select * from checklist_items;
```
