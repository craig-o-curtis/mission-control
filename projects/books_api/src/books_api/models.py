from typing import Literal

from pydantic import BaseModel, Field

MissionPhase = Literal["planning", "launch", "active", "complete", "archived"]

MISSION_TYPES = ["orbital", "eva", "deep_space", "surface"]


class BookBase(BaseModel):
    """Shared fields for all mission models."""

    mission_name: str = Field(
        min_length=2,
        max_length=100,
        description="The name of the mission.",
        examples=["Artemis Lunar Landing"],
    )
    commander: str = Field(
        min_length=2,
        max_length=100,
        description="The mission commander.",
        examples=["Lovell"],
    )
    mission_type: str = Field(
        min_length=2,
        max_length=50,
        description="The type of mission (orbital, eva, deep_space, surface).",
        examples=["surface"],
    )
    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="The description of the mission.",
        examples=["A crewed lunar landing attempt."],
    )
    phase: MissionPhase | None = Field(
        default=None,
        description="The mission phase (planning/launch/active/complete/archived).",
        examples=["active"],
    )
    priority: int | None = Field(
        default=None,
        ge=1,
        le=4,
        description="The mission priority, P0-P3 (1-4).",
        examples=[1],
    )
    launch_date: str | None = Field(
        default=None,
        description="Optional launch date string.",
        examples=["2026-09-01"],
    )


class Book(BookBase):
    """A mission with an ID."""

    id: int = Field(ge=1, description="The unique identifier of the mission.")
    seeded: bool = Field(
        default=False,
        description="True if this is a seeded demo mission that cannot be deleted.",
    )


class BookCreate(BookBase):
    """Created mission, same as BookBase with enforced required fields."""


class BookUpdate(BookBase):
    """PUT mission, all fields optional."""

    mission_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated mission name.",
    )
    commander: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated commander.",
    )
    mission_type: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Updated mission type.",
    )
    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated description.",
    )
    phase: MissionPhase | None = Field(
        default=None,
        description="Updated phase.",
    )
    priority: int | None = Field(
        default=None,
        ge=1,
        le=4,
        description="Updated priority.",
    )
    launch_date: str | None = Field(
        default=None,
        description="Updated launch date string.",
    )
