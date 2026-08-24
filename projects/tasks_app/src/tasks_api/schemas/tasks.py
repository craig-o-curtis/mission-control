from pydantic import BaseModel, ConfigDict, Field

# File for pydantic models


class ReadTaskRequest(BaseModel):
    id: int
    checklist_item: str
    description: str | None
    criticality: int | None
    executed: bool
    mission_id: int | None
    notes: str | None
    seeded: bool

    # This is key: tells pydantic to read from the SQLAlchemy model attributes,
    # not just the dict.
    model_config = ConfigDict(from_attributes=True)


class CreateTaskRequest(BaseModel):
    checklist_item: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    criticality: int | None = Field(default=None, gt=0, le=4)
    executed: bool = Field(default=False)
    mission_id: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=500)


class UpdateTaskRequest(BaseModel):
    checklist_item: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    criticality: int | None = Field(default=None, gt=0, le=4)
    executed: bool | None = Field(default=None)
    mission_id: int | None = Field(default=None, gt=0)
    notes: str | None = Field(default=None, max_length=500)
