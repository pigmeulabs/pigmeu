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
import openai

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


@shared_task(bind=True)
def generate_article_task(self, submission_id: str) -> dict:
    """Generate a full review article for a submission using prompts.

    Attempts to use stored prompts and an OpenAI credential. Falls back to
    a simple template-based article when the model is unavailable.
    """
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            db = await get_db()
            submission_repo = SubmissionRepository(db)
            book_repo = BookRepository(db)
            kb_repo = KnowledgeBaseRepository(db)
            # repositories
            PromptRepo = None
            CredRepo = None
            try:
                from src.db.repositories import PromptRepository, CredentialRepository, ArticleRepository
                PromptRepo = PromptRepository(db)
                CredRepo = CredentialRepository(db)
                ArticleRepo = ArticleRepository(db)
            except Exception:
                # ArticleRepository is defined above; if import fails, use available class
                from src.db.repositories import ArticleRepository as ArticleRepoClass
                ArticleRepo = ArticleRepoClass(db)

            submission = await submission_repo.get_by_id(submission_id)
            book = await book_repo.get_by_submission(submission_id)
            kb = None
            if book:
                kb = await kb_repo.get_by_book(str(book.get('_id')))

            title_base = submission.get('title') if submission else 'Book Review'
            author = submission.get('author_name') if submission else ''

            # select prompt for article generation
            prompt = None
            if PromptRepo:
                prompts = await PromptRepo.list_all()
                for p in prompts:
                    if p.get('purpose') and 'article' in p.get('purpose').lower():
                        prompt = p
                        break
                if not prompt and prompts:
                    prompt = prompts[0]

            system_prompt = prompt.get('system_prompt') if prompt else 'You are an expert technical book reviewer.'
            user_prompt_template = prompt.get('user_prompt') if prompt else (
                'Write a comprehensive, SEO-optimized review article for the book "{{title}}" by {{author}}. '
                'Use the following context and knowledge to produce sections and an engaging conclusion. Produce markdown.'
            )

            # assemble user prompt
            user_prompt = user_prompt_template.replace('{{title}}', title_base).replace('{{author}}', author)
            if kb and kb.get('markdown_content'):
                user_prompt += '\n\nContext:\n' + kb.get('markdown_content')

            generated_text = None

            # find OpenAI credential
            openai_key = None
            if CredRepo:
                try:
                    creds = await CredRepo.list_all()
                    for c in creds:
                        if c.get('service') == 'openai' and c.get('key'):
                            openai_key = c.get('key')
                            break
                except Exception:
                    logger.debug('Could not fetch credentials')

            if openai_key:
                try:
                    openai.api_key = openai_key
                    model_id = prompt.get('model_id') if prompt and prompt.get('model_id') else 'gpt-3.5-turbo'
                    resp = openai.ChatCompletion.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=(prompt.get('temperature') if prompt else 0.7),
                        max_tokens=(prompt.get('max_tokens') if prompt else 1200),
                    )
                    if resp and getattr(resp, 'choices', None):
                        choice = resp.choices[0]
                        if getattr(choice, 'message', None):
                            generated_text = choice.message.get('content')
                        else:
                            generated_text = choice.get('text') or choice.get('message', {}).get('content')
                except Exception as e:
                    logger.warning(f'Article model call failed: {e}')

            # fallback simple article
            if not generated_text:
                parts = [
                    f'# {title_base} — Review',
                    f'**Author:** {author}',
                    '\n## Introduction\n',
                    f'This is a short review of "{title_base}" by {author}.',
                ]
                if kb and kb.get('markdown_content'):
                    parts.append('\n## Context and Notes\n')
                    parts.append(kb.get('markdown_content'))
                parts.append('\n## Conclusion\n')
                parts.append('This review was generated automatically.')
                generated_text = '\n'.join(parts)

            # derive title
            gen_title = title_base + ' — Review'
            # store article
            book_id = str(book.get('_id')) if book else submission_id
            word_count = len(generated_text.split())
            article_id = await ArticleRepo.create(
                book_id=book_id,
                title=gen_title,
                content=generated_text,
                word_count=word_count,
            )

            # update submission status
            await submission_repo.update_fields(submission_id, {"status": "article_generated"})

            return {"status": "ok", "article_id": article_id}

        return loop.run_until_complete(_run())
    except Exception as e:
        logger.error(f"Error generating article: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}



@shared_task(bind=True)
def generate_context_task(self, submission_id: str) -> dict:
    """Generate context/knowledge base for a submission using stored prompts.

    This implementation will attempt to use stored prompts and an OpenAI
    credential (if available) to generate a context via the model. If no
    credential is present or the model call fails, it will fall back to a
    simple local generator.
    """
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            db = await get_db()
            submission_repo = SubmissionRepository(db)
            book_repo = BookRepository(db)
            kb_repo = KnowledgeBaseRepository(db)

            # Optional repositories
            PromptRepo = None
            CredRepo = None
            try:
                from src.db.repositories import PromptRepository, CredentialRepository
                PromptRepo = PromptRepository(db)
                CredRepo = CredentialRepository(db)
            except Exception:
                logger.debug("Prompt/Credential repos not available; continuing without model integration")

            submission = await submission_repo.get_by_id(submission_id)
            book = await book_repo.get_by_submission(submission_id)

            title = submission.get('title') if submission else 'Unknown'
            author = submission.get('author_name') if submission else 'Unknown'

            # Select prompt
            prompt = None
            if PromptRepo:
                prompts = await PromptRepo.list_all()
                for p in prompts:
                    if p.get('purpose') and 'context' in p.get('purpose').lower():
                        prompt = p
                        break
                if not prompt and prompts:
                    prompt = prompts[0]

            system_prompt = prompt.get('system_prompt') if prompt else 'You are an assistant that summarizes book information.'
            user_prompt_template = prompt.get('user_prompt') if prompt else 'Create a structured markdown context for the book titled "{{title}}" by {{author}}.'

            user_prompt = user_prompt_template.replace('{{title}}', title).replace('{{author}}', author)
            if book and book.get('extracted'):
                user_prompt += "\n\nExtracted metadata:\n" + "\n".join([f"{k}: {v}" for k, v in book.get('extracted', {}).items()])

            generated_text = None

            # Find OpenAI credential
            openai_key = None
            if CredRepo:
                try:
                    creds = await CredRepo.list_all()
                    for c in creds:
                        if c.get('service') == 'openai' and c.get('key'):
                            openai_key = c.get('key')
                            break
                except Exception:
                    logger.debug('Failed to list credentials')

            # Attempt real model call if key available
            if openai_key:
                try:
                    openai.api_key = openai_key
                    model_id = prompt.get('model_id') if prompt and prompt.get('model_id') else 'gpt-3.5-turbo'
                    resp = openai.ChatCompletion.create(
                        model=model_id,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=(prompt.get('temperature') if prompt else 0.7),
                        max_tokens=(prompt.get('max_tokens') if prompt else 800),
                    )
                    # Extract text (compat with returned structure)
                    generated_text = None
                    if resp and getattr(resp, 'choices', None):
                        choice = resp.choices[0]
                        # support both legacy and newer structures
                        if getattr(choice, 'message', None):
                            generated_text = choice.message.get('content')
                        else:
                            generated_text = choice.get('text') or choice.get('message', {}).get('content')
                except Exception as e:
                    logger.warning(f'OpenAI model call failed: {e}')

            # Fallback generator
            if not generated_text:
                md = f"# Context for {title}\n\n**Author:** {author}\n\n"
                if book and book.get('extracted'):
                    md += "## Extracted metadata\n"
                    for k, v in book.get('extracted', {}).items():
                        md += f"- **{k}**: {v}\n"
                md += "\n*Note: generated without external model.*"
                generated_text = md

            # Persist into knowledge base
            await kb_repo.create_or_update(
                book_id=str(book.get('_id')) if book else submission_id,
                markdown_content=generated_text,
                topics_index=["autogenerated"],
            )

            # update submission status
            await submission_repo.update_fields(submission_id, {"status": "context_generated"})

            return {"status": "ok"}

        return loop.run_until_complete(_run())
    except Exception as e:
        logger.error(f"Error generating context: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
