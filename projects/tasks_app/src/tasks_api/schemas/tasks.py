from pydantic import BaseModel, ConfigDict, Field

# File for pydantic models


class ReadTaskRequest(BaseModel):
    id: int
    title: str
    description: str | None
    priority: int | None
    completed: bool
    seeded: bool

    # This is key: tells pydantic to read from the SQLAlchemy model attributes,
    # not just the dict.
    model_config = ConfigDict(from_attributes=True)


class CreateTaskRequest(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    priority: int | None = Field(default=None, gt=0, le=5)
    completed: bool = Field(default=False)


class UpdateTaskRequest(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    priority: int | None = Field(default=None, gt=0, le=5)
    completed: bool | None = Field(default=None)
