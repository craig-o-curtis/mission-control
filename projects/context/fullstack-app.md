# Building a Fullstack Demo App

A 100%-free **Mission Control** demo that shows off two existing FastAPI backends
(`books_api` → missions, `tasks_api` → checklists) behind a SvelteKit GUI. The GUI
is a static site on **GitHub Pages**; the two Python backends run free on **Render**
(two Web Services; the tasks app uses Render's free **Postgres**).

## Constraints that drive the design

- **GitHub Pages serves static files only.** Python cannot run there, so the
  FastAPI backends MUST be hosted elsewhere (Render). The static frontend calls
  them cross-origin → **CORS is required** on both backends.
- **books_api** keeps data in memory (resets on restart) — fine for a demo.
- **tasks_api** needs a DB (Postgres on Render) and JWT auth.
- `requires-python >=3.14` — confirm Render offers 3.14 (Phase 5 has a fallback).

## Render dashboard — what each option is for

When you click **New +** on Render you'll see: Static Sites, Web Services,
Private Services, Background Workers, Postgres, Key Value, Cron Jobs. Here's what
we use for this project:

| Render option     | Use it? | Why                                                                         |
| ----------------- | ------- | --------------------------------------------------------------------------- |
| **Postgres**      | ✅ Yes  | Free database for `tasks_api`.                                              |
| **Web Service**   | ✅ Yes  | Hosts `books_api` and `tasks_api` (Python + uvicorn). We make two of these. |
| **Static Site**   | ❌ No   | We deploy the GUI to GitHub Pages instead (also free, already in-repo).     |
| Private Service   | ❌ No   | Nothing internal-only needed.                                               |
| Background Worker | ❌ No   | No offline/queue jobs.                                                      |
| Key Value         | ❌ No   | Not used.                                                                   |
| Cron Job          | ❌ No   | No scheduled tasks.                                                         |

## Architecture

```
Browser → GitHub Pages (static SvelteKit GUI)
            │ fetch (CORS)
            ├─► books_api  (Render Web Service, in-memory)  /books  → Missions dashboard
            └─► tasks_api  (Render Web Service + Postgres)  /auth/token, /tasks, /admin/tasks/reset  → Checklist ops
```

### Mission Control — field mapping

The two APIs keep their **endpoint URLs unchanged** (`/books`, `/tasks`, etc.) so Render
deployments need no reconfiguration. Only the Pydantic/SQLAlchemy field names and seed
data change to tell a mission-control story:

| Old field (books) | New field      | Meaning                                          |
| ----------------- | -------------- | ------------------------------------------------ |
| `title`           | `mission_name` | "Artemis Lunar Landing"                          |
| `author`          | `commander`    | Mission commander                                |
| `category`        | `mission_type` | Orbital, EVA, Deep Space, Surface                |
| `description`     | `description`  | Stays the same                                   |
| `rating` (1-5)    | `phase`        | planning → launch → active → complete → archived |
| _(new)_           | `priority`     | P0–P3 (1–4)                                      |
| _(new)_           | `launch_date`  | Optional date string                             |

| Old field (tasks) | New field        | Meaning                           |
| ----------------- | ---------------- | --------------------------------- |
| `title`           | `checklist_item` | "Verify oxygen levels"            |
| `description`     | `description`    | Stays the same                    |
| `priority` (1-5)  | `criticality`    | Critical/High/Medium/Low (1–4)    |
| `completed`       | `executed`       | Same boolean, different label     |
| _(new)_           | `mission_id`     | Groups checklist items by mission |
| _(new)_           | `notes`          | Execution notes                   |

> **Key constraint:** Endpoint URLs are identical. Pydantic field names change but the
> URL paths don't — so Render config is untouched.

---

## Phase 0 — Render walkthrough (do this first)

Goal: stand up the two backend services and the database on Render so the rest of
the build has live URLs to point the GUI at. Follow these steps in order.

### Step 0.1 — Connect GitHub to Render

1. Log into [dashboard.render.com](https://dashboard.render.com).
2. Go to **Account Settings → Connected Accounts** and connect your GitHub account.
   (Render needs this to read the `fastapi-endpoints` repo and auto-deploy on push.)

### Step 0.2 — Create the Postgres database

1. Click **New + → Postgres**.
2. **Name:** `tasks-db` (this is just Render's service name — anything memorable).
3. **Database** (the actual DB name inside Postgres): the field rejects the regex
   `/(^[a-z_][a-z0-9_]*$)|(^$)/`, so it must be **lowercase letters/digits/underscores,
   starting with a letter or underscore**. Use `tasks_application_database`
   (NOT `TasksApplicationDatabase` — uppercase fails). This name appears only inside
   the connection URL; our code never hardcodes it, so it needs no code change.
4. **User:** leave the Render default — Render auto-creates a DB user and bakes it
   into the connection URL. You don't set this yourself.
5. **Postgres Version:** pick a current stable release (e.g. **18**; 15 is also fine).
   Our stack (SQLAlchemy + psycopg3) supports either.
6. **Instance Type:** ** Free**.
7. **Storage Autoscaling:** **No** — it's a paid feature and the Free tier already
   includes a fixed ~1 GB. Choose No.
8. **Region:** pick one close to you (e.g. `Oregon (US-West)`).
9. Click **Create Database**.
10. Once it's provisioned, Render gives you an **Internal Database URL** of the form
    `postgres://user:pass@host:5432/tasks_application_database`. We attach it to the
    tasks service in Step 0.4 (Render injects it as `DATABASE_URL`). Note: the code
    in `config.py` now rewrites `postgres://` → `postgresql+psycopg://` so SQLAlchemy
    uses the installed psycopg3 driver — no other change is needed for Render.

### Step 0.3 — Create the books_api Web Service

1. Click **New + → Web Service**. The first screen prompts for a Git provider —
   this is normal even for a monorepo. Click **GitHub** (under "Connect Git provider")
   and authorize Render if asked. (If GitHub is already connected, you'll go straight
   to the repo list.) Then select the **`fastapi-endpoints`** repository.
2. **Name:** `books-api`.
3. **Root Directory:** this is how Render handles a monorepo (one repo, one service per
   subfolder). Render shows a "Select a directory" control (or a **Root Directory** text
   field) — choose/type `projects/books_api` (Render builds/runs from this subfolder).
4. **Language:** Python.
5. **Instance Type:** **Free**.
6. **Build Command:** Render may auto-fill a wrong default (e.g.
   `uv sync --frozen && uv cache prune --ci`, sometimes shown with a
   `projects/books_api/ $` prefix — that prefix is just the shell context, NOT part
   of the command). Overwrite it exactly with:
   ```
   pip install uv && uv sync
   ```
7. **Start Command:** Render may auto-fill `gunicorn your_application.wsgi` — this is
   wrong (our app is ASGI/FastAPI, not WSGI). Overwrite it exactly with:
   ```
   uv run uvicorn books_api.books:app --host 0.0.0.0 --port $PORT
   ```
   (Keep `$PORT` — Render supplies it.)
8. **Health Check Path:** `/` (the root returns JSON health metadata). Render may
   default this to `/healthz` — that route does NOT exist on either API, so the
   service would be marked unhealthy. Set it to `/` for both services.
9. Expand **Advanced → Environment Variables** and add:
   - `CORS_ORIGINS` = `https://<your-github-user>.github.io/fastapi-endpoints`
     (this is the **project page** for the `fastapi-endpoints` repo — NOT the bare
     `https://<your-github-user>.github.io`, which is your profile/user site and a
     different origin). No trailing slash. Comma-separated if you add more origins.
10. Click **Create Web Service**. Wait for the first deploy. When it's **Live**,
    copy the service URL — it looks like `https://books-api-xxxx.onrender.com`.
    Open it and you should see the JSON health check.

### Step 0.4 — Create the tasks_api Web Service

1. Click **New + → Web Service**. As in Step 0.3, the first screen asks for a Git
   provider — click **GitHub** (authorize if prompted) and select the **`fastapi-endpoints`**
   repository.
2. **Name:** `tasks-api`.
3. **Root Directory:** choose/type `projects/tasks_app` (same monorepo handling as Step 0.3).
4. **Language:** Python.
5. **Instance Type:** **Free**.
6. **Build Command:** overwrite any auto-filled default with:
   ```
   pip install uv && uv sync
   ```
7. **Start Command:** overwrite any auto-filled default (Render may suggest
   `gunicorn …` — wrong, we're ASGI) with:
   ```
   uv run alembic upgrade head && uv run uvicorn tasks_api.app:app --host 0.0.0.0 --port $PORT
   ```
   (This runs DB migrations on every boot, then starts the server. Keep `$PORT` — Render
   supplies it. Safe to repeat.)
8. **Health Check Path:** `/` (not Render's default `/healthz` — that route does
   not exist on this API).
9. **Environment Variables — `DATABASE_URL`:**
   The Postgres **Connect** panel on `tasks-db` only displays the URLs (there is no
   "connect to a service" picker). So copy the **Internal Database URL** from that panel
   and paste it as an env var on this service:
   - In the **Render dashboard**, open the **`tasks-api`** service page (created in steps 1–8
     above). Its left sidebar has an **Environment** item → click it → **Environment Variables**
     → **Add Environment Variable**. Name: `DATABASE_URL`; Value: the **Internal Database URL**
     shown on the `tasks-db` Connect panel (click its copy button — it's the
     `postgresql://tasks_application_database_user:…@dpg-…/tasks_application_database` string).
     Use the Internal URL (private network) rather than External when both are shown.
   - Our `config.py` rewrites `postgresql://` → `postgresql+psycopg://`, so this URL works as-is.
   - Keep this value only in Render — never commit it. If you pasted the password anywhere
     public, rotate it in the DB's Users tab.
     - `CORS_ORIGINS` = `https://<your-github-user>.github.io/fastapi-endpoints`
       (the project page for the `fastapi-endpoints` repo — NOT the bare profile URL;
       no trailing slash).
   - `SECRET_KEY` = run `openssl rand -hex 32` locally and paste the output.
   - `ADMIN_USER` = e.g. `demo`
   - `ADMIN_PASSWORD` = a password you choose (this is the demo login).
   - `ADMIN_EMAIL` = `demo@example.com`
   - `ADMIN_FIRST_NAME` = `Demo`
   - `ADMIN_LAST_NAME` = `User`
10. Click **Create Web Service**. Once **Live**, copy the URL
    (`https://tasks-api-xxxx.onrender.com`).

### Step 0.5 — Seed the database (automatic on deploy)

The tasks app needs an admin user before login works. Render's **free tier has no
web shell** (the Shell tab is behind the paid Starter plan), so we seed automatically
instead of running `scripts/seed.py` by hand.

- `tasks_api` now calls `ensure_seed_data()` in its **lifespan** on every startup
  (`src/tasks_api/bootstrap.py`). It reads the `ADMIN_*` vars and creates the admin
  user **and** the 3 seeded demo tasks **only if they don't already exist**. This runs
  on each deploy, so the demo always has a login and an original task list — no Shell
  needed. The same `seeded` flag is what protects seeded tasks from deletion.
- `scripts/seed.py` is still available for **local** use (or if you later upgrade to a
  paid instance and want to run it from the Shell). To seed locally against the Render
  Postgres, run it with `DATABASE_URL` set to the External URL and the same `ADMIN_*` vars.

After `tasks-api` redeploys with this change, verify login works:

```
curl -X POST https://tasks-api-xxxx.onrender.com/auth/token \
  -d "username=<your-ADMIN_USER>&password=<your-ADMIN_PASSWORD>"
```

You should get back a JSON token. (Use the same `ADMIN_USER` / `ADMIN_PASSWORD` you
set in Step 0.4.)

### Step 0.6 — Record your URLs

Write these down; Phases 4 and 6 need them:

- `BOOKS_API_URL` = `https://books-api-xxxx.onrender.com`
- `TASKS_API_URL` = `https://tasks-api-xxxx.onrender.com`
- `GH_PAGES_URL` = `https://<your-github-user>.github.io/fastapi-endpoints/`

**Phase 0 done when:** both services show **Live**, their `/` health checks
respond, and `POST /auth/token` returns a token with the demo credentials.

> **Python 3.14 note:** if a build fails because Render doesn't offer Python 3.14,
> either relax `requires-python` to `>=3.12` in the two `pyproject.toml` files, or
> add a `Dockerfile` (`FROM python:3.14-slim`, `uv sync`, uvicorn start) and deploy
> that Web Service "from Dockerfile". (Full detail in Phase 5 fallback.)

---

## Phase 1 — Mission Control: Backend Schema Migration (NEW)

**Goal**: Rename/restructure fields on both APIs without changing endpoint URLs.
This is the only new work needed — everything else in the existing phases stays intact.

### Books API → Missions (`projects/books_api`)

- `models.py`: Rename fields in Pydantic models:
  - `title` → `mission_name` (Field with new description/examples)
  - `author` → `commander`
  - `category` → `mission_type`
  - `rating` → `phase` (now `str`, choices: planning/launch/active/complete/archived)
  - Add `priority: int` (1-4), `launch_date: str | None`
- `mock_data.py`: Replace "Title One" books with mission-themed data
  (e.g., "Artemis Lunar Landing", "Mars Rover Deployment")
- `books.py`: Update query/filter param names (`title`→`mission_name`, `author`→`commander`,
  `category`→`mission_type`, `rating`→`phase`)
- **Endpoint URLs unchanged**: `/books`, `/books/{id}`, `/books/types/{type}`, etc.

### Tasks API → Checklists (`projects/tasks_app`)

- `models/task.py` (SQLAlchemy): Rename columns:
  - `title` → `checklist_item`
  - `priority` → `criticality`
  - `completed` → `executed`
  - Add `mission_id: Mapped[int | None]` (FK to users.id for now — cross-API FK not
    possible with separate services, just a numeric grouping field)
  - Add `notes: Mapped[str | None]`
- **Alembic migration**: Generate migration for column renames + new columns
- `schemas/tasks.py`: Update Pydantic schemas to match new field names
- `routers/tasks.py`, `routers/admin.py`: Update references to renamed fields
- `seed_data.py`: Replace task data with mission checklist items
  (e.g., "Verify oxygen levels", "Calibrate navigation")
- **Endpoint URLs unchanged**: `/tasks`, `/admin/tasks`, `/admin/tasks/reset`

### Done when

- `uv run pytest projects/books_api projects/tasks_app` still passes
- `uv run ty check` clean
- Seed data tells a coherent mission-control story

### Status (completed 2026-08-24)

- **books_api** (`projects/books_api`): Pydantic fields renamed to `mission_name` /
  `commander` / `mission_type` / `phase` (+ `priority`, `launch_date`); query params
  renamed (`mission_name`, `commander`, `mission_type`, `phase`); `description` kept.
  Seed data is mission-themed (Artemis Lunar Landing, etc.). Endpoint URLs unchanged.
  Tests rewritten → **37 passed**.
- **tasks_api** (`projects/tasks_app`): SQLAlchemy columns renamed
  `title`→`checklist_item`, `priority`→`criticality`, `completed`→`executed` (+ new
  `mission_id`, `notes`) via Alembic migration `b1c2d3e4f5a6_rename_tasks_to_checklist`.
  Pydantic schemas, routers, `seed_data.py`, and tests updated → **84 passed**.
  Migration verified to apply cleanly on a fresh DB.
- **gui** (`projects/gui`): `api.ts` types + `/books`, `/tasks`, and home pages
  relabeled to **Mission Control** / **Checklist Ops**; phase badges + criticality
  labels; backend URLs now baked via `$env/dynamic/public` (see gotcha below).

---

## Phase 2 — CORS on both backends (existing, unchanged)

- Both apps read a single `CORS_ORIGINS` env var (comma-separated list of allowed
  origins, **no trailing slash**; the code strips a trailing slash if present so it's
  forgiving). Default to the gh-pages URL.
- `projects/books_api/src/books_api/books.py`: add `CORSMiddleware`, origins from
  `CORS_ORIGINS`.
- `projects/tasks_app/src/tasks_api/app.py`: add `CORSMiddleware`, origins from
  `CORS_ORIGINS`.
- **Done when:** a browser on `*.github.io` can `fetch` both APIs without a CORS error.

## Phase 3 — Reset endpoints (seeded items are deletable, existing, unchanged)

- books: snapshot seeded missions at import; **deleting is allowed** (no 403);
  add `POST /books/reset` that restores the snapshot.
- tasks: add `seeded` boolean column (Alembic migration); **deleting seeded checklists
  is allowed** in `routers/tasks.py` + `routers/admin.py`; add
  `POST /admin/tasks/reset` (admin only) that wipes checklists and re-inserts the
  seeded ones (define `SEEDED_TASKS` in a new `seed_data.py`).
- Rationale: the **Reset** button is enough to restore the original demo state, so
  we don't block deletes. The `seeded` flag is kept only so the UI can badge demo
  rows and so reset knows what to re-create.
- **Done when:** `/books/reset` and `/admin/tasks/reset` restore seeded data; any
  item (seeded or not) can be deleted.

## Phase 4 — Frontend scaffold (`projects/gui`, existing, unchanged)

- **Package manager: pnpm** (security — hashed lockfile, content-addressable store).
  Do NOT use npm here.
- `sv create --install pnpm` → SvelteKit + TypeScript; manually add
  `@sveltejs/adapter-static` + `@tailwindcss/vite` (the `sv add adapter-static`
  add-on name 404s in this CLI version, so configure manually).
- SPA mode: root `+layout.ts` `ssr=false` / `prerender=false`, adapter
  `fallback:'index.html'`. Tailwind v4 via `@tailwindcss/vite` + `src/app.css`.
- **Mission Control dark theme**: Update `src/app.css` with dark background (`#0a0e17`),
  accent colors (`#00d4ff` cyan, `#ff6b35` orange for alerts), card backgrounds (`#151b2b`).
- `svelte.config.js`: `paths.base` from `BASE_PATH` (default `''` for local dev at the
  site root; the Phase 6 GitHub Pages build sets `BASE_PATH=/fastapi-endpoints`).
- Quality gates: `oxlint` (lint) + `oxfmt` (format) via Oxc — **not** ESLint/Prettier.
  Scripts `lint`, `format`, `format:check`; configs `.oxlintrc.json` / `.oxfmtrc.json`
  (both ignore `**/*.svelte`, `build`, `.svelte-kit`). `.svelte` formatting is handled by
  the `svelte.svelte-vscode` VS Code extension (format-on-save, set in root `.vscode`).
- **Done when:** `pnpm run dev` serves the app (200 shell), `pnpm run build` emits static
  `build/` with an `index.html` fallback, and `pnpm run check` / `lint` / `format:check`
  are all clean.

## Phase 5 — Frontend routes + API client (existing, update field names)

- `src/lib/config.ts`: `BOOKS_API` / `TASKS_API` from Vite `PUBLIC_BOOKS_API` /
  `PUBLIC_TASKS_API`. **Local default is `/api`** (relative) — `vite.config.ts` proxies
  `/api/*` to the local FastAPI backend on :8000, so no hardcoded URL is needed in dev.
  Production build sets the absolute Render URLs via `PUBLIC_*` env.
- `src/lib/api.ts`: typed fetch helpers (`booksApi`, `tasksApi`): missions CRUD + reset;
  checklists login (OAuth2 password → Bearer) + CRUD + admin reset; shared `ApiError`.
  - Update `Book` interface → rename fields to `mission_name`, `commander`, `mission_type`,
    `phase`, `priority`, `launch_date`
  - Update `Task` interface → rename fields to `checklist_item`, `criticality`, `executed`,
    `mission_id`, `notes`
- Routes: `/` (two cards: "Mission Control" / "Checklist Ops"), `/books` (list + create/edit
  - delete + Reset, phase badges color-coded: planning=gray, launch=yellow, active=cyan,
    complete=green, archived=dimmed), `/tasks` (login → list + create/edit/delete + Reset,
    demo-creds note, "ORIGINAL" badge for seeded items). Token persisted in `localStorage`.
- **Seeded indicators:** both `GET /books` and `GET /tasks` return a `seeded`
  boolean on each item. The UI renders an **"ORIGINAL" badge** for `seeded: true`
  rows, but deletion stays **enabled** (the Reset button restores the original
  seed). No lock icon / disabled delete button.
- **Done when:** local GUI talks to local (or Render) backends end-to-end; seeded
  rows show an "ORIGINAL" badge and the Reset button restores them.

## Phase 6 — Render tuning / fallback (existing, unchanged)

- Services already created in Phase 0. If Python 3.14 is unavailable, apply the
  Dockerfile or `requires-python` relaxation noted in Step 0.6.
- Confirm both services stay on the **Free** plan; note they sleep after ~15 min
  idle (first request after sleep is slow — acceptable for a demo).

## Phase 7 — GitHub Pages deploy (existing, unchanged)

- `.github/workflows/deploy-gui.yml`: on push to `main`, checkout → setup pnpm
  (`pnpm/action-setup@v4`, version 10) + Node 24 + pnpm cache → `pnpm install
--frozen-lockfile` in `projects/gui` → build with `BASE_PATH=/fastapi-endpoints`
  **and** `PUBLIC_BOOKS_API` / `PUBLIC_TASKS_API` set from repo **Secrets**
  (`BOOKS_API_URL`, `TASKS_API_URL`) → publish `projects/gui/build` to the
  `gh-pages` branch via `peaceiris/actions-gh-pages@v4`.
- **Authored and verified** (YAML valid; local build with those env vars bakes the
  base path + backend URLs into the bundle). Remaining manual steps (cannot be done
  in-repo):
  1. Add repo **Secrets** `BOOKS_API_URL` and `TASKS_API_URL` = the Phase 0 Render URLs.
  2. Repo **Settings → Pages → source: gh-pages** branch.
  3. Push to `main` → workflow deploys.
- **Done when:** `https://<user>.github.io/fastapi-endpoints/` loads the GUI.

## Phase 8 — Validate

- Local: run both backends; `pnpm run dev` (in `projects/gui`) with envs → localhost; manual CRUD + reset.
- `uv run pytest` for both apps (no regressions from CORS/reset/seed changes).
- Deployed: open the gh-pages URL; confirm CORS in the browser Network tab, live
  CRUD, and reset against Render.
- **Done when:** the public URL demonstrates Mission Control dashboard working.

### Status (validated 2026-08-24)

- **Automated checks PASS (Mission Control migration complete):**
  - `uv run pytest projects/books_api projects/tasks_app` → **121 passed** (no
    regressions from the field rename / CORS / reset / seed changes).
  - `pnpm run check` (svelte-check) → **0 errors, 0 warnings**.
  - `pnpm run lint` (oxlint) and `pnpm run format:check` (oxfmt) → **clean**.
  - `pnpm run build` with `BASE_PATH=/fastapi-endpoints` +
    `PUBLIC_BOOKS_API`/`PUBLIC_TASKS_API` → static `build/` emitted with the
    `/fastapi-endpoints/_app/...` base path **and the Render backend URLs** baked in
    (via `$env/dynamic/public`).
- **Phase 1 (Mission Control rename) is DONE** — see its status block above.
- **Remaining (cannot be done in-repo — gated on Phase 6 manual deploy):**
  1. Finish Phase 6 manual steps (repo Secrets `BOOKS_API_URL`/`TASKS_API_URL`,
     Pages source = `gh-pages`, push to `main`).
  2. Open the gh-pages URL; confirm browser CORS, live CRUD, and reset against Render.
- **Local manual check still available:** run both backends + `pnpm run dev` with
  envs → localhost for interactive CRUD/reset.

**Phase 8 local validation done when** the four automated checks above are green
(✅). **Fully done when** the deployed public URL demonstrates Mission Control
dashboard and Checklist Ops working end-to-end.

## Out of scope (for now)

- Enforcing numeric caps (max 5 missions, max 2 users, checklist limits) — deferred;
  only CORS + reset + protect-seeded are built in this pass.
- Custom domain for GitHub Pages.
- Kanban board view (phase columns) — can be added later as a visual enhancement.
- Real cross-service relationships between missions and checklists (separate services = separate DBs).

## Deployment gotcha — uv workspace members

The repo root `pyproject.toml` uses an explicit `[tool.uv.workspace] members` list
(`projects/books_api`, `projects/tasks_app`, `libs/shared`), NOT a `projects/*` glob.
A glob broke `uv sync` on Render (and locally) because `projects/context` is a docs
folder with no `pyproject.toml`, so uv aborted with
"Workspace member projects/context missing a pyproject.toml". Keep the members list
explicit if new subfolders are added under `projects/`.

## Deployment gotcha — Postgres driver (psycopg2 vs psycopg3)

The project depends on **psycopg3** (`psycopg[binary]`), but Render's Internal
Database URL is `postgresql://…`, and SQLAlchemy defaults `postgresql://` to the
**psycopg2** dialect → `ModuleNotFoundError: No module named 'psycopg2'` at
`alembic upgrade head`. Fixes (either works):

- **No push:** set the `tasks-api` `DATABASE_URL` env var to `postgresql+psycopg://…`
  (insert `+psycopg` after `postgresql`; keep host/user/db). Uses psycopg3 directly.
- **With push:** `config.py` already rewrites `postgresql://` → `postgresql+psycopg://`
  (and `postgres://` → `postgresql+psycopg://`). Commit & push that change, then the
  plain Internal URL works. The rewrite only triggers on `postgresql://`, so a
  `+psycopg` URL passes through unchanged — the two approaches are compatible.

## Deployment gotcha — health-check pings on Free tier

Render polls the **Health Check Path** every few seconds to monitor the service. This
is free and not an error, but it keeps the Free-tier instance **awake** (never sleeps),
so it burns free hours 24/7 and fills the logs. If you don't need constant monitoring
(fine for a demo), clear the **Health Check Path** (leave empty) on both services — the
instance will then sleep after ~15 min idle. Trade-off: first request after a sleep is
slow (cold start), and Render won't auto-detect an unhealthy state.

## Deployment gotcha — SvelteKit `PUBLIC_*` env vars

In this SvelteKit (2.63) + Vite 8 setup, `import.meta.env.PUBLIC_*` is **not** inlined
into the client bundle (Vite's `envPrefix` defaults to `VITE_`, and SvelteKit no longer
overrides it for `PUBLIC_`). The GUI reads backend URLs via `$env/dynamic/public`
(`src/lib/config.ts`):

```ts
import { env } from "$env/dynamic/public";
export const BOOKS_API = env.PUBLIC_BOOKS_API || "/api";
export const TASKS_API = env.PUBLIC_TASKS_API || "/api";
```

This bakes `PUBLIC_BOOKS_API` / `PUBLIC_TASKS_API` into the static build when set at build
time (the `deploy-gui.yml` CI step sets them from repo Secrets) and falls back to the
`/api` dev proxy when unset. Do **not** switch back to `import.meta.env.PUBLIC_*` — the
live site would call `/api` (which does not exist on GitHub Pages) and fail.
