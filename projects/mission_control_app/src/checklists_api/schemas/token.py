from pydantic import BaseModel

# File for pydantic models


class Token(BaseModel):
    access_token: str
    token_type: str
