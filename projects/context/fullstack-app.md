# Building a Fullstack Demo App

A 100%-free demo that shows off two existing FastAPI backends (`books_api`,
`tasks_api`) behind a SvelteKit GUI. The GUI is a static site on **GitHub Pages**;
the two Python backends run free on **Render** (two Web Services; the tasks app
uses Render's free **Postgres**).

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
            ├─► books_api  (Render Web Service, in-memory)  /books, /books/reset
            └─► tasks_api  (Render Web Service + Postgres)  /auth/token, /tasks, /admin/tasks/reset
```

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

### Step 0.5 — Seed the database (one time)

The tasks app needs an admin user (and seeded tasks) before login works.

1. Easiest: open the **Shell** tab on the `tasks-api` service in Render and run:
   ```
   uv run python scripts/seed.py
   ```
   (It reads the `ADMIN_*` env vars you set and creates the admin + seeded tasks.)
2. Or run locally with the same env vars pointed at the Render Postgres URL:
   ```
   DATABASE_URL=<internal-postgres-url> ADMIN_USER=demo ADMIN_PASSWORD=... \
   ADMIN_EMAIL=demo@example.com ADMIN_FIRST_NAME=Demo ADMIN_LAST_NAME=User \
   uv run python scripts/seed.py
   ```
3. Verify login works:
   ```
   curl -X POST https://tasks-api-xxxx.onrender.com/auth/token \
     -d "username=demo&password=<your-admin-password>"
   ```
   You should get back a JSON token.

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

## Phase 1 — CORS on both backends

- Both apps read a single `CORS_ORIGINS` env var (comma-separated list of allowed
  origins, **no trailing slash**; the code strips a trailing slash if present so it's
  forgiving). Default to the gh-pages URL.
- `projects/books_api/src/books_api/books.py`: add `CORSMiddleware`, origins from
  `CORS_ORIGINS`.
- `projects/tasks_app/src/tasks_api/app.py`: add `CORSMiddleware`, origins from
  `CORS_ORIGINS`.
- **Done when:** a browser on `*.github.io` can `fetch` both APIs without a CORS error.

## Phase 2 — Reset endpoints + protect seeded items

- books: snapshot seeded books at import; block deleting seeded ids (403);
  add `POST /books/reset` that restores the snapshot.
- tasks: add `seeded` boolean column (Alembic migration); block deleting seeded
  tasks (403) in `routers/tasks.py` + `routers/admin.py`; add
  `POST /admin/tasks/reset` (admin only) that deletes non-seeded tasks and
  re-inserts seeded ones (define `SEEDED_TASKS` in a new `seed_data.py`).
- **Done when:** `/books/reset` and `/admin/tasks/reset` restore seeded data;
  deleting a seeded item returns 403.

## Phase 3 — Frontend scaffold (`projects/gui`)

- `sv create` → SvelteKit + TypeScript; add `adapter-static` (SPA mode:
  root `+layout.ts` `ssr=false`, adapter `fallback:'index.html'`); add Tailwind.
- `svelte.config.js`: `paths.base` from `BASE_PATH` (default `/fastapi-endpoints`).
- **Done when:** `npm run dev` serves the app and `npm run build` emits static `build/`.

## Phase 4 — Frontend routes + API client

- `src/lib/config.ts`: `PUBLIC_BOOKS_API`, `PUBLIC_TASKS_API` (Vite `PUBLIC_` env,
  set to the Phase 0 URLs).
- `src/lib/api.ts`: fetch helpers (books CRUD; tasks login/CRUD with Bearer).
- Routes: `/` (two cards), `/books` (list + create + Reset), `/tasks`
  (login → list + create/update/delete + Reset; show demo creds).
- **Done when:** local GUI talks to local (or Render) backends end-to-end.

## Phase 5 — Render tuning / fallback

- Services already created in Phase 0. If Python 3.14 is unavailable, apply the
  Dockerfile or `requires-python` relaxation noted in Step 0.6.
- Confirm both services stay on the **Free** plan; note they sleep after ~15 min
  idle (first request after sleep is slow — acceptable for a demo).

## Phase 6 — GitHub Pages deploy

- `.github/workflows/deploy-gui.yml`: on push to `main`, checkout → setup Node →
  `npm ci` in `projects/gui` → build with `PUBLIC_BOOKS_API` / `PUBLIC_TASKS_API`
  set to the Phase 0 Render URLs → publish `projects/gui/build` to `gh-pages`
  (e.g. `peaceiris/actions-gh-pages`).
- Repo **Settings → Pages → source: gh-pages** branch.
- **Done when:** `https://<user>.github.io/fastapi-endpoints/` loads the GUI.

## Phase 7 — Validate

- Local: run both backends; `npm run dev` with envs → localhost; manual CRUD + reset.
- `uv run pytest` for both apps (no regressions from CORS/reset/seed changes).
- Deployed: open the gh-pages URL; confirm CORS in the browser Network tab, live
  CRUD, and reset against Render.
- **Done when:** the public URL demonstrates both backends working.

## Out of scope (for now)

- Enforcing numeric caps (max 5 books, max 2 users, task limits) — deferred;
  only CORS + reset + protect-seeded are built in this pass.
- Custom domain for GitHub Pages.

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
