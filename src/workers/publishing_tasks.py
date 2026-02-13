"""Celery tasks for WordPress publication."""

from __future__ import annotations

import asyncio
import logging
import re
from html import escape
from typing import List

from celery import shared_task

from src.config import settings
from src.db.connection import get_db
from src.db.repositories import ArticleRepository, CredentialRepository, SubmissionRepository
from src.models.enums import SubmissionStatus
from src.scrapers.wordpress_client import WordPressClient

logger = logging.getLogger(__name__)


def markdown_to_html(markdown_text: str) -> str:
    """Simple markdown to HTML converter for headings, lists, and paragraphs."""
    lines = markdown_text.splitlines()
    html_lines = []
    in_list = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        if line.startswith("### "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h3>{escape(line[4:])}</h3>")
            continue

        if line.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{escape(line[3:])}</h2>")
            continue

        if line.startswith("# "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h1>{escape(line[2:])}</h1>")
            continue

        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{escape(line[2:])}</li>")
            continue

        if in_list:
            html_lines.append("</ul>")
            in_list = False

        paragraph = escape(line)
        paragraph = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", paragraph)
        html_lines.append(f"<p>{paragraph}</p>")

    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


def build_meta_description(markdown_text: str, fallback_title: str) -> str:
    """Extract a concise meta description from markdown content."""
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") or line.startswith("- "):
            continue

        normalized = re.sub(r"\*\*(.+?)\*\*", r"\1", line)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if normalized:
            return (normalized[:157] + "...") if len(normalized) > 160 else normalized

    title = (fallback_title or "Generated article").strip()
    return (title[:157] + "...") if len(title) > 160 else title


def _compact_tags(values: List[str], max_items: int = 6) -> List[str]:
    seen = set()
    tags: List[str] = []
    for value in values:
        clean = str(value or "").strip()
        if not clean:
            continue
        lower = clean.lower()
        if lower in seen:
            continue
        seen.add(lower)
        tags.append(clean)
        if len(tags) >= max_items:
            break
    return tags


@shared_task(bind=True)
def publish_article_task(self, article_id: str, submission_id: str | None = None, draft: bool = False):
    """Publish article to WordPress and persist publication metadata."""

    async def _run():
        db = await get_db()
        article_repo = ArticleRepository(db)
        cred_repo = CredentialRepository(db)
        submission_repo = SubmissionRepository(db)

        article = await article_repo.get_by_id(article_id)
        if not article:
            return {"status": "error", "error": "article_not_found"}

        wp_url = settings.wordpress_url
        wp_user = settings.wordpress_username
        wp_pass = settings.wordpress_password

        cred_doc = await cred_repo.get_active("wordpress")
        if cred_doc:
            wp_url = cred_doc.get("url") or wp_url
            wp_user = cred_doc.get("username_email") or wp_user
            wp_pass = cred_doc.get("key") or wp_pass
            if isinstance(cred_doc.get("name"), str) and cred_doc.get("name", "").startswith("http"):
                wp_url = cred_doc.get("name")

        if not wp_url or not wp_user or not wp_pass:
            return {"status": "error", "error": "wordpress_credentials_not_configured"}

        sid = submission_id
        if not sid and article.get("submission_id"):
            sid = str(article.get("submission_id"))

        submission = await submission_repo.get_by_id(sid) if sid else None

        category_names: List[str] = []
        if submission and submission.get("main_category"):
            category_names.append(str(submission.get("main_category")))

        tag_candidates: List[str] = [
            "book-review",
            str(submission.get("article_status")) if submission and submission.get("article_status") else "",
            str(submission.get("author_name")) if submission and submission.get("author_name") else "",
        ]

        topics_used = article.get("topics_used", []) or []
        for item in topics_used:
            if isinstance(item, dict) and item.get("name"):
                tag_candidates.append(str(item.get("name")))

        tag_names = _compact_tags(tag_candidates)

        client = WordPressClient(wordpress_url=wp_url, username=wp_user, password=wp_pass)
        category_ids, tag_ids = await client.resolve_categories_and_tags(
            categories=_compact_tags(category_names, max_items=3),
            tags=tag_names,
        )

        content_markdown = article.get("content", "")
        html_content = markdown_to_html(content_markdown)
        meta_description = build_meta_description(content_markdown, article.get("title", "Generated Article"))

        result = await client.create_post(
            title=article.get("title", "Generated Article"),
            content_html=html_content,
            excerpt=meta_description,
            categories=category_ids,
            tags=tag_ids,
            status="draft" if draft else "publish",
            meta={
                "meta_description": meta_description,
                "_yoast_wpseo_metadesc": meta_description,
                "rank_math_description": meta_description,
            },
        )

        post_id = result.get("id")
        post_url = result.get("link")

        await article_repo.update_with_wordpress_link(article_id=article_id, wp_post_id=post_id, wp_url=post_url)
        await article_repo.update(
            article_id,
            {
                "wordpress_categories": category_ids,
                "wordpress_tags": tag_ids,
                "meta_description": meta_description,
            },
        )

        if sid:
            await submission_repo.update_status(
                sid,
                SubmissionStatus.PUBLISHED,
                {"current_step": "published", "published_url": post_url},
            )

        if cred_doc:
            await cred_repo.touch_last_used(str(cred_doc.get("_id")))

        return {
            "status": "ok",
            "article_id": article_id,
            "wordpress_post_id": post_id,
            "wordpress_url": post_url,
            "categories": category_ids,
            "tags": tag_ids,
        }

    try:
        return asyncio.run(_run())
    except Exception as e:
        logger.error("WordPress publish failed: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}
