# FastAPI Backend Projects

A `uv` workspace containing multiple FastAPI backend projects sharing a common library.

## Workspace Structure

```
fastapi-backend/
├── projects/
│   ├── books_api/     # Books management API
│   └── tasks_app/     # Tasks management API (WIP)
├── libs/
│   └── shared/        # Shared utilities (api_utils, etc.)
├── pyproject.toml     # Workspace root: shared deps, scripts, tool config
└── .github/workflows/ # CI pipeline
```

## Setup

```bash
uv sync
```

That's it — this installs every project, the shared library, and all dev tools (ruff, ty, pytest) in one shared virtual environment. There is no `requirements.txt`; dependencies live in each project's `pyproject.toml`.

## Running a project

```bash
uv run books-api   # starts Books API on http://127.0.0.1:8000 with auto-reload
uv run tasks-api   # starts Tasks API on http://127.0.0.1:8000 with auto-reload
```

Each project defines a console-script entry point ([project.scripts]), so `uv run <name>` works from anywhere in the repo — no need for `--package` or the full `uvicorn` invocation.

## Everyday commands

Dev tools (ruff, ty, pytest) are shared across the workspace, so most commands can run at the root without `--package`:

```bash
uv run pytest -v                       # test everything, verbose
uv run pytest                          # condensed version
uv run ruff check .                    # lint everything
uv run ruff format --check .           # format-check everything
uv run ty check projects/ libs/        # type-check everything
```

Tests default to an in-memory SQLite database. To run the tasks_app test suite against a real database, set `TEST_DATABASE_URL`:

```bash
# Postgres
TEST_DATABASE_URL=postgresql+psycopg://postgres:<.env.TEST_POSTGRES_PASSWORD>@localhost:5432/TasksApplicationDatabase uv run pytest projects/tasks_app/tests/ -v

# MySQL
TEST_DATABASE_URL=mysql+pymysql://root:<.env.MYSQL_ROOT_PASSWORD>@localhost:3306/tasks_application_database uv run pytest projects/tasks_app/tests/ -v
```

To scope to a single project:

```bash
uv run pytest -v projects/books_api/tests/
uv run ruff check projects/books_api/src/
uv run ty check projects/books_api/src/
```

## Adding a New Project

1. Create a new directory under `projects/` using the src-layout, matching `books_api`:

   ```text
   projects/new_api/
   ├── src/new_api/
   │   ├── __init__.py
   │   ├── main.py       # main() -> uvicorn.run("new_api.app:app", reload=True)
   │   └── app.py         # FastAPI() instance
   ├── tests/
   └── pyproject.toml
   ```

2. In its `pyproject.toml`:
   - `name = "new-api"` (kebab-case)
   - `dependencies = ["fastapi", "uvicorn", "shared"]`
   - `[project.scripts]` → `new-api = "new_api.main:main"`
   - `[tool.setuptools.packages.find] where = ["src"]`
   - No need to repeat `[tool.ruff]` / `[tool.pytest.ini_options]` — those are inherited from the workspace root.
3. It's automatically discovered as a workspace member (`projects/*` is already configured in the root `pyproject.toml`), but a bare `uv sync` only installs packages the root project actually depends on. Add it to the root `pyproject.toml`:
   - `dependencies = [..., "new-api"]`
   - `[tool.uv.sources]` → `new-api = { workspace = true }`
4. Run `uv sync` to install, then `uv run new-api` to start it.

## Managing packages

```bash
# Add/remove a dependency for one project
uv add httpx --package books-api
uv remove httpx --package books-api

# Add/remove a dev-only tool (shared across the whole workspace)
uv add --dev some-tool
uv remove --dev some-tool

uv sync
```

If you see errors about clashing virtual environments, unset `VIRTUAL_ENV` first:

```bash
unset VIRTUAL_ENV
uv sync
```

## Reference

- `pyproject.toml` — workspace root: members, shared dev tools, shared ruff/pytest config
- `projects/` — individual API projects (src-layout, each with its own `[project.scripts]` entry)
- `libs/shared/` — shared library code
- `.agents/skills/` — AI agent skills (quality-check, ape-pr, etc.)

## Learning

- [docs/packages.md](docs/packages.md) — explanations of every package in this project (FastAPI, Pydantic, Uvicorn, Ruff, ty, etc.)
