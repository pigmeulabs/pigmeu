"""
Database repository layer for CRUD operations on MongoDB collections.

This module provides high-level operations for interacting with MongoDB
collections, abstracting away low-level driver details.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple, Union
from urllib.parse import urlparse

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from src.models.enums import SubmissionStatus, ArticleStatus


def utcnow() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def _to_object_id(value: Union[str, ObjectId]) -> Optional[ObjectId]:
    """Convert string/ObjectId to ObjectId safely."""
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return None


class SubmissionRepository:
    """Repository for submission collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["submissions"]

    async def create(
        self,
        title: str,
        author_name: str,
        amazon_url: str,
        goodreads_url: Optional[str] = None,
        author_site: Optional[str] = None,
        other_links: Optional[List[str]] = None,
        textual_information: Optional[str] = None,
        run_immediately: bool = True,
        schedule_execution: Optional[datetime] = None,
        main_category: Optional[str] = None,
        article_status: Optional[str] = None,
        user_approval_required: bool = False,
        status: Union[str, SubmissionStatus] = SubmissionStatus.PENDING_SCRAPE,
    ) -> str:
        status_value = status.value if isinstance(status, SubmissionStatus) else str(status)
        now = utcnow()

        document = {
            "title": title,
            "author_name": author_name,
            "amazon_url": str(amazon_url),
            "goodreads_url": str(goodreads_url) if goodreads_url else None,
            "author_site": str(author_site) if author_site else None,
            "other_links": [str(url) for url in (other_links or [])],
            "textual_information": textual_information,
            "run_immediately": bool(run_immediately),
            "schedule_execution": schedule_execution,
            "main_category": main_category,
            "article_status": article_status,
            "user_approval_required": bool(user_approval_required),
            "status": status_value,
            "current_step": status_value,
            "attempts": {},
            "errors": [],
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_by_id(self, submission_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return None
        return await self.collection.find_one({"_id": object_id})

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query: Dict[str, Any] = {}
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"title": {"$regex": search, "$options": "i"}},
                {"author_name": {"$regex": search, "$options": "i"}},
            ]

        total = await self.collection.count_documents(query)
        docs = (
            await self.collection.find(query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )
        return docs, total

    async def update_status(
        self,
        submission_id: Union[str, ObjectId],
        status: Union[str, SubmissionStatus],
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> bool:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return False

        status_value = status.value if isinstance(status, SubmissionStatus) else str(status)
        fields = {"status": status_value, "updated_at": utcnow()}
        if extra_fields:
            fields.update(extra_fields)

        result = await self.collection.update_one({"_id": object_id}, {"$set": fields})
        return result.modified_count > 0

    async def update_fields(self, submission_id: Union[str, ObjectId], fields: Dict[str, Any]) -> bool:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return False

        payload = {**fields, "updated_at": utcnow()}
        result = await self.collection.update_one({"_id": object_id}, {"$set": payload})
        return result.modified_count > 0

    async def check_duplicate(self, amazon_url: str) -> Optional[str]:
        doc = await self.collection.find_one({"amazon_url": str(amazon_url)})
        return str(doc["_id"]) if doc else None

    async def delete(self, submission_id: Union[str, ObjectId]) -> bool:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return False
        result = await self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0

    async def stats(self) -> Dict[str, Any]:
        total = await self.collection.count_documents({})
        by_status_pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        grouped = await self.collection.aggregate(by_status_pipeline).to_list(length=None)

        by_status = {item.get("_id", "unknown"): item.get("count", 0) for item in grouped}
        completed = by_status.get(SubmissionStatus.PUBLISHED.value, 0) + by_status.get(
            SubmissionStatus.READY_FOR_REVIEW.value, 0
        )
        failed = by_status.get(SubmissionStatus.FAILED.value, 0) + by_status.get(
            SubmissionStatus.SCRAPING_FAILED.value, 0
        )
        success_rate = (completed / total) if total else 0.0

        return {
            "total_tasks": total,
            "by_status": by_status,
            "success_rate": round(success_rate, 4),
            "failed_tasks": failed,
        }


class BookRepository:
    """Repository for book collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["books"]

    async def create_or_update(
        self,
        submission_id: Union[str, ObjectId],
        extracted: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        object_id = _to_object_id(submission_id)
        if not object_id:
            raise ValueError("Invalid submission_id")

        payload = extracted if extracted is not None else data
        payload = payload or {}

        existing = await self.collection.find_one({"submission_id": object_id})
        if existing:
            merged = {**existing.get("extracted", {}), **payload}
            await self.collection.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "extracted": merged,
                        "last_updated": utcnow(),
                    }
                },
            )
            return str(existing["_id"])

        doc = {
            "submission_id": object_id,
            "extracted": payload,
            "last_updated": utcnow(),
        }
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_submission(self, submission_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return None
        return await self.collection.find_one({"submission_id": object_id})

    async def get_by_id(self, book_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(book_id)
        if not object_id:
            return None
        return await self.collection.find_one({"_id": object_id})


class SummaryRepository:
    """Repository for summary collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["summaries"]

    async def create(
        self,
        book_id: Union[str, ObjectId],
        source_url: str,
        summary_text: str,
        topics: Optional[List[str]] = None,
        key_points: Optional[List[str]] = None,
        credibility: Optional[str] = None,
        source_domain: Optional[str] = None,
        extra_fields: Optional[Dict[str, Any]] = None,
    ) -> str:
        object_id = _to_object_id(book_id)
        if not object_id:
            raise ValueError("Invalid book_id")

        parsed_domain = source_domain
        if not parsed_domain:
            try:
                parsed_domain = urlparse(str(source_url)).netloc
            except Exception:
                parsed_domain = None

        document = {
            "book_id": object_id,
            "source_url": str(source_url),
            "source_domain": parsed_domain,
            "summary_text": summary_text,
            "topics": topics or [],
            "key_points": key_points or [],
            "credibility": credibility,
            "created_at": utcnow(),
        }
        if extra_fields:
            document.update(extra_fields)
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_by_book(self, book_id: Union[str, ObjectId]) -> List[Dict[str, Any]]:
        object_id = _to_object_id(book_id)
        if not object_id:
            return []
        return await self.collection.find({"book_id": object_id}).to_list(length=None)


class KnowledgeBaseRepository:
    """Repository for knowledge_base collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["knowledge_base"]

    async def create_or_update(
        self,
        book_id: Optional[Union[str, ObjectId]] = None,
        markdown_content: Optional[str] = None,
        topics_index: Optional[List[str]] = None,
        submission_id: Optional[Union[str, ObjectId]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        book_object_id = _to_object_id(book_id) if book_id is not None else None
        submission_object_id = _to_object_id(submission_id) if submission_id is not None else None

        if data and not markdown_content:
            lines = ["# Additional Knowledge", ""]
            for key, value in data.items():
                lines.append(f"- **{key}**: {value}")
            markdown_content = "\n".join(lines)

        if not markdown_content:
            markdown_content = ""

        selector: Dict[str, Any]
        if book_object_id:
            selector = {"book_id": book_object_id}
        elif submission_object_id:
            selector = {"submission_id": submission_object_id}
        else:
            raise ValueError("book_id or submission_id is required")

        existing = await self.collection.find_one(selector)
        now = utcnow()

        doc = {
            **selector,
            "markdown_content": markdown_content,
            "topics_index": topics_index or [],
            "updated_at": now,
        }

        if existing:
            await self.collection.update_one({"_id": existing["_id"]}, {"$set": doc})
            return str(existing["_id"])

        doc["created_at"] = now
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def get_by_book(self, book_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(book_id)
        if not object_id:
            return None
        return await self.collection.find_one({"book_id": object_id})

    async def get_by_submission(self, submission_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return None
        return await self.collection.find_one({"submission_id": object_id})


class ArticleRepository:
    """Repository for article collection operations."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["articles"]
        self.drafts_collection = db["articles_drafts"]

    async def create(
        self,
        book_id: Union[str, ObjectId],
        title: str,
        content: str,
        word_count: int,
        status: Union[ArticleStatus, str] = ArticleStatus.DRAFT,
        submission_id: Optional[Union[str, ObjectId]] = None,
        validation_report: Optional[Dict[str, Any]] = None,
        topics_used: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        book_object_id = _to_object_id(book_id)
        if not book_object_id:
            raise ValueError("Invalid book_id")

        submission_object_id = _to_object_id(submission_id) if submission_id is not None else None
        status_value = status.value if isinstance(status, ArticleStatus) else str(status)

        now = utcnow()
        document = {
            "book_id": book_object_id,
            "submission_id": submission_object_id,
            "title": title,
            "content": content,
            "word_count": int(word_count),
            "status": status_value,
            "validation_report": validation_report,
            "topics_used": topics_used or [],
            "created_at": now,
            "updated_at": now,
        }

        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def get_by_book(self, book_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(book_id)
        if not object_id:
            return None
        return await self.collection.find_one({"book_id": object_id}, sort=[("created_at", DESCENDING)])

    async def list_by_submission(self, submission_id: Union[str, ObjectId], limit: int = 20) -> List[Dict[str, Any]]:
        object_id = _to_object_id(submission_id)
        if not object_id:
            return []
        return (
            await self.collection.find({"submission_id": object_id})
            .sort("created_at", DESCENDING)
            .limit(limit)
            .to_list(length=limit)
        )

    async def get_latest_by_submission(self, submission_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        articles = await self.list_by_submission(submission_id=submission_id, limit=1)
        return articles[0] if articles else None

    async def get_by_id(self, article_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(article_id)
        if not object_id:
            return None
        return await self.collection.find_one({"_id": object_id})

    async def update(self, article_id: Union[str, ObjectId], fields: Dict[str, Any]) -> bool:
        object_id = _to_object_id(article_id)
        if not object_id:
            return False

        payload = {**fields, "updated_at": utcnow()}
        result = await self.collection.update_one({"_id": object_id}, {"$set": payload})
        return result.modified_count > 0

    async def update_with_wordpress_link(
        self,
        article_id: Union[str, ObjectId],
        wp_post_id: Union[str, int],
        wp_url: str,
    ) -> bool:
        return await self.update(
            article_id,
            {
                "wordpress_post_id": str(wp_post_id),
                "wordpress_url": str(wp_url),
                "published_at": utcnow(),
                "status": ArticleStatus.PUBLISHED.value,
            },
        )

    async def save_draft(self, article_id: Union[str, ObjectId], content: str) -> str:
        article_object_id = _to_object_id(article_id)
        if not article_object_id:
            raise ValueError("Invalid article_id")

        now = utcnow()
        existing = await self.drafts_collection.find_one({"article_id": article_object_id})

        payload = {
            "article_id": article_object_id,
            "content": content,
            "updated_at": now,
        }

        if existing:
            await self.drafts_collection.update_one({"_id": existing["_id"]}, {"$set": payload})
            return str(existing["_id"])

        payload["created_at"] = now
        result = await self.drafts_collection.insert_one(payload)
        return str(result.inserted_id)

    async def get_draft(self, article_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        article_object_id = _to_object_id(article_id)
        if not article_object_id:
            return None
        return await self.drafts_collection.find_one({"article_id": article_object_id})


class CredentialRepository:
    """Repository for storing service credentials."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["credentials"]

    async def create(
        self,
        service: str,
        key: str,
        encrypted: bool = True,
        name: Optional[str] = None,
        username_email: Optional[str] = None,
        active: bool = True,
    ) -> str:
        now = utcnow()
        document = {
            "service": service,
            "name": name or service,
            "key": key,
            "encrypted": bool(encrypted),
            "username_email": username_email,
            "active": bool(active),
            "created_at": now,
            "updated_at": now,
            "last_used_at": None,
        }
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def list_all(self) -> List[Dict[str, Any]]:
        return await self.collection.find({}).sort("created_at", DESCENDING).to_list(length=None)

    async def list_active(self, service: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"active": True}
        if service:
            query["service"] = service
        return await self.collection.find(query).sort("created_at", DESCENDING).to_list(length=None)

    async def get_active(self, service: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"service": service, "active": True}, sort=[("created_at", DESCENDING)])

    async def get_active_by_name(self, name: str, service: Optional[str] = None) -> Optional[Dict[str, Any]]:
        query: Dict[str, Any] = {"name": name, "active": True}
        if service:
            query["service"] = service
        return await self.collection.find_one(query, sort=[("created_at", DESCENDING)])

    async def get_by_id(self, cred_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(cred_id)
        if not object_id:
            return None
        return await self.collection.find_one({"_id": object_id})

    async def touch_last_used(self, cred_id: Union[str, ObjectId]) -> bool:
        object_id = _to_object_id(cred_id)
        if not object_id:
            return False
        result = await self.collection.update_one(
            {"_id": object_id},
            {"$set": {"last_used_at": utcnow(), "updated_at": utcnow()}},
        )
        return result.modified_count > 0

    async def update(self, cred_id: Union[str, ObjectId], fields: Dict[str, Any]) -> bool:
        object_id = _to_object_id(cred_id)
        if not object_id:
            return False
        payload = {**fields, "updated_at": utcnow()}
        result = await self.collection.update_one({"_id": object_id}, {"$set": payload})
        return result.modified_count > 0

    async def delete(self, cred_id: Union[str, ObjectId]) -> bool:
        object_id = _to_object_id(cred_id)
        if not object_id:
            return False
        result = await self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0


class PromptRepository:
    """Repository for storing prompt templates."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["prompts"]

    async def create(self, payload: Dict[str, Any]) -> str:
        now = utcnow()
        doc = {
            **payload,
            "active": payload.get("active", True),
            "version": payload.get("version", 1),
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        return str(result.inserted_id)

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active: Optional[bool] = None,
        purpose: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if active is not None:
            query["active"] = active
        if purpose:
            query["purpose"] = purpose
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        return (
            await self.collection.find(query)
            .sort("updated_at", DESCENDING)
            .skip(skip)
            .limit(limit)
            .to_list(length=limit)
        )

    async def get_by_id(self, prompt_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        object_id = _to_object_id(prompt_id)
        if not object_id:
            return None
        return await self.collection.find_one({"_id": object_id})

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one({"name": name})

    async def get_active_by_purpose(self, purpose: str) -> Optional[Dict[str, Any]]:
        return await self.collection.find_one(
            {"purpose": purpose, "active": True},
            sort=[("updated_at", DESCENDING)],
        )

    async def update(self, prompt_id: Union[str, ObjectId], fields: Dict[str, Any]) -> bool:
        object_id = _to_object_id(prompt_id)
        if not object_id:
            return False
        payload = {**fields, "updated_at": utcnow()}
        result = await self.collection.update_one({"_id": object_id}, {"$set": payload})
        return result.modified_count > 0

    async def delete(self, prompt_id: Union[str, ObjectId]) -> bool:
        object_id = _to_object_id(prompt_id)
        if not object_id:
            return False
        result = await self.collection.delete_one({"_id": object_id})
        return result.deleted_count > 0
