import copy
import os
from typing import Annotated, Literal

from fastapi import Body, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from shared.api_utils import is_casefold_match, is_positive_integer

from .path_aliases import (
    CommanderPath,
    MissionIdPath,
    MissionNamePath,
    MissionTypePath,
)
from .query_aliases import (
    CommanderQuery,
    DescriptionQuery,
    MissionNameQuery,
    MissionTypeQuery,
    PhaseQuery,
)

MissionPhase = Literal["planning", "launch", "active", "complete", "archived"]

MISSION_TYPES = ["orbital", "eva", "deep_space", "surface"]


class MissionBase(BaseModel):
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


class Mission(MissionBase):
    """A mission with an ID."""

    id: int = Field(ge=1, description="The unique identifier of the mission.")
    seeded: bool = Field(
        default=False,
        description="True if this is a seeded demo mission that cannot be deleted.",
    )


class MissionCreate(MissionBase):
    """Created mission, same as MissionBase with enforced required fields."""


class MissionUpdate(MissionBase):
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


MissionCreateBody = Annotated[MissionCreate, Body()]
MissionUpdateBody = Annotated[MissionUpdate, Body()]


MISSIONS: dict[int, Mission] = {
    1: Mission(
        id=1,
        mission_name="Artemis Lunar Landing",
        commander="Lovell",
        mission_type="surface",
        description="Crewed lunar landing attempt.",
        phase="active",
        priority=1,
        launch_date="2026-09-01",
    ),
    2: Mission(
        id=2,
        mission_name="Mars Rover Deployment",
        commander="Vasquez",
        mission_type="surface",
        description="Deploy a rover on the Martian surface.",
        phase="launch",
        priority=2,
        launch_date="2027-03-15",
    ),
    3: Mission(
        id=3,
        mission_name="Orbital Telescope",
        commander="Kranz",
        mission_type="orbital",
        description="Deploy a deep-field space telescope.",
        phase="planning",
        priority=3,
        launch_date=None,
    ),
    4: Mission(
        id=4,
        mission_name="EVA Repair Walk",
        commander="Lovell",
        mission_type="eva",
        description="Extra-vehicular activity to repair the array.",
        phase="active",
        priority=1,
        launch_date="2026-08-30",
    ),
    5: Mission(
        id=5,
        mission_name="Deep Space Probe",
        commander="Vasquez",
        mission_type="deep_space",
        description="Launch a probe to the outer system.",
        phase="complete",
        priority=2,
        launch_date="2025-11-10",
    ),
    6: Mission(
        id=6,
        mission_name="Surface Habitat Build",
        commander="Kranz",
        mission_type="surface",
        description="Assemble the lunar surface habitat.",
        phase="archived",
        priority=4,
        launch_date=None,
    ),
}

SEEDED_MISSIONS = [copy.deepcopy(m) for m in MISSIONS.values()]
SEEDED_IDS = set(MISSIONS.keys())


def _with_seeded(mission: Mission) -> Mission:
    """Return a copy of the mission with its `seeded` flag set for the UI."""
    return Mission.model_validate(
        {**mission.model_dump(), "seeded": mission.id in SEEDED_IDS}
    )


app = FastAPI(
    title="Missions API",
    description="A simple API to manage a collection of missions.",
    version="1.0.0",
)

ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    summary="Health check",
    description=(
        "Returns basic information about the API including name, version, and status."
    ),
    response_description="API metadata",
)
def root() -> dict[str, str]:
    """Get API status and metadata."""
    return {
        "name": "Missions API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/missions")
def read_all_missions(
    mission_type: MissionTypeQuery = None,
    commander: CommanderQuery = None,
    mission_name: MissionNameQuery = None,
    description: DescriptionQuery = None,
    phase: PhaseQuery = None,
) -> list[Mission]:
    """
    Retrieve all missions.

    Optionally filter by mission_type, commander, or mission_name (query params).
    """
    filtered = list(MISSIONS.values())

    if mission_type is not None:
        filtered = [
            mission
            for mission in filtered
            if is_casefold_match(mission.mission_type, mission_type)
        ]
    if commander is not None:
        filtered = [
            mission
            for mission in filtered
            if is_casefold_match(mission.commander, commander)
        ]
    if mission_name is not None:
        filtered = [
            mission
            for mission in filtered
            if is_casefold_match(mission.mission_name, mission_name)
        ]
    if description is not None:
        filtered = [
            mission
            for mission in filtered
            if mission.description is not None
            and is_casefold_match(mission.description, description)
        ]
    if phase is not None:
        filtered = [mission for mission in filtered if mission.phase == phase]

    if not filtered:
        raise HTTPException(
            status_code=404,
            detail="No missions found matching the given criteria.",
        )

    return [_with_seeded(m) for m in filtered]


