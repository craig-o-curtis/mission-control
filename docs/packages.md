# Packages

This project uses a curated set of Python packages. Below is an explanation of each one, what it does, and why it's included.

## Core Runtime

### [FastAPI](https://fastapi.tiangolo.com/)

The web framework. FastAPI is a modern, high-performance web framework for building APIs with Python 3.14+.

- **What it does:** Handles routing, request parsing, response serialization, and automatic API documentation (Swagger/ReDoc).
- **Why it's used:** Type hints in function signatures are automatically validated and documented. It's async-ready but works fine with sync code too.
- **Key concepts:** Path parameters, query parameters, request bodies, response models, dependency injection.

### [Uvicorn](https://www.uvicorn.org/)

The ASGI (Asynchronous Server Gateway Interface) server. This is what actually runs your FastAPI application and handles incoming HTTP requests.

- **What it does:** Acts as the bridge between the internet and your Python code. It receives HTTP requests, passes them to FastAPI, and sends back responses.
- **Why it's used:** FastAPI is a framework, not a server. Uvicorn is the most popular ASGI server for Python and is built on `uvloop` for high performance.
- **How it runs:** `uvicorn missions_api.main:app --reload` starts the server in development mode with auto-reload.

### [HTTPX](https://www.python-httpx.org/)

The modern HTTP client. Used for making HTTP requests in tests and any client-side code.

- **What it does:** Sends HTTP requests (GET, POST, etc.) to APIs. Supports both sync and async.
- **Why it's used:** Replaces the older `requests` library. It's faster, supports async natively, and is the recommended client for testing FastAPI apps (used with `TestClient`).

## Data Validation & Models

### [Pydantic](https://docs.pydantic.dev/)

The data validation library. FastAPI uses Pydantic under the hood for all request/response validation. Similar to Zod, it validates data at both runtime and compile time. You define the schema and then get both validation and typed results - BaseModel.

- **What it does:** Defines data models with type hints and automatically validates, parses, and serializes data.
- **Why it's used:** Every field in a FastAPI request body or response is validated against Pydantic models. If data doesn't match the schema, FastAPI returns a 422 error automatically.
- **Key concepts:** `BaseModel` for data models, `Field()` for constraints, automatic JSON serialization.

### [SQLAlchemy](https://www.sqlalchemy.org/)

The SQL toolkit and ORM. Used for database interactions.

- **What it does:** Maps Python classes to database tables and provides query building.
- **Why it's used:** Avoids writing raw SQL. Handles connection pooling, query construction, and type mapping between Python and your database.
- **Note:** This project uses SQLModel on top of SQLAlchemy for a more FastAPI-friendly experience.

## Authentication & Security

### [bcrypt](https://bcrypt.readthedocs.io/)

Password hashing. Converts plain-text passwords into irreversible hashed values.

- **What it does:** Hashes passwords using the bcrypt algorithm, which is deliberately slow to resist brute-force attacks.
- **Why it's used:** Never store plain-text passwords. `bcrypt.hashpw()` creates a hash; `bcrypt.checkpw()` verifies a password against a stored hash.

### [passlib](https://passlib.readthedocs.io/)

Password hashing utilities. A wrapper that makes password hashing simpler and more flexible.

- **What it does:** Provides a clean API for hashing and verifying passwords, supporting multiple hashing schemes.
- **Why it's used:** Simplifies the bcrypt workflow with methods like `Context.hash()` and `Context.verify()`.

### [python-jose](https://python-jose.readthedocs.io/)

JSON Web Tokens (JWT). Creates and verifies JWTs for stateless authentication.

- **What it does:** Signs and encodes tokens containing user identity data; verifies token signatures on incoming requests.
- **Why it's used:** Enables token-based auth without storing sessions on the server. The token is sent in the `Authorization` header with each request.

### [cryptography](https://cryptography.readthedocs.io/)

