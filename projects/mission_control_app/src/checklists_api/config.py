"""Configuration for checklists API."""

import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

load_dotenv(PROJECT_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "test-secret-key-for-testing-only")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

ADMIN_USER = os.getenv("ADMIN_USER", "demo")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "demo")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "demo@example.com")
ADMIN_FIRST_NAME = os.getenv("ADMIN_FIRST_NAME", "Demo")
ADMIN_LAST_NAME = os.getenv("ADMIN_LAST_NAME", "User")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    os.getenv(
        "RENDER_DB_INTERNAL_DATABASE_URL",
        f"sqlite:///{DATA_DIR / 'checklistsapp.db'}",
    ),
)

# Render injects a `postgres://` URL, but SQLAlchemy needs the explicit psycopg3
# driver. Normalize the scheme so it works on Render and still works locally.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
