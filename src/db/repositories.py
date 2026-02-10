"""
Database repository layer for CRUD operations on MongoDB collections.

This module provides high-level operations for interacting with MongoDB
collections, abstracting away low-level driver details.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from src.models.enums import SubmissionStatus, ArticleStatus


class SubmissionRepository:
    """Repository for submission collection operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository with database instance.
        
        Args:
            db: Motor AsyncIOMotorDatabase instance
        """
        self.collection = db["submissions"]
    
    async def create(
        self,
        title: str,
        author_name: str,
        amazon_url: str,
        goodreads_url: Optional[str] = None,
        author_site: Optional[str] = None,
        other_links: Optional[List[str]] = None,
    ) -> str:
        """Create a new submission.
        
        Args:
            title: Book title
            author_name: Author name
            amazon_url: Amazon product URL
            goodreads_url: Goodreads book URL (optional)
            author_site: Author's personal website (optional)
            other_links: List of additional relevant links (optional)
        
        Returns:
            submission_id as string
        """
        document = {
            "title": title,
            "author_name": author_name,
            "amazon_url": str(amazon_url),
            "goodreads_url": str(goodreads_url) if goodreads_url else None,
            "author_site": str(author_site) if author_site else None,
            "other_links": [str(url) for url in (other_links or [])],
            "status": SubmissionStatus.PENDING_SCRAPE.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def get_by_id(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get submission by ID.
        
        Args:
            submission_id: Submission ObjectId as string
        
        Returns:
            Submission document or None if not found
        """
        try:
            return await self.collection.find_one(
                {"_id": ObjectId(submission_id)}
            )
        except Exception:
            return None
    
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], int]:
        """List all submissions with pagination.
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            status: Filter by status (optional)
        
        Returns:
            Tuple of (submissions list, total count)
        """
        query = {}
        if status:
            query["status"] = status
        
        total = await self.collection.count_documents(query)
        
        submissions = await self.collection.find(query).skip(skip).limit(limit).to_list(limit)
        
        return submissions, total
    
    async def update_status(self, submission_id: str, status: SubmissionStatus) -> bool:
        """Update submission status.
        
        Args:
            submission_id: Submission ObjectId as string
            status: New status
        
        Returns:
            True if updated, False if not found
        """
        result = await self.collection.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "status": status.value,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        return result.modified_count > 0
    
    async def check_duplicate(self, amazon_url: str) -> Optional[str]:
        """Check if submission with same Amazon URL already exists.
        
        Args:
            amazon_url: Amazon product URL
        
        Returns:
            submission_id if duplicate found, None otherwise
        """
        doc = await self.collection.find_one({"amazon_url": str(amazon_url)})
        return str(doc["_id"]) if doc else None


class BookRepository:
    """Repository for book collection operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository with database instance.
        
        Args:
            db: Motor AsyncIOMotorDatabase instance
        """
        self.collection = db["books"]
    
    async def create_or_update(
        self,
        submission_id: str,
        extracted: Dict[str, Any],
    ) -> str:
        """Create or update book metadata.
        
        Args:
            submission_id: Reference to submission
            extracted: Extracted metadata dictionary
        
        Returns:
            book_id as string
        """
        document = {
            "submission_id": ObjectId(submission_id),
            "extracted": extracted,
            "last_updated": datetime.utcnow(),
        }
        
        # Try to find existing book for this submission
        existing = await self.collection.find_one(
            {"submission_id": ObjectId(submission_id)}
        )
        
        if existing:
            # Update existing
            result = await self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": document},
            )
            return str(existing["_id"])
        else:
            # Create new
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
    
    async def get_by_submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """Get book by submission ID.
        
        Args:
            submission_id: Submission ObjectId as string
        
        Returns:
            Book document or None if not found
        """
        try:
            return await self.collection.find_one(
                {"submission_id": ObjectId(submission_id)}
            )
        except Exception:
            return None
    
    async def get_by_id(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get book by ID.
        
        Args:
            book_id: Book ObjectId as string
        
        Returns:
            Book document or None if not found
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(book_id)})
        except Exception:
            return None


