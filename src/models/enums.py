from enum import Enum


class SubmissionStatus(str, Enum):
    """Status of a submission processing."""

    PENDING_SCRAPE = "pending_scrape"
    SCRAPING_AMAZON = "scraping_amazon"
    SCRAPING_GOODREADS = "scraping_goodreads"
    SCRAPED = "scraped"
    PENDING_CONTEXT = "pending_context"
    CONTEXT_GENERATION = "context_generation"
    CONTEXT_GENERATED = "context_generated"
    PENDING_ARTICLE = "pending_article"
    ARTICLE_GENERATED = "article_generated"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SCRAPING_FAILED = "scraping_failed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Pipeline step status (for task progress)."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ArticleStatus(str, Enum):
    """Status of an article."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ServiceType(str, Enum):
    """Type of service credential."""

    OPENAI = "openai"
    GROQ = "groq"
    MISTRAL = "mistral"
    CLAUDE = "claude"
    WORDPRESS = "wordpress"
    AMAZON_PA_API = "amazon_pa_api"
