from typing import Annotated

from fastapi import Path

MissionIdPath = Annotated[
    int,
    Path(ge=1, description="The ID of the mission to retrieve."),
]

MissionTypePath = Annotated[
    str,
    Path(max_length=50, description="The mission type to filter missions by."),
]

CommanderPath = Annotated[
    str,
    Path(max_length=100, description="The commander to filter missions by."),
]

MissionNamePath = Annotated[
    str,
    Path(max_length=100, description="The mission name to filter missions by."),
]
