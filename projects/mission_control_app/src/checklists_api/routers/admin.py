from typing import Annotated

from checklists_api.dependencies.db_dep import DbDep
from checklists_api.dependencies.user_dep import UserDep
from checklists_api.models.checklist_item import ChecklistItem
from checklists_api.schemas.checklist import (
    CreateChecklistItemRequest,
    ReadChecklistItemRequest,
    UpdateChecklistItemRequest,
)
from checklists_api.seed_checklists import SEEDED_CHECKLISTS
from fastapi import APIRouter, HTTPException, Path, Query
from starlette import status

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user) -> None:
    """Raise 403 if user is not admin."""
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )


# ── Admin Checklist Item CRUD ──────────────────────────────────────


@router.get("/checklists", status_code=status.HTTP_200_OK)
def admin_get_all_checklist_items(
    user: UserDep,
    db: DbDep,
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 100,
) -> list[ReadChecklistItemRequest]:
    """Get all checklist items with pagination (admin only)."""
    _require_admin(user)
    return [
        ReadChecklistItemRequest.model_validate(t)
        for t in db.query(ChecklistItem).offset(skip).limit(limit).all()
    ]


@router.get(
    "/checklists/{checklist_item_id}",
    response_model=ReadChecklistItemRequest,
    status_code=status.HTTP_200_OK,
)
def admin_get_checklist_item(
    user: UserDep,
    db: DbDep,
    checklist_item_id: Annotated[int, Path(gt=0, description="Checklist item ID")],
) -> ReadChecklistItemRequest:
    """Get a single checklist item by ID (admin only)."""
    _require_admin(user)
    checklist_item = (
        db.query(ChecklistItem).filter(ChecklistItem.id == checklist_item_id).first()
    )
    if checklist_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found"
        )
    return ReadChecklistItemRequest.model_validate(checklist_item)


@router.post(
    "/checklists",
    response_model=ReadChecklistItemRequest,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_checklist_item(
    user: UserDep,
    db: DbDep,
    checklist_item: CreateChecklistItemRequest,
) -> ReadChecklistItemRequest:
    """Create a new checklist item (admin only)."""
    _require_admin(user)
    checklist_item_model = ChecklistItem(**checklist_item.model_dump())
    db.add(checklist_item_model)
    db.commit()
    db.refresh(checklist_item_model)
    return ReadChecklistItemRequest.model_validate(checklist_item_model)


@router.put(
    "/checklists/{checklist_item_id}",
    response_model=ReadChecklistItemRequest,
    status_code=status.HTTP_200_OK,
)
def admin_update_checklist_item(
    user: UserDep,
    db: DbDep,
    checklist_item_id: Annotated[int, Path(gt=0, description="Checklist item ID")],
    checklist_item: UpdateChecklistItemRequest,
) -> ReadChecklistItemRequest:
    """Update an existing checklist item (admin only)."""
    _require_admin(user)
    checklist_item_model = (
        db.query(ChecklistItem).filter(ChecklistItem.id == checklist_item_id).first()
    )
    if checklist_item_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found"
        )
    for key, value in checklist_item.model_dump(exclude_unset=True).items():
        setattr(checklist_item_model, key, value)
    db.commit()
    db.refresh(checklist_item_model)
    return ReadChecklistItemRequest.model_validate(checklist_item_model)


@router.delete(
    "/checklists/{checklist_item_id}", status_code=status.HTTP_204_NO_CONTENT
)
def admin_delete_checklist_item(
    user: UserDep,
    db: DbDep,
    checklist_item_id: Annotated[int, Path(gt=0, description="Checklist item ID")],
) -> None:
    """Delete a checklist item (admin only)."""
    _require_admin(user)
    checklist_item_model = (
        db.query(ChecklistItem).filter(ChecklistItem.id == checklist_item_id).first()
    )
    if checklist_item_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found"
        )
    db.delete(checklist_item_model)
    db.commit()


@router.post("/checklists/reset", status_code=status.HTTP_200_OK)
def admin_reset_checklist_items(
    user: UserDep,
    db: DbDep,
) -> dict:
    """Reset all checklist items to the original seeded state (admin only)."""
    _require_admin(user)
    deleted = db.query(ChecklistItem).delete()
    db.commit()
    for spec in SEEDED_CHECKLISTS:
        db.add(ChecklistItem(owner_id=user.id, seeded=True, **spec))
    db.commit()
    return {"deleted": deleted, "seeded": len(SEEDED_CHECKLISTS)}