Low-level cryptographic primitives. Provides the building blocks for encryption, hashing, and key management.

- **What it does:** Implements AES, RSA, HMAC, and other cryptographic algorithms.
- **Why it's used:** Used by `python-jose` and other packages under the hood. Included for any direct cryptographic needs.

## Database Drivers

### [psycopg2-binary](https://www.psycopg.org/)

PostgreSQL adapter. Connects Python to PostgreSQL databases.

- **What it does:** Translates Python database calls into PostgreSQL protocol messages.
- **Why it's used:** The standard PostgreSQL driver for Python. The `-binary` variant includes pre-compiled binaries for easier installation.

### [PyMySQL](https://pymysql.readthedocs.io/)

MySQL/MariaDB connector. Connects Python to MySQL databases.

- **What it does:** Pure-Python MySQL client that requires no external dependencies.
- **Why it's used:** Provides MySQL support alongside PostgreSQL. Useful for projects that need to work with both databases.

## Frontend & Templating

### [aiofiles](https://github.com/Tinche/aiofiles)

Async file I/O. Allows file operations without blocking the async event loop.

- **What it does:** Wraps synchronous file operations (`open`, `read`, `write`) in async-compatible functions.
- **Why it's used:** In an async FastAPI app, regular file I/O would block the event loop. `aiofiles` runs file operations in a thread pool instead.

### [Jinja2](https://jinja.palletsprojects.com/)

The templating engine. Generates HTML dynamically from templates.

- **What it does:** Combines templates with data to produce rendered HTML pages.
- **Why it's used:** For serving server-rendered pages when you need more than a static JSON API. Supports template inheritance, filters, and custom tags.

## Development Tools

### [Ruff](https://docs.astral.sh/ruff/)

The fast Python linter and formatter. Replaces flake8, isort, black, and several other tools.

- **What it does:** Checks code for errors, style issues, and best practices. Also formats code to a consistent style.
- **Why it's used:** Written in Rust, it's 10-100x faster than traditional Python linting tools. Single tool for linting (`ruff check`) and formatting (`ruff format`).
- **Commands:**
  - `ruff check` — lint the code
  - `ruff format` — format the code
  - `ruff check --fix` — auto-fix linting issues

### [ty](https://github.com/davidfurlong/ty)

The static type checker. A fast type checker for Python built on top of Ruff's infrastructure.

- **What it does:** Checks that types are used correctly across your codebase — variable assignments, function arguments, return types.
- **Why it's used:** Catches type mismatches before runtime. Much faster than `mypy` while providing similar guarantees.
- **Command:** `ty check` — run type checking

### [pytest](https://docs.pytest.org/)

The testing framework. The most popular Python testing library.

- **What it does:** Discovers and runs test functions, provides fixtures for setup/teardown, and offers rich assertions.
- **Why it's used:** Simple syntax (`assert` statements are inspected automatically), extensive plugin ecosystem, and excellent async support.
- **Commands:**
  - `pytest` — run all tests
  - `pytest -v` — verbose output
  - `pytest tests/test_missions.py` — run specific test file

### [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

Async test support for pytest. Enables testing of async functions and async test fixtures.

- **What it does:** Allows `async def` test functions and provides async fixtures.
- **Why it's used:** FastAPI apps often use async endpoints. This plugin lets you test them directly without wrapping in `asyncio.run()`.

## Package Management

### [uv](https://docs.astral.sh/uv/)

The fast Python package installer and resolver. (Not a dependency — this is the tool you use to manage dependencies.)

- **What it does:** Installs packages, manages virtual environments, and resolves dependencies. Written in Rust for extreme speed.
- **Why it's used:** 10-100x faster than `pip` and `venv` combined. Single tool for creating environments, installing packages, and running scripts.
- **Commands:**
  - `uv venv` — create a virtual environment
  - `uv pip install <package>` — install a package
  - `uv run <script>` — run a script in the project environment
