"""Idempotent demo seeding that runs on app startup.

Render's free tier has no web shell, so instead of relying on
`scripts/seed.py` we create the admin user (and seeded demo tasks) automatically
on boot. Safe to run on every deploy — it only inserts what is missing.
"""

import os

from tasks_api.database import SessionLocal
from tasks_api.models.task import Task
from tasks_api.models.user import User
from tasks_api.security import bcrypt_context
from tasks_api.seed_data import SEEDED_TASKS


def ensure_admin() -> User | None:
    """Create the demo admin user from env vars if it does not exist yet."""
    username = os.getenv("ADMIN_USER")
    password = os.getenv("ADMIN_PASSWORD")
    if not username or not password:
        return None

    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    first_name = os.getenv("ADMIN_FIRST_NAME", "Admin")
    last_name = os.getenv("ADMIN_LAST_NAME", "User")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is not None:
            return user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number="555-0000",
            hashed_password=bcrypt_context.hash(password),
            is_active=True,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def ensure_seed_data() -> None:
    """Ensure the admin exists and the seeded demo tasks are present."""
    admin = ensure_admin()
    if admin is None:
        return

    db = SessionLocal()
    try:
        seeded_exists = db.query(Task).filter(Task.seeded).first() is not None
        if seeded_exists:
            return
        for spec in SEEDED_TASKS:
            db.add(Task(owner_id=admin.id, seeded=True, **spec))
        db.commit()
    finally:
        db.close()
