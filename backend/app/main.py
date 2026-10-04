from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.provenance import router as provenance_router
from app.db import Base, engine

# Import models before create_all().
# This registers Artifact with SQLAlchemy metadata.
from app.models.artifact import Artifact  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup/shutdown lifecycle.
    """

    # MVP schema initialization.
    Base.metadata.create_all(
        bind=engine
    )

    yield

    # SQLAlchemy engine manages its own pool.
    engine.dispose()


app = FastAPI(
    title="ModelLedger API",
    description=(
        "Cryptographically verifiable AI provenance "
        "verification using C2PA and SHA-256."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    provenance_router
)


@app.get("/")
def root():
    return {
        "service": "ModelLedger",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT 1")
            )

        return {
            "status": "ok",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "degraded",
            "database": "disconnected",
        }