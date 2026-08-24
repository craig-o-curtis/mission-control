from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query
from starlette import status
from tasks_api.dependencies.db_dep import DbDep
from tasks_api.dependencies.user_dep import UserDep
from tasks_api.models.task import Task
from tasks_api.schemas.tasks import (
    CreateTaskRequest,
    ReadTaskRequest,
    UpdateTaskRequest,
)
from tasks_api.seed_data import SEEDED_TASKS

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user) -> None:
    """Raise 403 if user is not admin."""
    if user is None or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )


# ── Admin Task CRUD ────────────────────────────────────────────────


@router.get("/tasks", status_code=status.HTTP_200_OK)
def admin_get_all_tasks(
    user: UserDep,
    db: DbDep,
    skip: Annotated[int, Query(ge=0, description="Number of tasks to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max tasks to return")] = 100,
) -> list[ReadTaskRequest]:
    """Get all tasks with pagination (admin only)."""
    _require_admin(user)
    # return in structure of ReadTaskRequest for consistency with other endpoints
    # so is a list of ReadTaskRequest objects, not a list of Task objects
    # ReadTaskRequest is a Pydantic model, so we can use model_validate
    # to convert Task objects to ReadTaskRequest objects
    return [
        ReadTaskRequest.model_validate(t)
        for t in db.query(Task).offset(skip).limit(limit).all()
    ]


@router.get(
    "/tasks/{task_id}",
    response_model=ReadTaskRequest,
    status_code=status.HTTP_200_OK,
)
def admin_get_task(
    user: UserDep,
    db: DbDep,
    task_id: Annotated[int, Path(gt=0, description="Task ID")],
) -> ReadTaskRequest:
    """Get a single task by ID (admin only)."""
    _require_admin(user)
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    return ReadTaskRequest.model_validate(task)


@router.post(
    "/tasks",
    response_model=ReadTaskRequest,
    status_code=status.HTTP_201_CREATED,
)
def admin_create_task(
    user: UserDep,
    db: DbDep,
    task: CreateTaskRequest,
) -> ReadTaskRequest:
    """Create a new task (admin only)."""
    _require_admin(user)
    task_model = Task(**task.model_dump())
    db.add(task_model)
    db.commit()
    db.refresh(task_model)
    return ReadTaskRequest.model_validate(task_model)


@router.put(
    "/tasks/{task_id}",
    response_model=ReadTaskRequest,
    status_code=status.HTTP_200_OK,
)
def admin_update_task(
    user: UserDep,
    db: DbDep,
    task_id: Annotated[int, Path(gt=0, description="Task ID")],
    task: UpdateTaskRequest,
) -> ReadTaskRequest:
    """Update an existing task (admin only)."""
    _require_admin(user)
    task_model = db.query(Task).filter(Task.id == task_id).first()
    if task_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    for key, value in task.model_dump(exclude_unset=True).items():
        setattr(task_model, key, value)
    db.commit()
    db.refresh(task_model)
    return ReadTaskRequest.model_validate(task_model)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_task(
    user: UserDep,
    db: DbDep,
    task_id: Annotated[int, Path(gt=0, description="Task ID")],
) -> None:
    """Delete a task (admin only)."""
    _require_admin(user)
    task_model = db.query(Task).filter(Task.id == task_id).first()
    if task_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    db.delete(task_model)
    db.commit()


@router.post("/tasks/reset", status_code=status.HTTP_200_OK)
def admin_reset_tasks(
    user: UserDep,
    db: DbDep,
) -> dict:
    """Reset all tasks to the original seeded state (admin only)."""
    _require_admin(user)
    deleted = db.query(Task).delete()
    db.commit()
    for spec in SEEDED_TASKS:
        db.add(Task(owner_id=user.id, seeded=True, **spec))
    db.commit()
    return {"deleted": deleted, "seeded": len(SEEDED_TASKS)}
