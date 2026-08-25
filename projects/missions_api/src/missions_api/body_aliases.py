from typing import Annotated

from fastapi import Body

from .missions import MissionCreate, MissionUpdate

MissionCreateBody = Annotated[MissionCreate, Body()]
MissionUpdateBody = Annotated[MissionUpdate, Body()]
