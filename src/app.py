from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api import ingest, tasks, settings as settings_router, articles, operations
from src.config import settings
from src.db.connection import close_mongo_client
from src.db.migrations import run_migrations
from src.logger import setup_logger

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    try:
        logger.info("Starting Pigmeu Copilot API")
        await run_migrations()
        logger.info("Database migrations completed")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise

    yield

    try:
        logger.info("Shutting down Pigmeu Copilot API")
        await close_mongo_client()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error("Shutdown error: %s", e)


app = FastAPI(
    title="Pigmeu Copilot API",
    description="Automated technical book review generation and SEO-optimized article publishing",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(ingest.router)
app.include_router(tasks.router)
app.include_router(settings_router.router)
app.include_router(articles.router)
app.include_router(operations.router)

# Serve a minimal web UI under /ui
app.mount("/ui/static", StaticFiles(directory="src/static"), name="static")


@app.get("/ui", tags=["UI"])
async def ui_index():
    """Serve single-page web UI."""
    return FileResponse("src/static/index.html")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": "Pigmeu Copilot API",
        "environment": settings.app_env,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Pigmeu Copilot API",
        "docs": "/docs",
        "openapi_schema": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.app_env == "development",
    )