@app.get("/missions/{mission_id}")
def read_mission_by_id(
    mission_id: MissionIdPath,
) -> Mission:
    """
    Fetch a single mission by its ID.

    The ID must be a positive integer.
    """
    if not is_positive_integer(mission_id):
        raise HTTPException(
            status_code=422,
            detail=f"Mission ID must be a positive integer. Received: {mission_id}",
        )
    mission = MISSIONS.get(mission_id)
    if mission is None:
        raise HTTPException(
            status_code=404,
            detail=f"Mission with ID {mission_id} not found.",
        )
    return _with_seeded(mission)


@app.get("/missions/categories/{category}")
def read_missions_by_category(
    category: MissionTypePath,
) -> list[Mission]:
    """
    Fetch all missions of a given mission type.

    The mission type is case-insensitive.
    """
    filtered = [
        mission
        for mission in MISSIONS.values()
        if is_casefold_match(mission.mission_type, category)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No missions found for type: {category}",
        )
    return [_with_seeded(m) for m in filtered]


@app.get("/missions/commanders/{commander}")
def read_missions_by_commander(
    commander: CommanderPath,
) -> list[Mission]:
    """
    Fetch all missions for a given commander.

    The commander name is case-insensitive.
    """
    filtered = [
        mission
        for mission in MISSIONS.values()
        if is_casefold_match(mission.commander, commander)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No missions found for commander: {commander}",
        )
    return [_with_seeded(m) for m in filtered]


@app.get("/missions/names/{name}")
def read_missions_by_name(
    name: MissionNamePath,
) -> list[Mission]:
    """
    Fetch all missions with a given name.

    The mission name is case-insensitive.
    """
    filtered = [
        mission
        for mission in MISSIONS.values()
        if is_casefold_match(mission.mission_name, name)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No missions found with name: {name}",
        )
    return [_with_seeded(m) for m in filtered]


@app.post("/missions", status_code=status.HTTP_201_CREATED)
def create_mission(new_mission: MissionCreateBody) -> Mission:
    """
    Create a new mission.

    The mission must have a unique ID.
    """
    if any(
        is_casefold_match(mission.mission_name, new_mission.mission_name)
        and is_casefold_match(mission.commander, new_mission.commander)
        and is_casefold_match(mission.mission_type, new_mission.mission_type)
        for mission in MISSIONS.values()
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Mission {new_mission.mission_name} commanded by "
            f"{new_mission.commander} already exists.",
        )
    new_mission_id = max(MISSIONS.keys()) + 1
    mission = Mission(
        id=new_mission_id,
        **new_mission.model_dump(),
    )
    MISSIONS[new_mission_id] = mission
    return mission


@app.put("/missions/{mission_id}")
def update_mission_by_id(
    mission_id: MissionIdPath,
    mission_update: MissionUpdateBody,
) -> Mission:
    """
    Update a mission by ID.

    The mission ID must exist.
    """
    if mission_id not in MISSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Mission ID {mission_id} not found.",
        )
    mission = MISSIONS[mission_id]
    update_data = mission_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(mission, field, value)
    return _with_seeded(mission)


@app.delete("/missions/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mission_by_id(
    mission_id: MissionIdPath,
) -> Response:
    """
    Delete a mission by ID.

    The mission ID must exist.
    """
    if mission_id not in MISSIONS:
        raise HTTPException(
            status_code=404,
            detail=f"Mission ID {mission_id} not found.",
        )
    MISSIONS.pop(mission_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/missions/reset", status_code=status.HTTP_200_OK)
def reset_missions() -> dict:
    """
    Restore the seeded missions, discarding any user-created missions.

    Missions are held in memory, so this returns the demo to its original state.
    """
    MISSIONS.clear()
    for mission in copy.deepcopy(SEEDED_MISSIONS):
        MISSIONS[mission.id] = mission
    return {"status": "reset", "count": len(MISSIONS)}
