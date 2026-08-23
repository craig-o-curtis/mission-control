"""FastAPI app factory for tasks API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from tasks_api.database import init_db
from tasks_api.routers import admin, auth, tasks, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    init_db()
    yield


app = FastAPI(
    title="Tasks API",
    description="A simple API to manage a collection of tasks.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(tasks.router)
app.include_router(users.router)


@app.get("/")
def health_check() -> dict[str, str]:
    """Basic liveness check."""
    return {
        "name": "Tasks App",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
