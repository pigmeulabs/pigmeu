#!/usr/bin/env python3
"""
Script to check if prompts already exist in MongoDB.
"""

import asyncio
from src.db.connection import get_database

async def check_prompts():
    """Check if prompts exist in the database."""
    db = await get_database()
    prompts_collection = db["prompts"]

    try:
        count = await prompts_collection.count_documents({})
        print(f"📊 Total prompts in database: {count}")

        if count > 0:
            print("📝 Existing prompts:")
            prompts = await prompts_collection.find().to_list(length=10)
            for i, prompt in enumerate(prompts, 1):
                print(f"   {i}. {prompt['name']} ({prompt['model_id']})")
        else:
            print("⚠️  No prompts found in the database.")

    except Exception as e:
        print(f"❌ Error checking prompts: {e}")
        raise

async def main():
    """Main entry point."""
    print("🔍 Checking existing prompts...")
    try:
        await check_prompts()
    except Exception as e:
        print(f"Failed: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())