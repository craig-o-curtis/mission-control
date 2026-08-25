# Alembic Commands

Schema migrations for the Checklist API. Alembic tracks database changes as versioned Python scripts and applies them in order.

## Quick Start

```bash
# From projects/mission_control_app/
uv run alembic upgrade head
```

## Command Reference

| Command                                           | What it does                                                  | When to use                                                                                                  |
| ------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `uv run alembic upgrade head`                     | Applies all pending migrations to reach the latest version    | **Fresh database** — first time setup, or after `downgrade`                                                  |
| `uv run alembic upgrade <revision>`               | Applies migrations up to a specific revision                  | Rolling forward to a known point                                                                             |
| `uv run alembic downgrade -1`                     | Reverts the last migration                                    | **Undo a bad migration** on a dev database                                                                   |
| `uv run alembic downgrade <revision>`             | Reverts back to a specific revision                           | Rolling back multiple steps                                                                                  |
| `uv run alembic stamp head`                       | Marks the database as up-to-date **without running any DDL**  | **Only** if the DB schema already matches the models exactly — otherwise migrations will be silently skipped |
| `uv run alembic current`                          | Shows the current revision the database is on                 | Check if a DB is migrated                                                                                    |
| `uv run alembic heads`                            | Shows the latest available revision in `migrations/versions/` | See what `upgrade head` would apply                                                                          |
| `uv run alembic history`                          | Lists all migrations in order                                 | Review the changelog                                                                                         |
| `uv run alembic revision --autogenerate -m "msg"` | Creates a new migration by comparing models against the live DB      | **After changing a model** — always review the generated file before committing                              |
| `uv run alembic check`                            | Detects if models and DB schema have drifted                  | Run in CI to catch unapplied changes                                                                         |
| `uv run alembic init <dir>`                       | Initializes a new migrations environment                      | Not needed here — already set up                                                                             |

## Typical Workflow

### 1. Change a model

Edit a file in `src/checklists_api/models/` (e.g. add a column to `ChecklistItem`).

### 2. Generate a migration

```bash
uv run alembic revision --autogenerate -m "add criticality to checklist_items"
```

The `--autogenerate` flag tells Alembic to compare your models (`Base.metadata`) against the live database and automatically generate the `op.*` calls (`op.add_column()`, `op.create_table()`, etc.). Without it, you'd get an empty migration with blank `upgrade()`/`downgrade()` functions and have to write every `op.*` call by hand.

**When to use `--autogenerate`:** almost always. It handles the boilerplate for simple schema changes (add/drop columns, tables, indexes).

**When to omit `--autogenerate`:** when the change can't be expressed as a simple diff — e.g. data migrations, renaming columns, or complex constraint changes. In those cases, use `uv run alembic revision -m "msg"` and write the `op.*` calls manually.

**Always review the generated file.** Autogenerate is good but not perfect — it may miss `server_default` values, `nullable` changes, or index names. Check the `upgrade()` and `downgrade()` functions before committing.

### 3. Review the generated file

Check `migrations/versions/<hash>_add_criticality_to_checklist_items.py` — autogenerate is good but not perfect. Verify `op.*` calls, especially for `server_default`, `nullable`, and foreign keys.

### 4. Apply it

```bash
# Run this after EVERY model change — works for fresh DBs and existing DBs
uv run alembic upgrade head
```

On an existing database, Alembic automatically skips `CREATE TABLE` for tables that already exist and only runs the pending `ALTER TABLE` / `DROP` ops. **This is the normal path** — not just for fresh databases.

> **Do NOT use `stamp head` as your first instinct.** See the section below for when it's actually appropriate.

### 5. Rollback if needed

```bash
uv run alembic downgrade -1
```

## Important Notes

- **SQLite** uses batch mode (`render_as_batch=True`) because SQLite's `ALTER TABLE` is limited. MySQL and Postgres support real `ALTER` and don't need it.
- **Tests** do **not** run migrations — they use `Base.metadata.create_all()` directly on temporary SQLite files for speed.
- The app no longer calls `init_db()` on startup. If migrations are missing, the app will fail at runtime instead of silently creating tables.

## Choosing Between `upgrade head` and `stamp head`

| Situation                                 | Command        | Why                                                                                      |
| ----------------------------------------- | -------------- | ---------------------------------------------------------------------------------------- |
| Fresh DB (no tables)                      | `upgrade head` | Runs all migrations, creates schema                                                      |
| Existing DB, schema matches models        | `upgrade head` | Safest choice; skips CREATE TABLE for existing tables                                    |
| Existing DB, schema does NOT match models | `upgrade head` | Actually runs `ALTER TABLE` to fix the schema                                            |
| Not sure if schema matches                | `upgrade head` | If tables already exist, Alembic skips `CREATE` and runs only pending `ALTER`/`DROP` ops |

**Warning: `stamp head` silently skips migrations.** It only writes a row to the `alembic_version` table. If the DB schema is missing columns, indexes, or constraints that the migration would create, those will never be added — and the app will fail at runtime with "Unknown column" errors. Only use `stamp head` when you've manually verified the schema matches the models.

**How to check:** run `uv run alembic heads` (shows available migrations) and `uv run alembic current` (shows what the DB thinks is applied). If `current` is behind `heads`, run `upgrade head`.
