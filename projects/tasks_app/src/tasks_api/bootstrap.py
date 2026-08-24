"""Idempotent demo seeding that runs on app startup.

Render's free tier has no web shell, so instead of relying on
`scripts/seed.py` we create the admin user automatically on boot. Safe to run
on every deploy — it only inserts the admin if it does not already exist.
"""

import os

from tasks_api.database import SessionLocal
from tasks_api.models.user import User
from tasks_api.security import bcrypt_context


def ensure_admin() -> None:
    """Create the demo admin user from env vars if it does not exist yet."""
    username = os.getenv("ADMIN_USER")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        return

    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    first_name = os.getenv("ADMIN_FIRST_NAME", "Admin")
    last_name = os.getenv("ADMIN_LAST_NAME", "User")

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing is not None:
            return
        db.add(
            User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number="555-0000",
                hashed_password=bcrypt_context.hash(password),
                is_active=True,
                role="admin",
            )
        )
        db.commit()
    finally:
        db.close()
