# Postgres Setup

Docker Compose (isolated, disposable) or local Postgres + pgAdmin4 (persistent). Pick one.

## Option A: Docker Compose (recommended)

> **Sanity check:** If you already have Postgres running locally on port `5432`, stop it first:
>
> ```bash
> brew services stop postgresql
> # or
> pg_ctl -D /usr/local/var/postgres stop
> ```

### Spin Up

From `projects/tasks_app/`:

```bash
docker compose -f docker-compose.postgres.yml up -d
```

Verify:

```bash
docker compose -f docker-compose.postgres.yml ps
```

You should see `db` and `pgadmin` with state `Up`.

Confirm Postgres is reachable:

```bash
docker compose -f docker-compose.postgres.yml exec db pg_isready -U postgres -d TasksApplicationDatabase
```

Open pgAdmin4: http://localhost:5050

- Email: `admin@example.com`
- Password: `.env.ADMIN_PASSWORD`

Add a server connection in pgAdmin4:

- **General:** Name: `Tasks DB`
- **Connection:**
  - Host: `db`
  - Port: `5432`
  - Maintenance database: `TasksApplicationDatabase`
  - Username: `postgres`
  - Password: `.env.POSTGRES_PASSWORD`

### 3. Point the app at Postgres

In `.env`, uncomment the Postgres `DATABASE_URL`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:<.env.POSTGRES_PASSWORD>@localhost:5432/TasksApplicationDatabase
```

### 4. Start the app

```bash
uv run tasks-api
```

The app's `init_db()` auto-creates the `users` and `tasks` tables on startup.

### 5. Seed the admin user

In another terminal:

```bash
uv run python scripts/seed.py
```

This reads `ADMIN_USER`, `ADMIN_PASSWORD`, etc. from `.env` and creates the admin user.

### 6. Log in

- Open http://127.0.0.1:8000/docs
- Use `/auth/token` with:
  - **username:** `admin`
  - **password:** `.env.ADMIN_PASSWORD`

### Spin Down

From `projects/tasks_app/`:

```bash
docker compose -f docker-compose.postgres.yml down
```

### Wipe data

From `projects/tasks_app/`:

```bash
docker compose -f docker-compose.postgres.yml down -v
```

## Option B: Local Postgres + pgAdmin4 Mac App

1. Start your local Postgres:
   ```bash
   brew services start postgresql
   ```
2. Create the database:
   ```bash
   createdb TasksApplicationDatabase
   ```
3. Open your **pgAdmin4 Mac app** and connect to `localhost:5432`.
4. Start the app — it auto-creates tables via `init_db()`.
5. Seed the admin user (see below).

## Seeding the Database

After the app has started (tables auto-created), seed the admin user:

```bash
uv run python scripts/seed.py
# or with a custom password:
uv run python scripts/seed.py --password mypassword
```

## Sanity Checks

Start the API:

```bash
uv run tasks-api
```

Test login:

```bash
ADMIN_USER=$(grep ADMIN_USER .env | cut -d= -f2)
ADMIN_PASSWORD=$(grep ADMIN_PASSWORD .env | cut -d= -f2)
curl -X POST http://127.0.0.1:8000/auth/token \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD"
```

## Switching Backends

Change `DATABASE_URL` in `.env`, then repeat migrations and seeding for the new database.

## Testing Against Postgres

> **Note:** Tests use a separate database (`TasksApplicationDatabase_test`). Create it first:

```bash
docker compose -f docker-compose.postgres.yml exec db psql -U postgres -c "CREATE DATABASE \"TasksApplicationDatabase_test\";"
```

Then run:

```bash
TEST_DATABASE_URL=postgresql+psycopg://postgres:12345678@localhost:5432/TasksApplicationDatabase_test uv run pytest projects/tasks_app/tests/ -v
```

> If you used Docker Compose, use host `localhost` (not `db`) in the connection string since the tests run outside Docker.