class SummaryRepository:
    """Repository for summary collection operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository with database instance.
        
        Args:
            db: Motor AsyncIOMotorDatabase instance
        """
        self.collection = db["summaries"]
    
    async def create(
        self,
        book_id: str,
        source_url: str,
        summary_text: str,
        topics: Optional[List[str]] = None,
    ) -> str:
        """Create a new summary.
        
        Args:
            book_id: Reference to book
            source_url: URL that was summarized
            summary_text: Summary content
            topics: Extracted topics/keywords (optional)
        
        Returns:
            summary_id as string
        """
        document = {
            "book_id": ObjectId(book_id),
            "source_url": str(source_url),
            "summary_text": summary_text,
            "topics": topics or [],
            "created_at": datetime.utcnow(),
        }
        
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def get_by_book(self, book_id: str) -> List[Dict[str, Any]]:
        """Get all summaries for a book.
        
        Args:
            book_id: Book ObjectId as string
        
        Returns:
            List of summary documents
        """
        try:
            return await self.collection.find(
                {"book_id": ObjectId(book_id)}
            ).to_list(None)
        except Exception:
            return []


class KnowledgeBaseRepository:
    """Repository for knowledge_base collection operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository with database instance.
        
        Args:
            db: Motor AsyncIOMotorDatabase instance
        """
        self.collection = db["knowledge_base"]
    
    async def create_or_update(
        self,
        book_id: str,
        markdown_content: str,
        topics_index: Optional[List[str]] = None,
    ) -> str:
        """Create or update knowledge base.
        
        Args:
            book_id: Reference to book
            markdown_content: Structured markdown knowledge base
            topics_index: Indexed topics for search (optional)
        
        Returns:
            kb_id as string
        """
        document = {
            "book_id": ObjectId(book_id),
            "markdown_content": markdown_content,
            "topics_index": topics_index or [],
            "created_at": datetime.utcnow(),
        }
        
        # Check if exists
        existing = await self.collection.find_one(
            {"book_id": ObjectId(book_id)}
        )
        
        if existing:
            result = await self.collection.update_one(
                {"_id": existing["_id"]},
                {"$set": document},
            )
            return str(existing["_id"])
        else:
            result = await self.collection.insert_one(document)
            return str(result.inserted_id)
    
    async def get_by_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get knowledge base for a book.
        
        Args:
            book_id: Book ObjectId as string
        
        Returns:
            Knowledge base document or None if not found
        """
        try:
            return await self.collection.find_one(
                {"book_id": ObjectId(book_id)}
            )
        except Exception:
            return None


class ArticleRepository:
    """Repository for article collection operations."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize repository with database instance.
        
        Args:
            db: Motor AsyncIOMotorDatabase instance
        """
        self.collection = db["articles"]
    
    async def create(
        self,
        book_id: str,
        title: str,
        content: str,
        word_count: int,
        status: ArticleStatus = ArticleStatus.DRAFT,
    ) -> str:
        """Create a new article.
        
        Args:
            book_id: Reference to book
            title: Article title
            content: Article content (markdown)
            word_count: Total word count
            status: Article status (default: DRAFT)
        
        Returns:
            article_id as string
        """
        document = {
            "book_id": ObjectId(book_id),
            "title": title,
            "content": content,
            "word_count": word_count,
            "status": status.value,
            "created_at": datetime.utcnow(),
        }
        
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def get_by_book(self, book_id: str) -> Optional[Dict[str, Any]]:
        """Get article for a book.
        
        Args:
            book_id: Book ObjectId as string
        
        Returns:
            Article document or None if not found
        """
        try:
            return await self.collection.find_one(
                {"book_id": ObjectId(book_id)}
            )
        except Exception:
            return None
    
    async def get_by_id(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Get article by ID.
        
        Args:
            article_id: Article ObjectId as string
        
        Returns:
            Article document or None if not found
        """
        try:
            return await self.collection.find_one({"_id": ObjectId(article_id)})
        except Exception:
            return None
