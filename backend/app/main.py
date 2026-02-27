from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.database import init_db
from app.middleware.cors import setup_cors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Initializing database...")
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
    
    print("Application started")
    yield
    
    # Shutdown
    print("Application shutdown")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

setup_cors(app, settings.get_cors_origins())


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status indicator
    """
    return {"status": "healthy"}


# TODO: Include API v1 router
# from app.api.v1 import api_router
# app.include_router(api_router, prefix=settings.API_V1_PREFIX)
