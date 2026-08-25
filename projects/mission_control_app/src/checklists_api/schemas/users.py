from pydantic import BaseModel, ConfigDict, Field

# File for pydantic models, which are used to validate data
# incoming data is validated against these models


class ReadUserRequest(BaseModel):
    id: int
    username: str
    email: str
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    is_active: bool
    hashed_password: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class ReadUserPublic(BaseModel):
    id: int
    username: str
    email: str
    first_name: str | None
    last_name: str | None
    phone_number: str | None
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    phone_number: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=8, max_length=100)
    role: str | None = Field(default="user", min_length=3, max_length=20)


class UpdateUserRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None, min_length=5, max_length=100)
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    phone_number: str | None = Field(default=None, max_length=20)
    password: str | None = Field(default=None, min_length=8, max_length=100)
    role: str | None = Field(default=None, min_length=3, max_length=20)


class UpdateUserPasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=100)
    new_password: str = Field(min_length=8, max_length=100)
    new_password: str = Field(min_length=8, max_length=100)


class UpdateUserPhoneRequest(BaseModel):
    phone_number: str = Field(min_length=1, max_length=20)
