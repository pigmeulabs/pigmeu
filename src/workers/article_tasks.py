"""
Article generation tasks using ArticleStructurer.
"""

import logging
import asyncio
from typing import Dict, Any
from bson import ObjectId

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
import openai

from src.db.connection import get_db
from src.db.repositories import (
    SubmissionRepository,
    BookRepository,
    KnowledgeBaseRepository,
    ArticleRepository,
)
from src.models.enums import SubmissionStatus
from src.workers.article_structurer import ArticleStructurer

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_article_task(self, submission_id: str) -> dict:
    """Generate a full review article for a submission using ArticleStructurer.
    
    This task uses the ArticleStructurer to generate and validate articles
    with proper structure, word count, and SEO optimization.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _run():
            db = await get_db()
            submission_repo = SubmissionRepository(db)
            book_repo = BookRepository(db)
            kb_repo = KnowledgeBaseRepository(db)
            article_repo = ArticleRepository(db)

            submission = await submission_repo.get_by_id(submission_id)
            book = await book_repo.get_by_submission(submission_id)
            kb = None
            if book:
                kb = await kb_repo.get_by_book(str(book.get('_id')))

            title_base = submission.get('title') if submission else 'Book Review'
            author = submission.get('author_name') if submission else ''

            # Use ArticleStructurer for generating and validating articles
            structurer = ArticleStructurer()

            # Prepare book data for ArticleStructurer
            book_data = {
                "title": title_base,
                "author": author,
                "metadata": book.get('extracted', {}) if book else {},
                "context": kb.get('markdown_content', '') if kb else ''
            }

            try:
                # Generate and validate article with retries
                article_content = await structurer.generate_valid_article(
                    book_data=book_data,
                    context=book_data.get('context', ''),
                    max_retries=3
                )

                # Extract title from article (first H1)
                lines = article_content.split('\n')
                gen_title = next((line.replace('# ', '') for line in lines if line.startswith('# ')), title_base + ' — Review')

                # Store article
                book_id = str(book.get('_id')) if book else submission_id
                word_count = len(article_content.split())
                article_id = await article_repo.create(
                    book_id=book_id,
                    title=gen_title,
                    content=article_content,
                    word_count=word_count,
                )

                # Update submission status
                await submission_repo.update_fields(submission_id, {"status": "article_generated"})

                logger.info(f"✅ Article generated successfully: {article_id}")
                return {"status": "ok", "article_id": article_id}

            except Exception as e:
                logger.error(f"ArticleStructurer failed: {e}")
                # Fallback to original implementation
                return await _fallback_article_generation(
                    submission_id, submission, book, kb, submission_repo, book_repo, article_repo
                )

        async def _fallback_article_generation(
            submission_id: str,
            submission: dict,
            book: dict,
            kb: dict,
            submission_repo: SubmissionRepository,
            book_repo: BookRepository,
            article_repo: ArticleRepository
        ) -> dict:
            """Fallback article generation using original method."""
            logger.warning("Falling back to original article generation method")
            
            title_base = submission.get('title') if submission else 'Book Review'
            author = submission.get('author_name') if submission else ''
            
            # Try to use prompts if available
            prompt = None
            try:
                from src.db.repositories import PromptRepository
                prompt_repo = PromptRepository(db)
                prompts = await prompt_repo.list_all()
                for p in prompts:
                    if p.get('purpose') and 'article' in p.get('purpose').lower():
                        prompt = p
                        break
                if not prompt and prompts:
                    prompt = prompts[0]
            except Exception:
                logger.debug('Prompt repository not available')

            system_prompt = prompt.get('system_prompt') if prompt else 'You are an expert technical book reviewer.'
            user_prompt_template = prompt.get('user_prompt') if prompt else (
                'Write a comprehensive, SEO-optimized review article for the book "{{title}}" by {{author}}. '
                'Use the following context and knowledge to produce sections and an engaging conclusion. Produce markdown.'
            )

            # Assemble user prompt
            user_prompt = user_prompt_template.replace('{{title}}', title_base).replace('{{author}}', author)
            if kb and kb.get('markdown_content'):
                user_prompt += '\n\nContext:\n' + kb.get('markdown_content')

            generated_text = None

            # Try to use OpenAI if available
            openai_key = None
            try:
                from src.db.repositories import CredentialRepository
                cred_repo = CredentialRepository(db)
                creds = await cred_repo.list_all()
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

            # Fallback simple article
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

            # Store article
            book_id = str(book.get('_id')) if book else submission_id
            word_count = len(generated_text.split())
            article_id = await article_repo.create(
                book_id=book_id,
                title=title_base + ' — Review',
                content=generated_text,
                word_count=word_count,
            )

            # Update submission status
            await submission_repo.update_fields(submission_id, {"status": "article_generated"})

            return {"status": "ok", "article_id": article_id}

        return loop.run_until_complete(_run())
    except Exception as e:
        logger.error(f"Error generating article: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}