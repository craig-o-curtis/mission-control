"""Idempotent demo seeding that runs on app startup.

Render's free tier has no web shell, so instead of relying on
`scripts/seed.py` we create the admin user (and seeded demo checklist
items) automatically on boot. Safe to run on every deploy — it only
inserts what is missing.
"""

from checklists_api.config import (
    ADMIN_EMAIL,
    ADMIN_FIRST_NAME,
    ADMIN_LAST_NAME,
    ADMIN_PASSWORD,
    ADMIN_USER,
)
from checklists_api.database import SessionLocal
from checklists_api.models.checklist_item import ChecklistItem
from checklists_api.models.user import User
from checklists_api.security import bcrypt_context
from checklists_api.seed_checklists import SEEDED_CHECKLISTS


def ensure_admin() -> User | None:
    """Create the demo admin user from env vars if it does not exist yet."""
    username = ADMIN_USER
    password = ADMIN_PASSWORD

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is not None:
            return user
        user = User(
            username=username,
            email=ADMIN_EMAIL,
            first_name=ADMIN_FIRST_NAME,
            last_name=ADMIN_LAST_NAME,
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
    """Ensure the admin exists and the seeded demo checklist items are present."""
    admin = ensure_admin()
    if admin is None:
        return

    db = SessionLocal()
    try:
        seeded_exists = (
            db.query(ChecklistItem).filter(ChecklistItem.seeded).first() is not None
        )
        if seeded_exists:
            return
        for spec in SEEDED_CHECKLISTS:
            db.add(ChecklistItem(owner_id=admin.id, seeded=True, **spec))
        db.commit()
    finally:
        db.close()
