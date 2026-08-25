"""Security utilities for checklists API."""

from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from checklists_api.config import ALGORITHM, SECRET_KEY
from checklists_api.models.user import User

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def authenticate_user(username: str, password: str, db: Session) -> User | None:
    """Authenticate a user. Returns the User object or None."""
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return None
    return user


def verify_password(username: str, password: str, db: Session) -> bool:
    """Verify a password against a user's stored hash. Returns True/False."""
    user = authenticate_user(username, password, db)
    return user is not None


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
) -> str:
    """Create a JWT access token."""
    encode = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(UTC) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
