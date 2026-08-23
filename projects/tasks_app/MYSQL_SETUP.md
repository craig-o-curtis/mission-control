# MySQL Setup

Docker Compose (isolated, disposable) or local MySQL Mac app (persistent). Pick one.

## Option A: Docker Compose (recommended)

> **Sanity check:** If you already have MySQL running locally on port `3306`, stop it first.

### Spin Up

From `projects/tasks_app/`:

```bash
docker compose -f docker-compose.mysql.yml up -d
```

Verify:

```bash
docker compose -f docker-compose.mysql.yml ps
```

You should see `mysql` and `adminer` with state `Up`.

Confirm MySQL is reachable:

```bash
docker compose -f docker-compose.mysql.yml exec mysql mysqladmin ping -h localhost -u root -p12345678
```

Open Adminer: http://localhost:8080

Log in to Adminer:

- System: `MySQL`
- Server: `mysql`
- Username: `root`
- Password: `.env.MYSQL_ROOT_PASSWORD`
- Database: `tasks_application_database`

### 3. Point the app at MySQL

In `.env`, uncomment the MySQL `DATABASE_URL`:

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
docker compose -f docker-compose.mysql.yml down
```

### Wipe data

From `projects/tasks_app/`:

```bash
docker compose -f docker-compose.mysql.yml down -v
```

## Option B: Local MySQL Mac App

1. Start your local MySQL server.
2. Create the database:
   ```bash
   mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS tasks_application_database;"
   ```
3. Connect using Adminer (Docker) or a local client like Sequel Ace.
4. Start the app — it auto-creates tables via `init_db()`.
5. Seed the admin user (see below).

## Seeding the Database

After the DB is running and the app has started (tables auto-created), seed the admin user:

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

## Testing Against MySQL

> **Note:** Tests use a separate database (`tasks_application_database_test`). Create it first:

```bash
docker compose -f docker-compose.mysql.yml exec mysql mysql -u root -p12345678 -e "CREATE DATABASE IF NOT EXISTS tasks_application_database_test;"
```

Then run:

```bash
TEST_DATABASE_URL=mysql+pymysql://root:12345678@localhost:3306/tasks_application_database_test uv run pytest projects/tasks_app/tests/ -v
```

> If you used Docker Compose, use host `localhost` (not `mysql`) in the connection string since the tests run outside Docker.

## Docker Compose Environment Variables

Docker Compose reads secrets from `.env` in the project root. Copy `.env.example` to `.env` and change the defaults before starting:

```bash
cp .env.example .env
# Edit .env and change MYSQL_ROOT_PASSWORD / POSTGRES_PASSWORD etc.
```

| Variable                   | Default                      | Description             |
| -------------------------- | ---------------------------- | ----------------------- |
| `MYSQL_ROOT_PASSWORD`      | `.env.MYSQL_ROOT_PASSWORD`   | MySQL root password     |
| `MYSQL_DATABASE`           | `tasks_application_database` | Database name           |
| `MYSQL_PORT`               | `3306`                       | Host port for MySQL     |
| `ADMINER_PORT`             | `8080`                       | Host port for Adminer   |
| `POSTGRES_USER`            | `postgres`                   | Postgres superuser      |
| `POSTGRES_PASSWORD`        | `.env.POSTGRES_PASSWORD`     | Postgres root password  |
| `POSTGRES_DB`              | `TasksApplicationDatabase`   | Database name           |
| `POSTGRES_PORT`            | `5432`                       | Host port for Postgres  |
| `PGADMIN_DEFAULT_EMAIL`    | `admin@example.com`          | pgAdmin4 login email    |
| `PGADMIN_DEFAULT_PASSWORD` | `.env.ADMIN_PASSWORD`        | pgAdmin4 login password |
| `PGADMIN_PORT`             | `5050`                       | Host port for pgAdmin4  |
