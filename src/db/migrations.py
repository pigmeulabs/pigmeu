from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT
from src.db.connection import get_database


async def run_migrations() -> None:
    """Create all collections with proper indexes."""
    db = await get_database()
    
    # Submissions collection
    if "submissions" not in await db.list_collection_names():
        await db.create_collection("submissions")
    await db["submissions"].create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)]
    )
    await db["submissions"].create_index(
        [("title", TEXT), ("author_name", TEXT)]
    )
    print("✓ submissions")
    
    # Books collection
    if "books" not in await db.list_collection_names():
        await db.create_collection("books")
    await db["books"].create_index([("submission_id", ASCENDING)])
    await db["books"].create_index(
        [("isbn", ASCENDING)], unique=True, sparse=True
    )
    print("✓ books")
    
    # Summaries collection
    if "summaries" not in await db.list_collection_names():
        await db.create_collection("summaries")
    await db["summaries"].create_index([("book_id", ASCENDING)])
    print("✓ summaries")
    
    # Knowledge base collection
    if "knowledge_base" not in await db.list_collection_names():
        await db.create_collection("knowledge_base")
    await db["knowledge_base"].create_index([("book_id", ASCENDING)])
    print("✓ knowledge_base")
    
    # Articles collection
    if "articles" not in await db.list_collection_names():
        await db.create_collection("articles")
    await db["articles"].create_index(
        [("book_id", ASCENDING), ("created_at", DESCENDING)]
    )
    print("✓ articles")
    
    # Articles drafts collection
    if "articles_drafts" not in await db.list_collection_names():
        await db.create_collection("articles_drafts")
    await db["articles_drafts"].create_index([("article_id", ASCENDING)])
    print("✓ articles_drafts")
    
    # Credentials collection
    if "credentials" not in await db.list_collection_names():
        await db.create_collection("credentials")
    await db["credentials"].create_index(
        [("user_id", ASCENDING), ("service", ASCENDING)]
    )
    print("✓ credentials")
    
    # Prompts collection
    if "prompts" not in await db.list_collection_names():
        await db.create_collection("prompts")
    await db["prompts"].create_index([("name", ASCENDING)], unique=True)
    await db["prompts"].create_index([("model_id", ASCENDING)])
    print("✓ prompts")
    
    print("\n🎉 All migrations completed!")
