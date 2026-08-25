# Building a Fullstack Demo App

A 100%-free **Mission Control** demo that shows off two existing FastAPI backends
(`missions_api` → missions, `mission_control_app` → checklists) behind a SvelteKit GUI. The GUI
is a static site on **GitHub Pages**; the two Python backends run free on **Render**
(two Web Services; the checklists app uses Render's free **Postgres**).

## Constraints that drive the design

- **GitHub Pages serves static files only.** Python cannot run there, so the
  FastAPI backends MUST be hosted elsewhere (Render). The static frontend calls
  them cross-origin → **CORS is required** on both backends.
- **missions_api** keeps data in memory (resets on restart) — fine for a demo.
- **checklists_api** needs a DB (Postgres on Render) and JWT auth.
- `requires-python >=3.14` — confirm Render offers 3.14 (Phase 5 has a fallback).

## Render dashboard — what each option is for

When you click **New +** on Render you'll see: Static Sites, Web Services,
Private Services, Background Workers, Postgres, Key Value, Cron Jobs. Here's what
we use for this project:

| Render option     | Use it? | Why                                                                         |
| ----------------- | ------- | --------------------------------------------------------------------------- |
| **Postgres**      | ✅ Yes  | Free database for `checklists_api`.                                              |
| **Web Service**   | ✅ Yes  | Hosts `missions_api` and `checklists_api` (Python + uvicorn). We make two of these. |
| **Static Site**   | ❌ No   | We deploy the GUI to GitHub Pages instead (also free, already in-repo).     |
| Private Service   | ❌ No   | Nothing internal-only needed.                                               |
| Background Worker | ❌ No   | No offline/queue jobs.                                                      |
| Key Value         | ❌ No   | Not used.                                                                   |
| Cron Job          | ❌ No   | No scheduled tasks.                                                         |

## Architecture

```
Browser → GitHub Pages (static SvelteKit GUI)
            │ fetch (CORS)
            ├─► missions_api  (Render Web Service, in-memory)  /missions  → Missions dashboard
            └─► checklists_api  (Render Web Service + Postgres)  /auth/token, /checklists, /admin/checklists/reset  → Checklist ops
```

### Mission Control — field mapping

The two APIs use **renamed endpoint URLs** (`/missions`, `/checklists`, etc.) so Render
deployments need reconfiguration. The Pydantic/SQLAlchemy field names and seed
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

> **Key constraint:** Endpoint URLs are renamed. Pydantic field names change and the
> URL paths do too — so Render config needs updating.

---

## Phase 0 — Render walkthrough (do this first)

Goal: stand up the two backend services and the database on Render so the rest of
the build has live URLs to point the GUI at. Follow these steps in order.

### Step 0.1 — Connect GitHub to Render

1. Log into [dashboard.render.com](https://dashboard.render.com).
2. Go to **Account Settings → Connected Accounts** and connect your GitHub account.
   (Render needs this to read the `mission-control` repo and auto-deploy on push.)

### Step 0.2 — Create the Postgres database

1. Click **New + → Postgres**.
2. **Name:** `mission-control-db` (this is just Render's service name — anything memorable).
3. **Database** (the actual DB name inside Postgres): the field rejects the regex
   `/(^[a-z_][a-z0-9_]*$)|(^$)/`, so it must be **lowercase letters/digits/underscores,
   starting with a letter or underscore**. Use `mission_control_application_database`
   (NOT `MissionControlDatabase` — uppercase fails). This name appears only inside
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
    `postgres://user:pass@host:5432/mission_control_application_database`. We attach it to the
    tasks service in Step 0.4 (Render injects it as `DATABASE_URL`). Note: the code
    in `config.py` now rewrites `postgres://` → `postgresql+psycopg://` so SQLAlchemy
    uses the installed psycopg3 driver — no other change is needed for Render.

### Step 0.3 — Create the missions_api Web Service

1. Click **New + → Web Service**. The first screen prompts for a Git provider —
   this is normal even for a monorepo. Click **GitHub** (under "Connect Git provider")
   and authorize Render if asked. (If GitHub is already connected, you'll go straight
   to the repo list.) Then select the **`mission-control`** repository.
2. **Name:** `missions-api`.
3. **Root Directory:** this is how Render handles a monorepo (one repo, one service per
   subfolder). Render shows a "Select a directory" control (or a **Root Directory** text
   field) — choose/type `projects/missions_api` (Render builds/runs from this subfolder).
4. **Language:** Python.
5. **Instance Type:** **Free**.
6. **Build Command:** Render may auto-fill a wrong default (e.g.
   `uv sync --frozen && uv cache prune --ci`, sometimes shown with a
   `projects/missions_api/ $` prefix — that prefix is just the shell context, NOT part
   of the command). Overwrite it exactly with:
   ```
   pip install uv && uv sync
   ```
7. **Start Command:** Render may auto-fill `gunicorn your_application.wsgi` — this is
   wrong (our app is ASGI/FastAPI, not WSGI). Overwrite it exactly with:
   ```
    uv run uvicorn missions_api.missions:app --host 0.0.0.0 --port $PORT
   ```
   (Keep `$PORT` — Render supplies it.)
8. **Health Check Path:** `/` (the root returns JSON health metadata). Render may
   default this to `/healthz` — that route does NOT exist on either API, so the
   service would be marked unhealthy. Set it to `/` for both services.
9. Expand **Advanced → Environment Variables** and add:
   - `CORS_ORIGINS` = `https://<your-github-user>.github.io/mission-control`
     (this is the **project page** for the `mission-control` repo — NOT the bare
     `https://<your-github-user>.github.io`, which is your profile/user site and a
     different origin). No trailing slash. Comma-separated if you add more origins.
10. Click **Create Web Service**. Wait for the first deploy. When it's **Live**,
    copy the service URL — it looks like `https://missions-api-xxxx.onrender.com`.
    Open it and you should see the JSON health check.

### Step 0.4 — Create the checklists_api Web Service

1. Click **New + → Web Service**. As in Step 0.3, the first screen asks for a Git
   provider — click **GitHub** (authorize if prompted) and select the **`mission-control`**
   repository.
2. **Name:** `checklists-api`.
3. **Root Directory:** choose/type `projects/mission_control_app` (same monorepo handling as Step 0.3).
4. **Language:** Python.
5. **Instance Type:** **Free**.
6. **Build Command:** overwrite any auto-filled default with:
   ```
   pip install uv && uv sync
   ```
7. **Start Command:** overwrite any auto-filled default (Render may suggest
   `gunicorn …` — wrong, we're ASGI) with:
   ```
   uv run alembic upgrade head && uv run uvicorn checklists_api.app:app --host 0.0.0.0 --port $PORT
   ```
   (This runs DB migrations on every boot, then starts the server. Keep `$PORT` — Render
   supplies it. Safe to repeat.)
8. **Health Check Path:** `/` (not Render's default `/healthz` — that route does
   not exist on this API).
9. **Environment Variables — `DATABASE_URL`:**
   The Postgres **Connect** panel on `mission-control-db` only displays the URLs (there is no
   "connect to a service" picker). So copy the **Internal Database URL** from that panel
   and paste it as an env var on this service:
   - In the **Render dashboard**, open the **`checklists-api`** service page (created in steps 1–8
     above). Its left sidebar has an **Environment** item → click it → **Environment Variables**
     → **Add Environment Variable**. Name: `DATABASE_URL`; Value: the **Internal Database URL**
     shown on the `mission-control-db` Connect panel (click its copy button — it's the
     `postgresql://mission_control_application_database_user:…@dpg-…/mission_control_application_database` string).
     Use the Internal URL (private network) rather than External when both are shown.
   - Our `config.py` rewrites `postgresql://` → `postgresql+psycopg://`, so this URL works as-is.
   - Keep this value only in Render — never commit it. If you pasted the password anywhere
     public, rotate it in the DB's Users tab.
     - `CORS_ORIGINS` = `https://<your-github-user>.github.io/mission-control`
       (the project page for the `mission-control` repo — NOT the bare profile URL;
       no trailing slash).
   - `SECRET_KEY` = run `openssl rand -hex 32` locally and paste the output.
   - `ADMIN_USER` = e.g. `demo`
   - `ADMIN_PASSWORD` = a password you choose (this is the demo login).
   - `ADMIN_EMAIL` = `demo@example.com`
   - `ADMIN_FIRST_NAME` = `Demo`
   - `ADMIN_LAST_NAME` = `User`
10. Click **Create Web Service**. Once **Live**, copy the URL
    (`https://checklists-api-xxxx.onrender.com`).

### Step 0.5 — Seed the database (automatic on deploy)

The checklists app needs an admin user before login works. Render's **free tier has no
web shell** (the Shell tab is behind the paid Starter plan), so we seed automatically
instead of running `scripts/seed.py` by hand.

- `checklists_api` now calls `ensure_seed_data()` in its **lifespan** on every startup
  (`src/checklists_api/bootstrap.py`). It reads the `ADMIN_*` vars and creates the admin
  user **and** the 3 seeded demo checklist items **only if they don't already exist**. This runs
  on each deploy, so the demo always has a login and an original checklist item list — no Shell
  needed. The same `seeded` flag is what protects seeded checklist items from deletion.
- `scripts/seed.py` is still available for **local** use (or if you later upgrade to a
  paid instance and want to run it from the Shell). To seed locally against the Render
  Postgres, run it with `DATABASE_URL` set to the External URL and the same `ADMIN_*` vars.

After `checklists-api` redeploys with this change, verify login works:

```
curl -X POST https://checklists-api-xxxx.onrender.com/auth/token \
  -d "username=<your-ADMIN_USER>&password=<your-ADMIN_PASSWORD>"
```

You should get back a JSON token. (Use the same `ADMIN_USER` / `ADMIN_PASSWORD` you
set in Step 0.4.)

### Step 0.6 — Record your URLs

Write these down; Phases 4 and 6 need them:

- `MISSIONS_API_URL` = `https://missions-api-xxxx.onrender.com`
- `CHECKLISTS_API_URL` = `https://checklists-api-xxxx.onrender.com`
- `GH_PAGES_URL` = `https://<your-github-user>.github.io/mission-control/`

**Phase 0 done when:** both services show **Live**, their `/` health checks
respond, and `POST /auth/token` returns a token with the demo credentials.

> **Python 3.14 note:** if a build fails because Render doesn't offer Python 3.14,
> either relax `requires-python` to `>=3.12` in the two `pyproject.toml` files, or
> add a `Dockerfile` (`FROM python:3.14-slim`, `uv sync`, uvicorn start) and deploy
> that Web Service "from Dockerfile". (Full detail in Phase 5 fallback.)

---

## Phase 1 — Mission Control: Backend Schema Migration (COMPLETED 2026-08-24)

- **missions_api** (`projects/missions_api`): Pydantic fields renamed to `mission_name` /
  `commander` / `mission_type` / `phase` (+ `priority`, `launch_date`); query params
  renamed (`mission_name`, `commander`, `mission_type`, `phase`); `description` kept.
  Seed data is mission-themed (Artemis Lunar Landing, etc.). Endpoint URLs at
  `/missions/*`. Tests rewritten → **37 passed**.
- **checklists_api** (`projects/mission_control_app`): SQLAlchemy columns renamed
  `title`→`checklist_item`, `priority`→`criticality`, `completed`→`executed` (+ new
  `mission_id`, `notes`) via Alembic migration. Pydantic schemas, routers,
  `seed_checklists.py`, and tests updated → **84 passed**.
  Migration verified to apply cleanly on a fresh DB.
- **gui** (`projects/gui`): `api.ts` types + `/missions`, `/checklists`, and home pages
  relabeled to **Mission Control** / **Checklist Ops**; phase badges + criticality
  labels; backend URLs baked via `$env/dynamic/public`.

---

## Phase 2 — CORS on both backends (existing, unchanged)

- Both apps read a single `CORS_ORIGINS` env var (comma-separated list of allowed
  origins, **no trailing slash**; the code strips a trailing slash if present so it's
  forgiving). Default to the gh-pages URL.
- `projects/missions_api/src/missions_api/missions.py`: add `CORSMiddleware`, origins from
  `CORS_ORIGINS`.
- `projects/mission_control_app/src/checklists_api/app.py`: add `CORSMiddleware`, origins from
  `CORS_ORIGINS`.
- **Done when:** a browser on `*.github.io` can `fetch` both APIs without a CORS error.

## Phase 3 — Reset endpoints (seeded items are deletable, existing, unchanged)

- missions: snapshot seeded missions at import; **deleting is allowed** (no 403);
  add `POST /missions/reset` that restores the snapshot.
- checklists: add `seeded` boolean column (Alembic migration); **deleting seeded checklists
  is allowed** in `routers/checklists.py` + `routers/admin.py`; add
  `POST /admin/checklists/reset` (admin only) that wipes checklists and re-inserts the
  seeded ones (define `SEEDED_CHECKLISTS` in a new `seed_checklists.py`).
- Rationale: the **Reset** button is enough to restore the original demo state, so
  we don't block deletes. The `seeded` flag is kept only so the UI can badge demo
  rows and so reset knows what to re-create.
- **Done when:** `/missions/reset` and `/admin/checklists/reset` restore seeded data; any
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
  site root; the Phase 6 GitHub Pages build sets `BASE_PATH=/mission-control`).
- Quality gates: `oxlint` (lint) + `oxfmt` (format) via Oxc — **not** ESLint/Prettier.
  Scripts `lint`, `format`, `format:check`; configs `.oxlintrc.json` / `.oxfmtrc.json`
  (both ignore `**/*.svelte`, `build`, `.svelte-kit`). `.svelte` formatting is handled by
  the `svelte.svelte-vscode` VS Code extension (format-on-save, set in root `.vscode`).
- **Done when:** `pnpm run dev` serves the app (200 shell), `pnpm run build` emits static
  `build/` with an `index.html` fallback, and `pnpm run check` / `lint` / `format:check`
  are all clean.

## Phase 5 — Frontend routes + API client (existing, update field names)

- `src/lib/config.ts`: `MISSIONS_API` / `CHECKLISTS_API` from Vite `PUBLIC_MISSIONS_API` /
  `PUBLIC_CHECKLISTS_API`. **Local default is `/api`** (relative) — `vite.config.ts` proxies
  `/api/*` to the local FastAPI backend on :8000, so no hardcoded URL is needed in dev.
  Production build sets the absolute Render URLs via `PUBLIC_*` env.
- `src/lib/api.ts`: typed fetch helpers (`missionsApi`, `checklistsApi`): missions CRUD + reset;
  checklists login (OAuth2 password → Bearer) + CRUD + admin reset; shared `ApiError`.
  - `Book` interface renamed to `Mission` with fields `mission_name`, `commander`, `mission_type`,
    `phase`, `priority`, `launch_date`
  - `Task` interface renamed to `ChecklistItem` with fields `checklist_item`, `criticality`, `executed`,
    `mission_id`, `notes`
- Routes: `/` (two cards: "Mission Control" / "Checklist Ops"), `/missions` (list + create/edit
  - delete + Reset, phase badges color-coded: planning=gray, launch=yellow, active=cyan,
    complete=green, archived=dimmed), `/checklists` (login → list + create/edit/delete + Reset,
    demo-creds note, "ORIGINAL" badge for seeded items). Token persisted in `localStorage`.
- **Seeded indicators:** both `GET /missions` and `GET /checklists` return a `seeded`
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
  --frozen-lockfile` in `projects/gui` → build with `BASE_PATH=/mission-control`
  **and** `PUBLIC_MISSIONS_API` / `PUBLIC_CHECKLISTS_API` set from repo **Secrets**
  (`MISSIONS_API_URL`, `CHECKLISTS_API_URL`) → publish `projects/gui/build` to the
  `gh-pages` branch via `peaceiris/actions-gh-pages@v4`.
- **Authored and verified** (YAML valid; local build with those env vars bakes the
  base path + backend URLs into the bundle). Remaining manual steps (cannot be done
  in-repo):
  1. Add repo **Secrets** `MISSIONS_API_URL` and `CHECKLISTS_API_URL` = the Phase 0 Render URLs.
  2. Repo **Settings → Pages → source: gh-pages** branch.
  3. Push to `main` → workflow deploys.
- **Done when:** `https://<user>.github.io/mission-control/` loads the GUI.

## Phase 8 — Validate

- Local: run both backends; `pnpm run dev` (in `projects/gui`) with envs → localhost; manual CRUD + reset.
- `uv run pytest` for both apps (no regressions from CORS/reset/seed changes).
- Deployed: open the gh-pages URL; confirm CORS in the browser Network tab, live
  CRUD, and reset against Render.
- **Done when:** the public URL demonstrates Mission Control dashboard working.

### Status (validated 2026-08-24)

- **Automated checks PASS (Mission Control migration complete):**
  - `uv run pytest projects/missions_api projects/mission_control_app` → **121 passed** (no
    regressions from the field rename / CORS / reset / seed changes).
  - `pnpm run check` (svelte-check) → **0 errors, 0 warnings**.
  - `pnpm run lint` (oxlint) and `pnpm run format:check` (oxfmt) → **clean**.
  - `pnpm run build` with `BASE_PATH=/mission-control` +
    `PUBLIC_MISSIONS_API`/`PUBLIC_CHECKLISTS_API` → static `build/` emitted with the
    `/mission-control/_app/...` base path **and the Render backend URLs** baked in
    (via `$env/dynamic/public`).
- **Phase 1 (Mission Control rename) is DONE** — see its status block above.
- **Remaining (cannot be done in-repo — gated on Phase 6 manual deploy):**
  1. Finish Phase 6 manual steps (repo Secrets `MISSIONS_API_URL`/`CHECKLISTS_API_URL`,
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
(`projects/missions_api`, `projects/mission_control_app`, `libs/shared`), NOT a `projects/*` glob.
A glob broke `uv sync` on Render (and locally) because `projects/context` is a docs
folder with no `pyproject.toml`, so uv aborted with
"Workspace member projects/context missing a pyproject.toml". Keep the members list
explicit if new subfolders are added under `projects/`.

## Deployment gotcha — Postgres driver (psycopg2 vs psycopg3)

The project depends on **psycopg3** (`psycopg[binary]`), but Render's Internal
Database URL is `postgresql://…`, and SQLAlchemy defaults `postgresql://` to the
**psycopg2** dialect → `ModuleNotFoundError: No module named 'psycopg2'` at
`alembic upgrade head`. Fixes (either works):

- **No push:** set the `checklists-api` `DATABASE_URL` env var to `postgresql+psycopg://…`
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
export const MISSIONS_API = env.PUBLIC_MISSIONS_API || "/api";
export const CHECKLISTS_API = env.PUBLIC_CHECKLISTS_API || "/api";
```

This bakes `PUBLIC_MISSIONS_API` / `PUBLIC_CHECKLISTS_API` into the static build when set at build
time (the `deploy-gui.yml` CI step sets them from repo Secrets) and falls back to the
`/api` dev proxy when unset. Do **not** switch back to `import.meta.env.PUBLIC_*` — the
live site would call `/api` (which does not exist on GitHub Pages) and fail.

## Phase 9 — Complete Rebrand: File & Module Renames (COMPLETED 2026-08-24)

All `book`/`Book`/`task`/`Task` identifiers have been eliminated from active source code:

- **missions_api** (`projects/missions_api`):
  - `main.py` now runs `uvicorn missions_api.missions:app`
  - All models renamed (`Mission`, `MissionBase`, `MissionCreate`, `MissionUpdate`)
  - `books.py` merged into `missions.py`; internal `BOOKS` → `MISSIONS`
  - `mock_data.py` → `seed_missions.py`; seed data is mission-themed
  - Tests in `test_missions.py`; alias files (`body_aliases`, `path_aliases`, `query_aliases`) updated
  - Endpoint URLs: `/missions`, `/missions/{id}`, `/missions/categories/{category}`, etc.

- **checklists_api** (`projects/mission_control_app`):
  - `models/checklist_item.py`: `class ChecklistItem(Base)` with `__tablename__ = "checklist_items"`
  - `schemas/checklist.py`: `CreateChecklistItemRequest`, `ReadChecklistItemRequest`, `UpdateChecklistItemRequest`
  - `routers/checklists.py` + `routers/admin.py` updated
  - `seed_data.py` → `seed_checklists.py` with `SEEDED_CHECKLISTS`
  - `bootstrap.py`, `migrations/env.py`, `conftest.py`, `test_admin.py` updated
  - Endpoint URLs: `/checklists`, `/admin/checklists`, `/admin/checklists/reset`

- **gui** (`projects/gui`):
  - Route folders: `books/` → `missions/`, `tasks/` → `checklists/`
  - `api.ts`: `Book`→`Mission`, `Task`→`ChecklistItem`, `booksApi`→`missionsApi`, `tasksApi`→`checklistsApi`
  - `config.ts` env vars: `MISSIONS_API` / `CHECKLISTS_API`, `PUBLIC_MISSIONS_API` / `PUBLIC_CHECKLISTS_API`

### Final gate criteria (all passing)

- `uv run pytest projects/missions_api projects/mission_control_app` → **121 passed**
- `git grep -inE '\b(Book|Task|book|task)\b'` → zero hits in active source (allowed: `MISSIONS_API` / `CHECKLISTS_API` / `MISSIONS_API_URL` / `CHECKLISTS_API_URL` and their `PUBLIC_` variants)
- Public endpoint URLs: `/missions`, `/checklists`, `/admin/checklists/reset`

---

## Phase 10 — Repo Name Verified (COMPLETED)

**Status:** The repo is already named `mission-control` on GitHub. No rename needed.

This phase was the original repo migration from `fastapi-endpoints` → `mission-control`.
That migration is complete; the remote is `https://github.com/craig-o-curtis/mission-control.git`.

No action required.

---

## Phase 11 — Render Service & DB Renames

> ⚠️ **Interactive confirmation required** — walk through each step and wait for the
> user's confirmation before proceeding (these are paid/manual dashboard actions).

### Step 11.1 — Backup current state

Confirm the current Render service URLs are saved:

- `MISSIONS_API_URL` = ?
- `CHECKLISTS_API_URL` = ?

Reply **"DONE"** when confirmed.

### Step 11.2 — Create new missions_api service

- Click **New + → Web Service** in Render; select the `mission-control` repo (GitHub connected).
- **Name:** `mission-control-api` (was `missions-api`).
- **Root Directory:** `projects/missions_api`.
- **Build Command:** `pip install uv && uv sync`.
- **Start Command:** `uv run uvicorn missions_api.missions:app --host 0.0.0.0 --port $PORT`
  (note the post-Phase-9 module path `missions_api.missions`, not `missions_api.books`).
- **Health Check Path:** `/`.
- **Environment Variables:** `CORS_ORIGINS` = `https://<your-user>.github.io/mission-control`
  (project page for the new repo; no trailing slash).
- Click **Create** → wait for deploy → confirm **Live**.

### Step 11.3 — Create new checklists_api service

- Click **New + → Web Service**; select the `mission-control` repo.
- **Name:** `checklist-api` (was `checklists-api`).
- **Root Directory:** `projects/mission_control_app`.
- **Build Command:** `pip install uv && uv sync`.
- **Start Command:** `uv run alembic upgrade head && uv run uvicorn checklists_api.app:app --host 0.0.0.0 --port $PORT`.
- **Health Check Path:** `/`.
- **Environment Variables:**
  - `DATABASE_URL` = copy the **Internal Database URL** from the old `mission-control-db` Connect panel
    (Render rewrites `postgresql://`→`postgresql+psycopg://` via `config.py`, so paste as-is).
  - `CORS_ORIGINS` = `https://<your-user>.github.io/mission-control`.
  - `SECRET_KEY` = copy from old `checklists-api` (or `openssl rand -hex 32`).
  - `ADMIN_USER`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`, `ADMIN_FIRST_NAME`, `ADMIN_LAST_NAME` = copy from old `checklists-api`.
- Click **Create** → wait for deploy → confirm **Live**.

### Step 11.4 — Update database name (optional)

- Render → Postgres → `mission-control-db` → **Settings → Rename** → `mission-db`.
- The **internal DB name** (`mission_control_application_database`) cannot change without recreating
  the DB; if you recreate it, update `DATABASE_URL` on the new `checklist-api` service.
- Keep the old Postgres for now (delete after Phase 12).

### Step 11.5 — Delete old services

Once both new services are **Live** and verified:

- Delete old `missions-api` service.
- Delete old `checklists-api` service.
- Keep old Postgres for now.

### Step 11.6 — Update GitHub workflow secrets

- GitHub → `mission-control` repo → **Settings → Secrets and variables → Actions**.
- Update secrets (secret _names_ stay the same — they are just keys):
  - `MISSIONS_API_URL` → `https://mission-control-api-xxxx.onrender.com`
  - `CHECKLISTS_API_URL` → `https://checklist-api-xxxx.onrender.com`
- Reply **"DONE"** when secrets are updated.

### Done when

- Both new services are **Live**.
- Old services deleted.
- GitHub Secrets updated with new URLs.

Reply **"PHASE 11 DONE"** to proceed.

---

## Phase 12 — GitHub Pages URL Update & Final Validation

**Goal:** Deploy to the new GitHub Pages URL and verify everything works.

### Step 12.1 — Update Pages settings

- GitHub → `mission-control` repo → **Settings → Pages**.
- **Source:** `gh-pages` branch (already used by `deploy-gui.yml`); confirm publish branch = `gh-pages`.
- Click **Save**.

### Step 12.2 — Trigger deployment

```bash
git push origin main
```

- Go to the **Actions** tab → verify `deploy-gui.yml` runs and completes.
- `deploy-gui.yml` builds with `BASE_PATH=/mission-control` and `PUBLIC_MISSIONS_API` /
  `PUBLIC_CHECKLISTS_API` from the updated secrets, then publishes `projects/gui/build` to `gh-pages`.

### Step 12.3 — Update CORS on Render services

- Render → `mission-control-api` → **Environment** → set
  `CORS_ORIGINS = https://<your-user>.github.io/mission-control`.
- Render → `checklist-api` → **Environment** → set the same `CORS_ORIGINS`.
- Both services auto-redeploy.

### Step 12.4 — Final validation

Open `https://<your-user>.github.io/mission-control/` and verify:

- GUI loads without errors.
- Mission Control dashboard shows mission-themed data.
- Checklist Ops page loads with login.
- CRUD works (create, read, update, delete).
- Reset buttons restore seeded data.
- No CORS errors in the browser console.
- All field names are mission/checklist themed.

Run local checks:

```bash
uv run pytest projects/missions_api projects/mission_control_app
cd projects/gui && pnpm run check && pnpm run lint && pnpm run format:check
```

### Done when

- `https://<your-user>.github.io/mission-control/` is live and fully functional.
- All automated checks pass.
- No references to old names remain in deployed code (except the allowed env-var namespace).

---

## Final Checklist

- [x] Phase 1: schema migration complete (missions_api fields + checklists_api fields renamed, seed data mission-themed).
- [x] Phase 9: file & module renames complete (incl. `main.py`, alias files, `migrations/env.py`, `conftest.py`, `test_admin.py`).
- [x] Phase 9: endpoint URLs (`/missions`, `/checklists`, …) verified changed.
- [x] Phase 10: repo name verified as `mission-control`.
- [ ] Phase 11: Render services renamed (future manual step).
- [ ] Phase 12: GitHub Pages URL update + final validation (future manual step).
- [x] All tests passing (`pytest` → 121 passed, `svelte-check` clean, `oxlint` + `oxfmt` clean).
- [x] No remaining `book`/`task`/`Book`/`Task` references in active source (env-var namespace excepted).
- [ ] Deployed URL demonstrates the complete Mission Control experience (pending Phase 11–12).
