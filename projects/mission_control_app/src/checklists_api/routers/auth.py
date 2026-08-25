from datetime import timedelta
from typing import Annotated

from checklists_api.dependencies.db_dep import DbDep
from checklists_api.schemas.token import Token
from checklists_api.security import authenticate_user, create_access_token
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbDep,
):
    """Login for access token."""
    user = authenticate_user(form_data.username, form_data.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user.",
        )
    user_id = user.id
    user_role = user.role
    token = create_access_token(
        form_data.username, user_id, user_role, timedelta(minutes=20)
    )
    return Token(access_token=token, token_type="bearer")
