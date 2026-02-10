"""
Celery task definitions for web scraping pipeline.

This module defines asynchronous tasks for:
- Scraping Amazon product pages
- Scraping Goodreads reviews
- Scraping author websites
- Status tracking and error handling
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId

from celery import shared_task, Task
from celery.exceptions import MaxRetriesExceededError

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
)
from src.models.enums import SubmissionStatus, StepStatus
from src.scrapers.amazon import AmazonScraper
from src.scrapers.goodreads import GoodreadsScraper
from src.scrapers.web_scraper import GenericWebScraper

logger = logging.getLogger(__name__)


class ScraperTask(Task):
    """Base Celery task class with error handling.
    
    All scraper tasks inherit from this to share common functionality.
    """
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True


@shared_task(base=ScraperTask, bind=True)
async def scrape_amazon_task(
    self,
    submission_id: str,
    amazon_url: str,
) -> Dict[str, Any]:
    """Scrape Amazon product page for book metadata.
    
    Args:
        submission_id: MongoDB submission ID
        amazon_url: Amazon product URL (e.g., https://amazon.com/dp/B001234567)
    
    Returns:
        Dictionary with scraped book data
    
    Raises:
        Exception: If scraping fails after retries
    """
    task_id = self.request.id
    attempt = self.request.retries
    
    logger.info(
        f"Starting Amazon scrape: submission={submission_id}, "
        f"url={amazon_url}, attempt={attempt + 1}"
    )
    
    db = None
    amazon_scraper = None
    
    try:
        # Get database connection
        db = await get_db()
        
        # Update submission status
        submission_repo = SubmissionRepository(db)
        await submission_repo.update_status(
            ObjectId(submission_id),
            SubmissionStatus.SCRAPING_AMAZON,
            {
                "current_step": "amazon_scrape",
                "task_id": task_id,
                "attempt": attempt + 1,
                "started_at": datetime.utcnow(),
            }
        )
        
        # Initialize scraper
        amazon_scraper = AmazonScraper()
        await amazon_scraper.initialize()
        
        # Scrape Amazon
        logger.info(f"Fetching Amazon page: {amazon_url}")
        book_data = await amazon_scraper.scrape(amazon_url)
        
        if not book_data:
            logger.error(f"Failed to scrape Amazon: {amazon_url}")
            await submission_repo.update_status(
                ObjectId(submission_id),
                SubmissionStatus.SCRAPING_FAILED,
                {"error": "Amazon scrape returned no data"}
            )
            raise Exception("Amazon scrape failed")
        
        # Store book data in MongoDB
        book_repo = BookRepository(db)
        book_doc = await book_repo.create_or_update(
            submission_id=submission_id,
            data={
                "title": book_data.get("title"),
                "authors": book_data.get("authors", []),
                "price": book_data.get("price"),
                "rating": book_data.get("rating"),
                "reviews_count": book_data.get("reviews_count", 0),
                "isbn": book_data.get("isbn"),
                "pages": book_data.get("pages"),
                "publication_date": book_data.get("publication_date"),
                "publisher": book_data.get("publisher"),
                "language": book_data.get("language"),
                "theme": book_data.get("theme"),
                "amazon_url": book_data.get("amazon_url"),
                "asin": book_data.get("asin"),
                "scraped_at": datetime.utcnow(),
            }
        )
        
        logger.info(f"Book data stored: {book_doc}")
        
        # Update submission to next status
        await submission_repo.update_status(
            ObjectId(submission_id),
            SubmissionStatus.SCRAPING_GOODREADS,
            {
                "current_step": "goodreads_scrape",
                "amazon_scrape_completed_at": datetime.utcnow(),
            }
        )
        
        # Trigger next task (Goodreads scrape)
        scrape_goodreads_task.delay(
            submission_id=submission_id,
            title=book_data.get("title"),
            authors=book_data.get("authors", []),
        )
        
        logger.info(f"Amazon scrape completed, triggered Goodreads scrape")
        return {
            "status": "success",
            "book_id": str(book_doc.get("_id")),
            "title": book_data.get("title"),
            "authors": book_data.get("authors"),
        }
    
    except Exception as e:
        logger.error(f"Error scraping Amazon: {e}", exc_info=True)
        
        try:
            if db:
                submission_repo = SubmissionRepository(db)
                await submission_repo.update_status(
                    ObjectId(submission_id),
                    SubmissionStatus.SCRAPING_FAILED,
                    {"error": str(e), "attempt": attempt + 1}
                )
        except Exception as err:
            logger.error(f"Error updating submission status: {err}")
        
        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=2 ** attempt)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for Amazon scrape: {submission_id}")
            raise
    
    finally:
        # Clean up scraper
        if amazon_scraper:
            try:
                await amazon_scraper.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up Amazon scraper: {e}")


@shared_task(base=ScraperTask, bind=True)
async def scrape_goodreads_task(
    self,
    submission_id: str,
    title: str,
    authors: list,
) -> Dict[str, Any]:
    """Scrape Goodreads for book ratings and reviews.
    
    Args:
        submission_id: MongoDB submission ID
        title: Book title
        authors: List of author names
    
    Returns:
        Dictionary with Goodreads data
    """
    task_id = self.request.id
    attempt = self.request.retries
    
    logger.info(
        f"Starting Goodreads scrape: submission={submission_id}, "
        f"title={title}, attempt={attempt + 1}"
    )
    
    db = None
    goodreads_scraper = None
    
    try:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        
        # Update status
        await submission_repo.update_status(
            ObjectId(submission_id),
            SubmissionStatus.SCRAPING_GOODREADS,
            {
                "current_step": "goodreads_scrape",
                "task_id": task_id,
                "started_at": datetime.utcnow(),
            }
        )
        
        # Search Goodreads
        goodreads_scraper = GoodreadsScraper()
        await goodreads_scraper.initialize()
        
        author = authors[0] if authors else None
        logger.info(f"Searching Goodreads: {title} by {author}")
        
        results = await goodreads_scraper.search(title, author)
        
        if not results:
            logger.warning(f"No Goodreads results found for: {title}")
            goodreads_data = {"goodreads_found": False}
        else:
            # Use first result
            best_result = results[0]
            logger.info(f"Found Goodreads book: {best_result.get('title')}")
            
            # Get detailed info if available
            if best_result.get("goodreads_url"):
                details = await goodreads_scraper.get_book_details(
                    best_result["goodreads_url"]
                )
                if details:
                    best_result.update(details)
            
            goodreads_data = {
                "goodreads_found": True,
                **best_result,
            }
        
        # Store Goodreads data
        book_repo = BookRepository(db)
        await book_repo.create_or_update(
            submission_id=submission_id,
            data={
                "goodreads_data": goodreads_data,
                "goodreads_updated_at": datetime.utcnow(),
            }
        )
        
        # Update submission status
        await submission_repo.update_status(
            ObjectId(submission_id),
            SubmissionStatus.CONTEXT_GENERATION,
            {
                "current_step": "context_generation",
                "goodreads_scrape_completed_at": datetime.utcnow(),
            }
        )
        
        logger.info("Goodreads scrape completed")
        return goodreads_data
    
    except Exception as e:
        logger.error(f"Error scraping Goodreads: {e}", exc_info=True)
        
        try:
            if db:
                submission_repo = SubmissionRepository(db)
                await submission_repo.update_status(
                    ObjectId(submission_id),
                    SubmissionStatus.CONTEXT_GENERATION,  # Continue to next step anyway
                    {"goodreads_error": str(e), "attempt": attempt + 1}
                )
        except Exception as err:
            logger.error(f"Error updating submission: {err}")
        
        # Goodreads failures are not critical, continue
        try:
            raise self.retry(exc=e, countdown=2 ** attempt)
        except MaxRetriesExceededError:
            logger.warning(f"Max retries for Goodreads, continuing: {submission_id}")
            return {"status": "failed", "error": str(e)}
    
    finally:
        if goodreads_scraper:
            try:
                await goodreads_scraper.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up Goodreads scraper: {e}")


@shared_task(base=ScraperTask, bind=True)
async def scrape_author_website_task(
    self,
    submission_id: str,
    author_name: str,
    author_website: Optional[str] = None,
) -> Dict[str, Any]:
    """Scrape author website for bio and contact information.
    
    Args:
        submission_id: MongoDB submission ID
        author_name: Author name
        author_website: Author website URL (optional, will search if not provided)
    
    Returns:
        Dictionary with author data
    """
    task_id = self.request.id
    attempt = self.request.retries
    
    logger.info(
        f"Starting author website scrape: submission={submission_id}, "
        f"author={author_name}, attempt={attempt + 1}"
    )
    
    db = None
    web_scraper = None
    
    try:
        db = await get_db()
        
        # If no URL provided, try to find it
        if not author_website:
            # This would integrate with a search engine or database lookup
            logger.warning(f"No author website provided for: {author_name}")
            author_website = f"https://www.google.com/search?q={author_name}+website"
        
        # Scrape website
        web_scraper = GenericWebScraper()
        await web_scraper.initialize()
        
        logger.info(f"Scraping author website: {author_website}")
        author_data = await web_scraper.scrape(author_website)
        
        if author_data:
            # Store in knowledge base
            kb_repo = KnowledgeBaseRepository(db)
            await kb_repo.create_or_update(
                submission_id=submission_id,
                data={
                    "author_name": author_name,
                    "author_website": author_website,
                    "author_bio": author_data.get("description"),
                    "author_email": author_data.get("email"),
                    "author_social": author_data.get("social_links", {}),
                    "scraped_at": datetime.utcnow(),
                }
            )
            
            logger.info(f"Author data stored: {author_name}")
        else:
            logger.warning(f"No author data found for: {author_website}")
        
        return {
            "status": "success" if author_data else "no_data",
            "author": author_name,
            **author_data
        }
    
    except Exception as e:
        logger.error(f"Error scraping author website: {e}", exc_info=True)
        
        try:
            raise self.retry(exc=e, countdown=2 ** attempt)
        except MaxRetriesExceededError:
            logger.warning(f"Max retries for author scrape: {submission_id}")
            return {"status": "failed", "error": str(e)}
    
    finally:
        if web_scraper:
            try:
                await web_scraper.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up web scraper: {e}")


@shared_task
async def check_scraping_status(submission_id: str) -> Dict[str, Any]:
    """Check overall scraping status for a submission.
    
    Args:
        submission_id: MongoDB submission ID
    
    Returns:
        Status summary
    """
    try:
        db = await get_db()
        submission_repo = SubmissionRepository(db)
        
        submission = await submission_repo.get_by_id(ObjectId(submission_id))
        
        if not submission:
            logger.error(f"Submission not found: {submission_id}")
            return {"status": "not_found"}
        
        status = {
            "submission_id": submission_id,
            "submission_status": submission.get("status"),
            "current_step": submission.get("current_step"),
            "created_at": submission.get("created_at"),
            "updated_at": submission.get("updated_at"),
        }
        
        logger.info(f"Scraping status: {status}")
        return status
    
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        return {"status": "error", "error": str(e)}


# Task chain for complete pipeline
def start_scraping_pipeline(submission_id: str, amazon_url: str) -> None:
    """Start the complete scraping pipeline for a submission.
    
    This orchestrates the chain:
    1. Amazon scraping
    2. Goodreads scraping
    3. Author website scraping
    4. Context generation (next phase)
    
    Args:
        submission_id: MongoDB submission ID
        amazon_url: Amazon product URL
    """
    logger.info(f"Starting scraping pipeline for submission: {submission_id}")
    
    # Start Amazon scrape (will trigger Goodreads automatically)
    scrape_amazon_task.delay(
        submission_id=submission_id,
        amazon_url=amazon_url,
    )
