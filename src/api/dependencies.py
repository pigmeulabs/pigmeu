"""
FastAPI dependency injection for database connections and repositories.

This module provides dependency injection for FastAPI routes,
ensuring clean separation of concerns and testability.
"""

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.db.connection import get_database
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    SummaryRepository,
    KnowledgeBaseRepository,
    ArticleRepository,
)


async def get_submission_repo(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SubmissionRepository:
    """Dependency: Get submission repository instance.
    
    Args:
        db: Database connection (injected)
    
    Returns:
        SubmissionRepository instance
    """
    return SubmissionRepository(db)


async def get_book_repo(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> BookRepository:
    """Dependency: Get book repository instance.
    
    Args:
        db: Database connection (injected)
    
    Returns:
        BookRepository instance
    """
    return BookRepository(db)


async def get_summary_repo(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> SummaryRepository:
    """Dependency: Get summary repository instance.
    
    Args:
        db: Database connection (injected)
    
    Returns:
        SummaryRepository instance
    """
    return SummaryRepository(db)


async def get_knowledge_base_repo(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> KnowledgeBaseRepository:
    """Dependency: Get knowledge base repository instance.
    
    Args:
        db: Database connection (injected)
    
    Returns:
        KnowledgeBaseRepository instance
    """
    return KnowledgeBaseRepository(db)


async def get_article_repo(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ArticleRepository:
    """Dependency: Get article repository instance.
    
    Args:
        db: Database connection (injected)
    
    Returns:
        ArticleRepository instance
    """
    return ArticleRepository(db)
