from typing import Annotated

from checklists_api.config import ALGORITHM, SECRET_KEY
from checklists_api.dependencies.db_dep import DbDep
from checklists_api.models.user import User
from fastapi import Depends, HTTPException

# verifies token in the Authorization header of requests
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_bearer)],
    db: DbDep,
) -> User:
    """Get the current user from the token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from None


UserDep = Annotated[User, Depends(get_current_user)]
