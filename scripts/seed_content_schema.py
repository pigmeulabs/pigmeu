#!/usr/bin/env python3
"""
Seed script to initialize/update default content schema in MongoDB.

Run with: python3 scripts/seed_content_schema.py
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from src.api.settings import DEFAULT_CONTENT_SCHEMA_NAME, _default_book_review_content_schema_payload
from src.db.connection import get_database


async def seed_content_schema() -> None:
    db = await get_database()
    collection = db["content_schemas"]
    now = datetime.utcnow()

    payload = _default_book_review_content_schema_payload()
    payload["updated_at"] = now

    existing = await collection.find_one({"name": DEFAULT_CONTENT_SCHEMA_NAME, "target_type": "book_review"})
    if existing:
        payload["created_at"] = existing.get("created_at", now)
        await collection.update_one({"_id": existing["_id"]}, {"$set": payload})
        print(f"✅ Content schema updated: {DEFAULT_CONTENT_SCHEMA_NAME}")
        return

    payload.setdefault("created_at", now)
    await collection.insert_one(payload)
    print(f"✅ Content schema created: {DEFAULT_CONTENT_SCHEMA_NAME}")


async def main() -> None:
    print("🌱 Seeding default content schema...")
    await seed_content_schema()
    print("✨ Content schema seed complete!")


if __name__ == "__main__":
    asyncio.run(main())

