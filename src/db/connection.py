from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from src.config import settings

_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    """Get or create MongoDB client instance."""
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongodb_uri)
    return _client


async def get_database() -> AsyncIOMotorDatabase:
    """Get or create MongoDB database instance."""
    global _database
    if _database is None:
        client = await get_mongo_client()
        _database = client[settings.mongo_db_name]
    return _database


async def close_mongo_client() -> None:
    """Close MongoDB client connection."""
    global _client, _database
    if _client is not None:
        _client.close()
        _client = None
        _database = None
