import os
from collections.abc import Generator
from typing import Annotated
from urllib.parse import urlparse

import psycopg
import pymysql
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from jose import jwt
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from tasks_api.app import app
from tasks_api.database import Base
from tasks_api.dependencies.db_dep import DbDep, get_db
from tasks_api.dependencies.user_dep import get_current_user
from tasks_api.models.task import Task
from tasks_api.models.user import User
from tasks_api.security import bcrypt_context

_FAKE_HASH = bcrypt_context.hash("fakepass123")
_SECRET = "test-secret-key-for-testing-only"
_ALGO = "HS256"

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:",
)


def _get_connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _get_poolclass(database_url: str):
    if database_url.startswith("sqlite"):
        return StaticPool
    return None


_TEST_TOKEN_CACHE = None


def _make_token(username: str, user_id: int, role: str) -> str:
    global _TEST_TOKEN_CACHE
    if _TEST_TOKEN_CACHE is not None:
        payload = jwt.decode(_TEST_TOKEN_CACHE, _SECRET, algorithms=[_ALGO])
        if payload.get("sub") == username and payload.get("id") == user_id:
            return _TEST_TOKEN_CACHE
    from datetime import UTC, datetime, timedelta

    encode = {
        "sub": username,
        "id": user_id,
        "role": role,
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    _TEST_TOKEN_CACHE = jwt.encode(encode, _SECRET, algorithm=_ALGO)
    return _TEST_TOKEN_CACHE


# ── User fixtures ──────────────────────────────────────────────────


@pytest.fixture
def fake_user() -> User:
    """Create a fake user for testing authenticated endpoints."""
    return User(
        id=1,
        username="testuser",
        email="test@example.com",
        hashed_password=_FAKE_HASH,
        is_active=True,
        role="user",
    )


@pytest.fixture
def fake_second_user() -> User:
    """Create a second fake user for owner isolation tests."""
    return User(
        id=3,
        username="seconduser",
        email="second@example.com",
        hashed_password=_FAKE_HASH,
        is_active=True,
        role="user",
    )


@pytest.fixture
def fake_admin_user() -> User:
    """Create a fake admin user for testing admin endpoints."""
    return User(
        id=2,
        username="adminuser",
        email="admin@example.com",
        hashed_password=_FAKE_HASH,
        is_active=True,
        role="admin",
    )


# ── Task fixtures ──────────────────────────────────────────────────


@pytest.fixture
def fake_task(fake_user: User) -> Task:
    """Create a default task owned by fake_user."""
    return Task(
        title="Test Task",
        description="A test task.",
        priority=1,
        completed=False,
        owner_id=fake_user.id,
    )


@pytest.fixture
def fake_admin_task(fake_admin_user: User) -> Task:
    """Create a default task owned by fake_admin_user."""
    return Task(
        title="Admin Test Task",
        description="A task for admin testing.",
        priority=2,
        completed=False,
        owner_id=fake_admin_user.id,
    )


@pytest.fixture
def fake_second_user_task(fake_second_user: User) -> Task:
    """Create a task owned by fake_second_user for isolation tests."""
    return Task(
        title="Other User's Task",
        description="Owned by second user.",
        priority=1,
        completed=False,
        owner_id=fake_second_user.id,
    )


# ── Database fixtures ─────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine (session-scoped for efficiency)."""
    try:
        engine = create_engine(
            TEST_DATABASE_URL,
            connect_args=_get_connect_args(TEST_DATABASE_URL),
            poolclass=_get_poolclass(TEST_DATABASE_URL),
        )
    except ImportError as e:
        raise ImportError(
            f"Cannot create test engine for {TEST_DATABASE_URL!r}. "
            "Make sure the DB driver is installed: "
            "psycopg for Postgres, pymysql for MySQL. "
            f"Original error: {e}"
        ) from e
    yield engine
    engine.dispose()


def _ensure_test_database(database_url: str) -> None:
    """Create the test database if it doesn't exist (MySQL/Postgres only)."""
    if database_url.startswith("mysql"):
        _ensure_mysql_database()
    elif database_url.startswith("postgresql"):
        _ensure_postgres_database()


def _ensure_mysql_database() -> None:

    parsed = urlparse(TEST_DATABASE_URL)
    conn = pymysql.connect(
        host=parsed.hostname or os.getenv("TEST_MYSQL_HOST", "localhost"),
        port=parsed.port or int(os.getenv("TEST_MYSQL_PORT", "3306")),
        user=parsed.username or os.getenv("TEST_MYSQL_USER", "root"),
        password=parsed.password or os.getenv("TEST_MYSQL_PASSWORD", ""),
    )
    try:
        db_name = parsed.path.lstrip("/") or os.getenv(
            "TEST_MYSQL_DB", "tasks_application_database_test"
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")
        conn.commit()
    finally:
        conn.close()


def _ensure_postgres_database() -> None:
    parsed = urlparse(TEST_DATABASE_URL)
    user = parsed.username or os.getenv("TEST_POSTGRES_USER", "postgres")
    password = parsed.password or os.getenv("TEST_POSTGRES_PASSWORD", "")
    host = parsed.hostname or os.getenv("TEST_POSTGRES_HOST", "localhost")
    port = parsed.port or int(os.getenv("TEST_POSTGRES_PORT", "5432"))
    db_name = parsed.path.lstrip("/") or os.getenv(
        "TEST_POSTGRES_DB", "TasksApplicationDatabase_test"
    )

    conn = psycopg.connect(
        host=host, port=port, user=user, password=password, dbname="postgres"
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cursor.fetchone():
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
                )
    finally:
        conn.close()


@pytest.fixture(scope="session")
def test_tables(test_engine):
    """Create tables once per test session, drop them at the end."""
    _ensure_test_database(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=test_engine, checkfirst=True)
    yield
    Base.metadata.drop_all(bind=test_engine, checkfirst=True)


@pytest.fixture
def test_session(test_engine, test_tables):
    """Create a test database session and clear all tables before each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    session = TestingSessionLocal()

    is_mysql = TEST_DATABASE_URL.startswith("mysql")
    is_postgres = TEST_DATABASE_URL.startswith("postgresql")

    # Disable foreign key checks for MySQL
    if is_mysql:
        session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))

    # Clear all tables
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    # Reset auto-increment counters
    if is_mysql:
        for table in Base.metadata.sorted_tables:
            session.execute(text(f"ALTER TABLE {table.name} AUTO_INCREMENT = 1"))

        session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        session.commit()
    # For PG we need to reset the sequence for each table
    elif is_postgres:
        for table in Base.metadata.sorted_tables:
            session.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence("
                    f"'{table.name}', 'id'), 1, false)"
                )
            )
        session.commit()
    # yield session means that
    yield session
    session.close()


# ── Client fixtures ────────────────────────────────────────────────


@pytest.fixture
def api_client(fake_user: User, fake_task: Task, test_session) -> Generator[TestClient]:
    """Client authenticated as a regular user with a default task in DB."""
    test_session.add(fake_user)
    test_session.flush()
    test_session.add(fake_task)
    test_session.commit()

    def override_get_db():
        yield test_session

    def override_get_current_user(
        db: Annotated[DbDep, Depends(get_db)],
    ) -> User | None:
        return db.query(User).filter(User.id == fake_user.id).first()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(
    fake_admin_user: User, fake_admin_task: Task, test_session
) -> Generator[TestClient]:
    """Client authenticated as an admin user with a default admin task in DB."""
    test_session.add(fake_admin_user)
    test_session.flush()
    test_session.add(fake_admin_task)
    test_session.commit()

    def override_get_db():
        yield test_session

    def override_get_current_user(
        db: Annotated[DbDep, Depends(get_db)],
    ) -> User | None:
        return db.query(User).filter(User.id == fake_admin_user.id).first()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def no_auth_client(test_session) -> Generator[TestClient]:
    """Client with no authentication override — for testing auth/login endpoints."""
    user = User(
        id=99,
        username="authtest",
        email="authtest@example.com",
        hashed_password=_FAKE_HASH,
        is_active=True,
        role="user",
    )
    test_session.add(user)
    test_session.flush()
    test_session.commit()

    app.state.test_token = _make_token("authtest", 99, "user")

    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def isolation_client(
    fake_user: User,
    fake_second_user: User,
    fake_second_user_task: Task,
    test_session,
) -> Generator[TestClient]:
    """Client authenticated as user 1, but DB has a task owned by user 2."""
    test_session.add(fake_second_user)
    test_session.flush()
    test_session.add(fake_second_user_task)
    test_session.commit()

    def override_get_db():
        yield test_session

    def override_get_current_user() -> User:
        return fake_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield TestClient(app)
    app.dependency_overrides.clear()


def _db_label() -> str:
    if TEST_DATABASE_URL.startswith("postgresql"):
        return "POSTGRES"
    if TEST_DATABASE_URL.startswith("mysql"):
        return "MYSQL"
    return "SQLITE"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Shows which db was used in the test run."""
    label = _db_label()
    print(f"\n*********** {label} ***************")
    print(f"TEST_DATABASE_URL={TEST_DATABASE_URL!r}\n")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Shows which db was used in the test run."""
    print(f"\n*********** {_db_label()} DONE ***************\n")
