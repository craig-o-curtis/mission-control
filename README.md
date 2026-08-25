# Mission Control — Fullstack Demo

A `uv` workspace containing two FastAPI backend projects behind a SvelteKit GUI.

## Workspace Structure

```
mission-control/
├── projects/
│   ├── missions_api/          # Missions API (in-memory)
│   ├── mission_control_app/   # Checklists API + Postgres
│   └── gui/                   # SvelteKit + TypeScript frontend (static SPA)
├── libs/
│   └── shared/                # Shared utilities (api_utils, etc.)
├── pyproject.toml             # Workspace root: shared deps, scripts, tool config
└── .github/workflows/         # CI pipeline
```

The `projects/gui` app is a separate Node/npm project (not part of the `uv` workspace). It builds to static files and is served as a SPA — see **Frontend GUI** below.

## Setup

```bash
uv sync
```

That's it — this installs every project, the shared library, and all dev tools (ruff, ty, pytest) in one shared virtual environment. There is no `requirements.txt`; dependencies live in each project's `pyproject.toml`.

## Running a project

```bash
uv run missions-api    # starts Missions API on http://127.0.0.1:8000 with auto-reload
uv run checklists-api  # starts Checklists API on http://127.0.0.1:8000 with auto-reload
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

Tests default to an in-memory SQLite database. To run the checklists test suite against a real database, set `TEST_DATABASE_URL`:

```bash
# Postgres
TEST_DATABASE_URL=postgresql+psycopg://postgres:<.env.TEST_POSTGRES_PASSWORD>@localhost:5432/mission_control_database uv run pytest projects/mission_control_app/tests/ -v

# MySQL
TEST_DATABASE_URL=mysql+pymysql://root:<.env.MYSQL_ROOT_PASSWORD>@localhost:3306/mission_control_database uv run pytest projects/mission_control_app/tests/ -v
```

To scope to a single project:

```bash
uv run pytest -v projects/missions_api/tests/
uv run ruff check projects/missions_api/src/
uv run ty check projects/missions_api/src/
```

## Adding a New Project

1. Create a new directory under `projects/` using the src-layout, matching `missions_api`:

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
uv add httpx --package missions-api
uv remove httpx --package missions-api

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

## Frontend GUI (`projects/gui`)

A static SPA built with SvelteKit + TypeScript + Tailwind, using `@sveltejs/adapter-static`
in SPA mode (no SSR, single `index.html` fallback that serves every client route). It is
published to GitHub Pages under the `mission-control` base path. This is a **separate
pnpm project** — it is not part of the `uv` workspace above (and uses pnpm, not npm, for
dependency management).

### Prerequisites

- **Node.js 24+** (enforced via the `engines.node` field and `engine-strict`)
- **pnpm**, managed by **corepack** — the project pins `pnpm@10.33.2` via the
  `packageManager` field, so run `corepack enable` once, then use `pnpm` as normal
  (corepack supplies the pinned version automatically).

### Install dependencies (if starting fresh)

```bash
cd projects/gui
pnpm install
```

### Run the dev server

```bash
cd projects/gui
pnpm run dev
```

Open the URL it prints. By default the app is served at the **site root**, so:

```
http://localhost:5173/
```

The GitHub Pages deploy (Phase 6) builds with `BASE_PATH=/mission-control` so the
static site is published under that subpath. To preview that subpath locally, set it:

```bash
BASE_PATH=/mission-control pnpm run dev   # then open http://localhost:5173/mission-control/
```

### Build the static site

```bash
cd projects/gui
pnpm run build                   # outputs static files to projects/gui/build/
```

`BASE_PATH` controls the URL prefix baked into asset links. It defaults to the **root**
for local use; the GitHub Pages build sets `BASE_PATH=/mission-control`. For a local
build served under that subpath, use `BASE_PATH=/mission-control`.

### Serve the built site locally

The `build/` folder is fully static, so any static file server works. Pick one:

```bash
# Option A: Node (pnpm dlx serve) — works with the default /mission-control base
cd projects/gui/build && pnpm dlx serve

