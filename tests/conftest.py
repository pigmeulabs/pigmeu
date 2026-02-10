import pytest
import asyncio
from src.config import settings
from src.db.connection import get_database, close_mongo_client
import pymongo


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Get test database connection."""
    db = await get_database()
    # Ensure a clean database for tests
    try:
        await db.client.drop_database(settings.mongo_db_name)
    except Exception:
        pass
    yield db
    # Cleanup would go here


@pytest.fixture(autouse=True)
async def cleanup():
    """Auto-use fixture to cleanup after tests."""
    # Drop database before each test to ensure isolation (use sync pymongo to avoid loop issues)
    try:
        client = pymongo.MongoClient(settings.mongodb_uri)
        client.drop_database(settings.mongo_db_name)
        client.close()
    except Exception:
        pass

    yield

    await close_mongo_client()
