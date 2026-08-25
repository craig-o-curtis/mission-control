"""Route handlers for users API."""

from typing import Annotated

from checklists_api.dependencies.db_dep import DbDep
from checklists_api.dependencies.user_dep import UserDep
from checklists_api.models.user import User
from checklists_api.schemas.users import (
    CreateUserRequest,
    ReadUserPublic,
    UpdateUserPasswordRequest,
    UpdateUserPhoneRequest,
    UpdateUserRequest,
)
from checklists_api.security import bcrypt_context, verify_password
from fastapi import APIRouter, HTTPException, Path, status

router = APIRouter(prefix="/users", tags=["users"])


def _require_admin(user) -> None:
    """Raise 403 if user is not admin."""
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )


# ── Admin User CRUD ────────────────────────────────────────────────


@router.get("", response_model=list[ReadUserPublic])
def admin_read_users(
    user: UserDep,
    db: DbDep,
) -> list[ReadUserPublic]:
    """Get all users (admin only)."""
    _require_admin(user)
    users = db.query(User).all()
    return [ReadUserPublic.model_validate(u) for u in users]


@router.post("", response_model=ReadUserPublic, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    user: UserDep,
    db: DbDep,
    new_user: CreateUserRequest,
) -> ReadUserPublic:
    """Create a new user with any role (admin only)."""
    _require_admin(user)

    if db.query(User).filter(User.username == new_user.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    if db.query(User).filter(User.email == new_user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user_model = User(
        email=new_user.email,
        username=new_user.username,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        phone_number=new_user.phone_number,
        role=new_user.role or "user",
        hashed_password=bcrypt_context.hash(new_user.password),
        is_active=True,
    )

    db.add(user_model)
    db.commit()
    db.refresh(user_model)
    return ReadUserPublic.model_validate(user_model)


# ── Self-service endpoints ─────────────────────────────────────────

# NOTE: /me and /me/password MUST come before /{user_id} routes below —
# FastAPI matches top-to-bottom, and /{user_id} would otherwise swallow
# /me requests (parsing "me" as user_id and failing path validation).


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def update_current_user_password(
    user: UserDep,
    db: DbDep,
    updates: UpdateUserPasswordRequest,
) -> None:
    """Update current user's own password."""
    # Verify current password
    if not verify_password(str(user.username), updates.current_password, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
        )

    # Reject same password
    if bcrypt_context.verify(updates.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must differ from current password",
        )

    user.hashed_password = bcrypt_context.hash(updates.new_password)
    db.commit()


@router.patch("/me/phone-number", status_code=status.HTTP_204_NO_CONTENT)
def update_current_user_phone(
    user: UserDep,
    db: DbDep,
    updates: UpdateUserPhoneRequest,
) -> None:
    """Update current user's own phone number."""
    user.phone_number = updates.phone_number
    db.commit()


@router.get("/me", response_model=ReadUserPublic)
def get_current_user_profile(
    user: UserDep,
    db: DbDep,
) -> ReadUserPublic:
    """Get current user's own profile."""
    return ReadUserPublic.model_validate(user)


@router.put("/me", response_model=ReadUserPublic)
def update_current_user(
    user: UserDep,
    db: DbDep,
    updates: UpdateUserRequest,
) -> ReadUserPublic:
    """Update current user's own profile. Cannot change role."""
    for key, value in updates.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        if key == "role":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role",
            )
        if key == "password":
            setattr(user, key, bcrypt_context.hash(value))
        else:
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return ReadUserPublic.model_validate(user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(
    user: UserDep,
    db: DbDep,
) -> None:
    """Delete current user's own account."""
    db.delete(user)
    db.commit()


# ── Admin User CRUD (by ID) ────────────────────────────────────────


@router.get("/{user_id}", response_model=ReadUserPublic)
def admin_read_user(
    user: UserDep,
    db: DbDep,
    user_id: Annotated[int, Path(gt=0, description="User ID")],
) -> ReadUserPublic:
    """Get a single user by ID (admin only)."""
    _require_admin(user)
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return ReadUserPublic.model_validate(target)


@router.put("/{user_id}", response_model=ReadUserPublic)
def admin_update_user(
    user: UserDep,
    db: DbDep,
    user_id: Annotated[int, Path(gt=0, description="User ID")],
    updates: UpdateUserRequest,
) -> ReadUserPublic:
    """Update an existing user (admin only)."""
    _require_admin(user)
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    for key, value in updates.model_dump(exclude_unset=True).items():
        if value is None:
            continue
        if key == "password":
            setattr(target, key, bcrypt_context.hash(value))
        elif key == "hashed_password":
            continue
        else:
            setattr(target, key, value)

    db.commit()
    db.refresh(target)
    return ReadUserPublic.model_validate(target)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user: UserDep,
    db: DbDep,
    user_id: Annotated[int, Path(gt=0, description="User ID")],
) -> None:
    """Delete a user (admin only)."""
    _require_admin(user)
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    db.delete(target)
    db.commit()
