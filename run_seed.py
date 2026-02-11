"""
Script temporário para executar o seed de prompts.
"""

import asyncio
from scripts.seed_prompts import seed_prompts


if __name__ == "__main__":
    print("🌱 Executando seed de prompts...")
    asyncio.run(seed_prompts())
    print("✨ Seed concluído!")