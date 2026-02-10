from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import logging
from src.config import settings
from src.db.connection import close_mongo_client
from src.db.migrations import run_migrations
from src.logger import setup_logger
from src.api import ingest, tasks

# Setup logging
setup_logger()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    try:
        logger.info("🚀 Starting Pigmeu Copilot API")
        await run_migrations()
        logger.info("✓ Database migrations completed")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown
    try:
        logger.info("🛑 Shutting down Pigmeu Copilot API")
        await close_mongo_client()
        logger.info("✓ Database connection closed")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")


app = FastAPI(
    title="Pigmeu Copilot API",
    description="Automated technical book review generation and SEO-optimized article publishing",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(ingest.router)
app.include_router(tasks.router)


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