# Option B: Python — build with BASE_PATH='' first, then serve at root
BASE_PATH='' pnpm run build
cd projects/gui/build && python3 -m http.server 8080   # open http://localhost:8080/
```

(With the default base path, a root server won't find the assets; either use `serve`, which
respects the path, or build with `BASE_PATH=''`.)

### Type-check

```bash
cd projects/gui
pnpm run check                  # svelte-check over the TypeScript sources
```

### Lint & format (Oxc)

The GUI uses [Oxc](https://oxc.rs) — `oxlint` for linting and `oxfmt` for formatting
(no ESLint/Prettier). These mirror the Python side's `ruff`/`ty` quality gates.

```bash
cd projects/gui
pnpm run lint          # oxlint over .ts/.js sources
pnpm run format        # oxfmt --write (reformats in place)
pnpm run format:check  # oxfmt --check (CI-friendly, non-zero on diffs)
```

Config: `.oxlintrc.json` and `.oxfmtrc.json` (both ignore `**/*.svelte`, `build`,
`.svelte-kit`, `node_modules`, `static`). `.svelte` files are formatted in the editor
via the `svelte.svelte-vscode` extension (format-on-save is enabled in `.vscode/settings.json`).

### Run from the repo root

A root `package.json` delegates the GUI scripts via `pnpm -C projects/gui`, so you can run
them from the repository root without `cd`-ing into `projects/gui`:

```bash
pnpm run dev            # projects/gui: vite dev
pnpm run build          # projects/gui: vite build  -> projects/gui/build/
pnpm run preview        # projects/gui: vite preview
pnpm run check          # projects/gui: svelte-check
pnpm run lint           # projects/gui: oxlint
pnpm run format         # projects/gui: oxfmt --write
pnpm run format:check   # projects/gui: oxfmt --check
pnpm run test           # projects/gui: vitest run
```

(These just forward to the matching script in `projects/gui`; the `cd projects/gui && pnpm run …`
forms above are equivalent.)

### Configuring the backend URLs

The GUI reads its backend base URLs from Vite `PUBLIC_` env vars, defined in
`projects/gui/src/lib/config.ts`:

```ts
export const MISSIONS_API = import.meta.env.PUBLIC_MISSIONS_API ?? "/api";
export const CHECKLISTS_API = import.meta.env.PUBLIC_CHECKLISTS_API ?? "/api";
```

**Local dev needs no URL string.** `vite.config.ts` proxies `/api/*` to the
locally-running FastAPI backend on port 8000 (override with `API_TARGET` if you run a
backend elsewhere). So `MISSIONS_API` defaults to `/api` and requests like `/api/missions`
are forwarded to `http://127.0.0.1:8000/missions`. Both backends default to port 8000,
so run one at a time locally. The proxy also avoids cross-origin/CORS friction in dev.

For production (GitHub Pages → Render), bake the absolute Render URLs in at build time:

```bash
PUBLIC_MISSIONS_API=https://missions-api.onrender.com \
PUBLIC_CHECKLISTS_API=https://checklists-api.onrender.com \
pnpm run build
```

Also set each backend's `CORS_ORIGINS` to include the GitHub Pages origin
(e.g. `https://<user>.github.io`) so the browser can call them cross-origin.

### Deploy to GitHub Pages

`.github/workflows/deploy-gui.yml` builds and publishes the GUI to the `gh-pages`
branch on every push to `main`. One-time setup:

1. Add repo **Secrets** `MISSIONS_API_URL` and `CHECKLISTS_API_URL` (the Render URLs).
2. **Settings → Pages → source: `gh-pages`** branch.

The workflow builds with `BASE_PATH=/mission-control` and bakes the above URLs
into the bundle, so the live site is `https://<user>.github.io/mission-control/`.

## Learning

- [docs/packages.md](docs/packages.md) — explanations of every package in this project (FastAPI, Pydantic, Uvicorn, Ruff, ty, etc.)
