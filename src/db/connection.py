from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import asyncio
from src.config import settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None
_loop: Optional[asyncio.AbstractEventLoop] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client instance."""
    global _client, _database, _loop
    current_loop = asyncio.get_running_loop()

    # Motor client is bound to the event loop used on first access.
    # Celery tasks use asyncio.run() per task, so we must recreate client when loop changes.
    if _client is not None and (_loop is None or _loop.is_closed() or _loop is not current_loop):
        _client.close()
        _client = None
        _database = None
        _loop = None

    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
        _loop = current_loop
    return _client


async def get_database() -> AsyncIOMotorDatabase:
    """Get or create MongoDB database instance."""
    global _database, _loop
    current_loop = asyncio.get_running_loop()

    # Rebind db handle when current loop differs from the one that created it.
    if _database is not None and (_loop is None or _loop.is_closed() or _loop is not current_loop):
        _database = None

    if _database is None:
        client = await get_mongo_client()
        _database = client[settings.mongo_db_name]
        _loop = current_loop
    return _database


async def get_db() -> AsyncIOMotorDatabase:
    """Backward-compatible alias used by worker modules."""
    return await get_database()


async def close_mongo_client() -> None:
    """Close MongoDB client connection."""
    global _client, _database, _loop
    if _client is not None:
        _client.close()
        _client = None
        _database = None
        _loop = None
