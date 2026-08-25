from typing import Annotated

from fastapi import Query

MissionNameQuery = Annotated[
    str | None,
    Query(max_length=100, description="The mission name to filter missions by."),
]

CommanderQuery = Annotated[
    str | None,
    Query(max_length=100, description="The commander to filter missions by."),
]

MissionTypeQuery = Annotated[
    str | None,
    Query(max_length=50, description="The mission type to filter missions by."),
]

DescriptionQuery = Annotated[
    str | None,
    Query(max_length=100, description="The description to filter missions by."),
]

PhaseQuery = Annotated[
    str | None,
    Query(
        description="The phase to filter missions by "
        "(planning/launch/active/complete/archived)."
    ),
]
