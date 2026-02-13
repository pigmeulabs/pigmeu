from pymongo import ASCENDING, DESCENDING, TEXT

from src.db.connection import get_database


async def run_migrations() -> None:
    """Create collections with required indexes."""
    db = await get_database()

    if "submissions" not in await db.list_collection_names():
        await db.create_collection("submissions")
    await db["submissions"].create_index([("status", ASCENDING), ("created_at", DESCENDING)])
    await db["submissions"].create_index([("pipeline_id", ASCENDING), ("created_at", DESCENDING)])
    await db["submissions"].create_index([("title", TEXT), ("author_name", TEXT)])
    await db["submissions"].create_index([("amazon_url", ASCENDING)], unique=True)
    print("✓ submissions")

    if "books" not in await db.list_collection_names():
        await db.create_collection("books")
    await db["books"].create_index([("submission_id", ASCENDING)], unique=True)
    await db["books"].create_index([("extracted.isbn", ASCENDING)], unique=True, sparse=True)
    print("✓ books")

    if "summaries" not in await db.list_collection_names():
        await db.create_collection("summaries")
    await db["summaries"].create_index([("book_id", ASCENDING), ("created_at", DESCENDING)])
    await db["summaries"].create_index([("source_domain", ASCENDING)])
    print("✓ summaries")

    if "knowledge_base" not in await db.list_collection_names():
        await db.create_collection("knowledge_base")
    await db["knowledge_base"].create_index([("book_id", ASCENDING)], sparse=True)
    await db["knowledge_base"].create_index([("submission_id", ASCENDING)], sparse=True)
    print("✓ knowledge_base")

    if "articles" not in await db.list_collection_names():
        await db.create_collection("articles")
    await db["articles"].create_index([("book_id", ASCENDING), ("created_at", DESCENDING)])
    await db["articles"].create_index([("submission_id", ASCENDING), ("created_at", DESCENDING)], sparse=True)
    await db["articles"].create_index([("wordpress_post_id", ASCENDING)], sparse=True)
    print("✓ articles")

    if "articles_drafts" not in await db.list_collection_names():
        await db.create_collection("articles_drafts")
    await db["articles_drafts"].create_index([("article_id", ASCENDING)], unique=True)
    print("✓ articles_drafts")

    if "credentials" not in await db.list_collection_names():
        await db.create_collection("credentials")
    await db["credentials"].create_index([("service", ASCENDING), ("active", ASCENDING)])
    await db["credentials"].create_index([("name", ASCENDING)])
    await db["credentials"].create_index([("service", ASCENDING), ("url", ASCENDING)], sparse=True)
    print("✓ credentials")

    if "prompts" not in await db.list_collection_names():
        await db.create_collection("prompts")
    await db["prompts"].create_index([("name", ASCENDING)], unique=True)
    await db["prompts"].create_index([("purpose", ASCENDING), ("active", ASCENDING)])
    await db["prompts"].create_index([("category", ASCENDING), ("active", ASCENDING)])
    await db["prompts"].create_index([("provider", ASCENDING), ("active", ASCENDING)])
    await db["prompts"].create_index([("model_id", ASCENDING)])
    print("✓ prompts")

    if "content_schemas" not in await db.list_collection_names():
        await db.create_collection("content_schemas")
    await db["content_schemas"].create_index([("name", ASCENDING)], unique=True)
    await db["content_schemas"].create_index([("target_type", ASCENDING), ("active", ASCENDING)])
    await db["content_schemas"].create_index([("updated_at", DESCENDING)])
    print("✓ content_schemas")

    print("\n🎉 All migrations completed!")
