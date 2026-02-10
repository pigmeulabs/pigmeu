import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.migrations import run_migrations
from src.db.connection import close_mongo_client


async def main():
    """Run database migrations."""
    try:
        print("🚀 Starting migrations...\n")
        await run_migrations()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await close_mongo_client()


if __name__ == "__main__":
    asyncio.run(main())
