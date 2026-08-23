# Quick Start

All commands run from the `projects/tasks_app/` directory. From the monorepo root:

```bash
cd projects/tasks_app
```

## Spin Up

### 1. Start the database

Pick the stack you want:

**MySQL:**

```bash
docker compose -f docker-compose.mysql.yml up -d
```

**Postgres:**

```bash
docker compose -f docker-compose.postgres.yml up -d
```

Verify:

```bash
docker compose -f docker-compose.mysql.yml ps
# or
docker compose -f docker-compose.postgres.yml ps
```

**MySQL GUI (Adminer):** http://localhost:8080

- Server: `mysql`
- Username: `root`
- Password: `.env.MYSQL_ROOT_PASSWORD`
- Database: `tasks_application_database`

**Postgres GUI (pgAdmin4):** http://localhost:5050

- Email: `admin@example.com`
- Password: `.env.ADMIN_PASSWORD`
- Add server: Host `db`, Port `5432`, User `postgres`, Password `.env.POSTGRES_PASSWORD`

### 2. Start the app

```bash
uv run tasks-api
```

The app's lifespan calls `init_db()`, which auto-creates the `users` and `tasks` tables if they don't exist.

### 3. Seed the admin user

```bash
uv run python scripts/seed.py
# or with a custom password:
uv run python scripts/seed.py --password mypassword
```

### 4. Log in

```bash
ADMIN_USER=$(grep ADMIN_USER .env | cut -d= -f2)
ADMIN_PASSWORD=$(grep ADMIN_PASSWORD .env | cut -d= -f2)
curl -X POST http://127.0.0.1:8000/auth/token \
  -d "username=$ADMIN_USER" \
  -d "password=$ADMIN_PASSWORD"
```

## Spin Down

### Stop the app

In the terminal running `uv run tasks-api`:

```bash
# Press Ctrl+C
```

### Stop the database containers

**MySQL:**

```bash
docker compose -f docker-compose.mysql.yml down
```

**Postgres:**

```bash
docker compose -f docker-compose.postgres.yml down
```

### Wipe all data (nuclear option)

**MySQL:**

```bash
docker compose -f docker-compose.mysql.yml down -v
```

**Postgres:**

```bash
docker compose -f docker-compose.postgres.yml down -v
```

After a full wipe, repeat the **Spin Up** steps from the top.
