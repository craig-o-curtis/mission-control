from pydantic import BaseModel, Field

# Pydantic models


class BookBase(BaseModel):
    # No custom __init__ needed — Pydantic handles initialization, validation,
    # and serialization automatically. Fields are populated from keyword arguments
    # and validated against their type annotations and Field() constraints.
    """Shared fields for all book models."""

    title: str = Field(
        min_length=2,
        max_length=100,
        description="The title of the book.",
        examples=["Amazing Book Title"],
    )
    author: str = Field(
        min_length=2,
        max_length=100,
        description="The author of the book.",
        examples=["John Doe"],
    )
    category: str = Field(
        min_length=2,
        max_length=50,
        description="The category or genre of the book.",
        examples=["Fiction"],
    )
    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="The description of the book.",
        examples=["A book about amazing things."],
    )
    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="The rating of the book.",
        examples=[3],
    )


class Book(BookBase):
    """A book with an ID."""

    id: int = Field(ge=1, description="The unique identifier of the book.")
    seeded: bool = Field(
        default=False,
        description="True if this is a seeded demo book that cannot be deleted.",
    )


class BookCreate(BookBase):
    """Created book, same as BookBase with enforced required fields"""

    pass


class BookUpdate(BookBase):
    "PUT Book, all fields optional"

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated title of the book.",
    )
    author: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated author of the book.",
    )
    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Updated category or genre of the book.",
    )
    description: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Updated description of the book.",
    )
    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Updated rating of the book.",
    )
