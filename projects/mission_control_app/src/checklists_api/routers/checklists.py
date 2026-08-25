"""Route handlers for checklists API."""

from typing import Annotated

from checklists_api.dependencies.db_dep import DbDep
from checklists_api.dependencies.user_dep import UserDep
from checklists_api.models.checklist_item import ChecklistItem
from checklists_api.schemas.checklist import (
    CreateChecklistItemRequest,
    ReadChecklistItemRequest,
    UpdateChecklistItemRequest,
)
from fastapi import APIRouter, HTTPException, Path, Query
from starlette import status

router = APIRouter(prefix="/checklists", tags=["checklists"])


@router.get("/", response_model=list[ReadChecklistItemRequest])
def get_all_checklist_items(
    user: UserDep,
    db: DbDep,
    skip: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max items to return")] = 100,
) -> list[ReadChecklistItemRequest]:
    """Get all checklist items with pagination."""

    return [
        ReadChecklistItemRequest.model_validate(t)
        for t in db.query(ChecklistItem)
        .filter(ChecklistItem.owner_id == user.id)
        .offset(skip)
        .limit(limit)
        .all()
    ]


@router.get("/{checklist_item_id}", response_model=ReadChecklistItemRequest)
def get_checklist_item_by_id(
    user: UserDep,
    db: DbDep,
    checklist_item_id: Annotated[int, Path(gt=0, description="Checklist item ID")],
) -> ReadChecklistItemRequest:
    """Get a single checklist item by ID."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    checklist_item = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.id == checklist_item_id)
        .filter(ChecklistItem.owner_id == user.id)
        .first()
    )
    if checklist_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found"
        )
    return ReadChecklistItemRequest.model_validate(checklist_item)


@router.post("/", response_model=ReadChecklistItemRequest, status_code=201)
def create_checklist_item(
    user: UserDep, db: DbDep, checklist_item: CreateChecklistItemRequest
) -> ReadChecklistItemRequest:
    """Create a new checklist item."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    checklist_item_model = ChecklistItem(
        **checklist_item.model_dump(), owner_id=user.id
    )

    # db.add lets session know that we want to add this object to the database.
    db.add(checklist_item_model)
    # db.commit() is used to commit the changes to the database.
    db.commit()
    # db.refresh() is used to refresh the object from the database.
    db.refresh(checklist_item_model)
    return ReadChecklistItemRequest.model_validate(checklist_item_model)


@router.put("/{checklist_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_checklist_item(
    user: UserDep,
    db: DbDep,
    checklist_item_id: Annotated[int, Path(gt=0, description="Checklist item ID")],
    checklist_item: UpdateChecklistItemRequest,
) -> None:
    """Update an existing checklist item."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    checklist_item_model = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.id == checklist_item_id)
        .filter(ChecklistItem.owner_id == user.id)
        .first()
    )
    if checklist_item_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found"
        )
    for key, value in checklist_item.model_dump(exclude_unset=True).items():
        # skip updating the owner_id field to prevent changing the item's owner
        if key == "owner_id":
            continue
        setattr(checklist_item_model, key, value)
    db.commit()
    db.refresh(checklist_item_model)


@router.delete("/{checklist_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_checklist_item(
    user: UserDep,
    db: DbDep,
    checklist_item_id: Annotated[int, Path(gt=0, description="Checklist item ID")],
) -> None:
    """Delete a checklist item."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )

    checklist_item_model = (
        db.query(ChecklistItem)
        .filter(ChecklistItem.id == checklist_item_id)
        .filter(ChecklistItem.owner_id == user.id)
        .first()
    )
    if checklist_item_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found"
        )
    db.delete(checklist_item_model)
    db.commit()
