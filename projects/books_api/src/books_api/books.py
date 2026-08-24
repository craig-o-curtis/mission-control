import copy
import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from shared.api_utils import is_casefold_match, is_positive_integer

from .body_aliases import BookCreateBody, BookUpdateBody
from .mock_data import BOOKS
from .models import Book
from .path_aliases import (
    AuthorPath,
    BookIdPath,
    CategoryPath,
    TitlePath,
)
from .query_aliases import (
    CommanderQuery,
    DescriptionQuery,
    MissionNameQuery,
    MissionTypeQuery,
    PhaseQuery,
)

# Snapshot of the original seeded missions so we can restore them on reset.
SEEDED_BOOKS = [copy.deepcopy(b) for b in BOOKS.values()]
SEEDED_IDS = set(BOOKS.keys())


def _with_seeded(book: Book) -> Book:
    """Return a copy of the mission with its `seeded` flag set for the UI."""
    return Book.model_validate({**book.model_dump(), "seeded": book.id in SEEDED_IDS})


app = FastAPI(
    title="Books API",
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

## Read Endpoints


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
        "name": "Books API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/books")
def read_all_books(
    mission_type: MissionTypeQuery = None,
    commander: CommanderQuery = None,
    mission_name: MissionNameQuery = None,
    description: DescriptionQuery = None,
    phase: PhaseQuery = None,
) -> list[Book]:
    """
    Retrieve all missions.

    Optionally filter by mission_type, commander, or mission_name (query params).
    """
    filtered = list(BOOKS.values())

    if mission_type is not None:
        filtered = [
            book
            for book in filtered
            if is_casefold_match(book.mission_type, mission_type)
        ]
    if commander is not None:
        filtered = [
            book for book in filtered if is_casefold_match(book.commander, commander)
        ]
    if mission_name is not None:
        filtered = [
            book
            for book in filtered
            if is_casefold_match(book.mission_name, mission_name)
        ]
    if description is not None:
        filtered = [
            book
            for book in filtered
            if book.description is not None
            and is_casefold_match(book.description, description)
        ]
    if phase is not None:
        filtered = [book for book in filtered if book.phase == phase]

    if not filtered:
        raise HTTPException(
            status_code=404,
            detail="No missions found matching the given criteria.",
        )

    return [_with_seeded(b) for b in filtered]


@app.get("/books/{book_id}")
def read_book_by_id(
    book_id: BookIdPath,
) -> Book:
    """
    Fetch a single mission by its ID.

    The ID must be a positive integer.
    """
    if not is_positive_integer(book_id):
        raise HTTPException(
            status_code=422,
            detail=f"Mission ID must be a positive integer. Received: {book_id}",
        )
    book = BOOKS.get(book_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail=f"Mission with ID {book_id} not found.",
        )
    return _with_seeded(book)


@app.get("/books/categories/{category}")
def read_books_by_category(
    category: CategoryPath,
) -> list[Book]:
    """
    Fetch all missions of a given mission type.

    The mission type is case-insensitive.
    """
    filtered = [
        book
        for book in BOOKS.values()
        if is_casefold_match(book.mission_type, category)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No missions found for type: {category}",
        )
    return [_with_seeded(b) for b in filtered]


@app.get("/books/authors/{author}")
def read_books_by_author(
    author: AuthorPath,
) -> list[Book]:
    """
    Fetch all missions for a given commander.

    The commander name is case-insensitive.
    """
    filtered = [
        book for book in BOOKS.values() if is_casefold_match(book.commander, author)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No missions found for commander: {author}",
        )
    return [_with_seeded(b) for b in filtered]


@app.get("/books/titles/{title}")
def read_books_by_title(
    title: TitlePath,
) -> list[Book]:
    """
    Fetch all missions with a given name.

    The mission name is case-insensitive.
    """
    filtered = [
        book for book in BOOKS.values() if is_casefold_match(book.mission_name, title)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No missions found with name: {title}",
        )
    return [_with_seeded(b) for b in filtered]


## Create Endpoint


@app.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(new_book: BookCreateBody) -> Book:
    """
    Create a new mission.

    The mission must have a unique ID.
    """
    # Ensure this is not a repeat - check key vals to see not a duplicate
    if any(
        is_casefold_match(book.mission_name, new_book.mission_name)
        and is_casefold_match(book.commander, new_book.commander)
        and is_casefold_match(book.mission_type, new_book.mission_type)
        for book in BOOKS.values()
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Mission {new_book.mission_name} commanded by "
            f"{new_book.commander} already exists.",
        )
    # Create a new mission with a unique ID
    new_book_id = max(BOOKS.keys()) + 1
    book = Book(
        id=new_book_id,
        **new_book.model_dump(),
    )
    BOOKS[new_book_id] = book
    return book


## Update Request


@app.put("/books/{book_id}")
def update_book_by_id(
    book_id: BookIdPath,
    book_update: BookUpdateBody,
) -> Book:
    """
    Update a mission by ID.

    The mission ID must exist.
    """
    if book_id not in BOOKS:
        raise HTTPException(
            status_code=404,
            detail=f"Mission ID {book_id} not found.",
        )
    # The targeted mission, op below mutates/updates
    book = BOOKS[book_id]
    # model_dump in pydantic serializes model instance into dict.
    # exclude_unset=True means that if a field is not set in the request body,
    # it will not be updated - i.e. if an undefined is passed from the FE.
    # FE passing `null` will be properly converted to None.
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)
    return _with_seeded(book)


## Delete Request
@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_by_id(
    book_id: BookIdPath,
) -> Response:
    """
    Delete a mission by ID.

    The mission ID must exist.
    """
    if book_id not in BOOKS:
        raise HTTPException(
            status_code=404,
            detail=f"Mission ID {book_id} not found.",
        )
    BOOKS.pop(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


## Reset Request
@app.post("/books/reset", status_code=status.HTTP_200_OK)
def reset_books() -> dict:
    """
    Restore the seeded missions, discarding any user-created missions.

    Missions are held in memory, so this returns the demo to its original state.
    """
    BOOKS.clear()
    for book in copy.deepcopy(SEEDED_BOOKS):
        BOOKS[book.id] = book
    return {"status": "reset", "count": len(BOOKS)}
