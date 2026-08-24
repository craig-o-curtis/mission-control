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
    AuthorQuery,
    CategoryQuery,
    DescriptionQuery,
    RatingQuery,
    TitleQuery,
)

app = FastAPI(
    title="Books API",
    description="A simple API to manage a collection of books.",
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
    category: CategoryQuery = None,
    author: AuthorQuery = None,
    title: TitleQuery = None,
    description: DescriptionQuery = None,
    rating: RatingQuery = None,
) -> list[Book]:
    """
    Retrieve all books.

    Optionally allow filtering by category, author, or title via query params
    """
    filtered = list(BOOKS.values())

    if category is not None:
        filtered = [
            book for book in filtered if is_casefold_match(book.category, category)
        ]
    if author is not None:
        filtered = [book for book in filtered if is_casefold_match(book.author, author)]
    if title is not None:
        filtered = [book for book in filtered if is_casefold_match(book.title, title)]
    if description is not None:
        filtered = [
            book
            for book in filtered
            # need to check first if description is not None
            if book.description is not None
            and is_casefold_match(book.description, description)
        ]
    if rating is not None:
        filtered = [book for book in filtered if book.rating == rating]

    if not filtered:
        raise HTTPException(
            status_code=404,
            detail="No books found matching the given criteria.",
        )

    return filtered


@app.get("/books/{book_id}")
def read_book_by_id(
    book_id: BookIdPath,
) -> Book:
    """
    Fetch a single book by its ID.

    The ID must be a positive integer.
    """
    if not is_positive_integer(book_id):
        raise HTTPException(
            status_code=422,
            detail=f"Book ID must be a positive integer. Received: {book_id}",
        )
    book = BOOKS.get(book_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail=f"Book with ID {book_id} not found.",
        )
    return book


@app.get("/books/categories/{category}")
def read_books_by_category(
    category: CategoryPath,
) -> list[Book]:
    """
    Fetch all books in a given category.

    The category name is case-sensitive.
    """
    filtered = [
        book for book in BOOKS.values() if is_casefold_match(book.category, category)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No books found in category: {category}",
        )
    return filtered


# read_books_by_author
@app.get("/books/authors/{author}")
def read_books_by_author(
    author: AuthorPath,
) -> list[Book]:
    """
    Fetch all books in a given author.

    The author name is case-sensitive.
    """
    filtered = [
        book for book in BOOKS.values() if is_casefold_match(book.author, author)
    ]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No books found in author: {author}",
        )
    return filtered


# get book by title
@app.get("/books/titles/{title}")
def read_books_by_title(
    title: TitlePath,
) -> list[Book]:
    """
    Fetch all books in a given title.

    The title name is case-sensitive.
    """
    filtered = [book for book in BOOKS.values() if is_casefold_match(book.title, title)]
    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No books found in title: {title}",
        )
    return filtered


# Pydantic definitions


## Create Endpoint


@app.post("/books", status_code=status.HTTP_201_CREATED)
def create_book(new_book: BookCreateBody) -> Book:
    """
    Create a new book.

    The book must have a unique ID.
    """
    # Ensure this is not a repeat - check all key vals to see not a duplicate
    if any(
        is_casefold_match(book.title, new_book.title)
        and is_casefold_match(book.author, new_book.author)
        and is_casefold_match(book.category, new_book.category)
        for book in BOOKS.values()
    ):
        raise HTTPException(
            status_code=409,
            detail=f"Book {new_book.title} by {new_book.author} already exists.",
        )
    # Create a new book with a unique ID
    new_book_id = max(BOOKS.keys()) + 1
    book = Book(
        id=new_book_id,
        # title=new_book.title,
        # author=new_book.author,
        # category=new_book.category,
        # description=new_book.description,
        # rating=new_book.rating,
        # **new_book.dict(), was changed to .model_dump() in version ...
        # Or spread with a copy, model_dump() copies the model into a dict
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
    Update a book by ID.

    The book ID must exist.
    """
    if book_id not in BOOKS:
        raise HTTPException(
            status_code=404,
            detail=f"Book ID {book_id} not found.",
        )
    # The targeted book, op below mutates/updates
    book = BOOKS[book_id]
    # model_dump in pydantic serializes model instance into dict
    # it is replacement for the old .dict()
    # exclude_unset=True means that if a field is not set in the request body,
    # it will not be updated - i.e. if an undefined is passed from the FE
    # FE passing `null` will be properly converted to None
    update_data = book_update.model_dump(exclude_unset=True)
    # The .items() method returns a view object that displays a list
    # of a given dictionary's key-value tuple pair.
    for field, value in update_data.items():
        # if value is not None: # enabling this prevents nulling out values
        setattr(book, field, value)
        # if returning updated item, status code should be 200, easy to debug, payload
        # if returning null, status code should be 204, hard to debug, big payload
    return book


## Delete Request
@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book_by_id(
    book_id: BookIdPath,
) -> Response:
    """
    Delete a book by ID.

    The book ID must exist.
    """
    if book_id not in BOOKS:
        raise HTTPException(
            status_code=404,
            detail=f"Book ID {book_id} not found.",
        )
    BOOKS.pop(book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
