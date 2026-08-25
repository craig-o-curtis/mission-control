"""FastAPI app factory for checklists API."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from checklists_api.bootstrap import ensure_seed_data
from checklists_api.database import init_db
from checklists_api.routers import admin, auth, checklists, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    init_db()
    ensure_seed_data()
    yield


app = FastAPI(
    title="Checklist API",
    description="A simple API to manage mission checklist items.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(checklists.router)
app.include_router(users.router)

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


@app.get("/")
def health_check() -> dict[str, str]:
    """Basic liveness check."""
    return {
        "name": "Checklist App",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }
