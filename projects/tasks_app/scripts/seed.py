#!/usr/bin/env python3
"""Seed the database with an admin user.

All values come from environment variables. No hardcoded secrets.
"""

from __future__ import annotations

import os
import sys

from sqlalchemy.orm import Session
from tasks_api.database import SessionLocal, engine
from tasks_api.models.user import User
from tasks_api.security import bcrypt_context

REQUIRED_ENV_VARS = [
    "ADMIN_USER",
    "ADMIN_PASSWORD",
    "ADMIN_EMAIL",
    "ADMIN_FIRST_NAME",
    "ADMIN_LAST_NAME",
]


def _require_env() -> dict[str, str]:
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        print(f"Error: missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return {var: os.environ[var] for var in REQUIRED_ENV_VARS}


def seed_admin(
    username: str,
    password: str,
    email: str,
    first_name: str,
    last_name: str,
) -> None:
    db: Session = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Admin user '{username}' already exists — updating.")
            existing.hashed_password = bcrypt_context.hash(password)
            existing.email = email
            existing.first_name = first_name
            existing.last_name = last_name
            db.commit()
        else:
            admin = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number="555-0000",
                hashed_password=bcrypt_context.hash(password),
                is_active=True,
                role="admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print(f"Admin user created: {username}")
    finally:
        db.close()


def main() -> None:
    from sqlalchemy import inspect

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "users" not in tables:
        print(
            "Error: 'users' table does not exist."
            " Start the app first so init_db() can create tables."
        )
        sys.exit(1)

    env = _require_env()
    seed_admin(
        username=env["ADMIN_USER"],
        password=env["ADMIN_PASSWORD"],
        email=env["ADMIN_EMAIL"],
        first_name=env["ADMIN_FIRST_NAME"],
        last_name=env["ADMIN_LAST_NAME"],
    )


if __name__ == "__main__":
    main()
