from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel, HttpUrl, Field, field_validator, model_validator

from src.models.enums import SubmissionStatus, ArticleStatus, ServiceType
from src.workers.ai_defaults import DEFAULT_PROVIDER


class SubmissionCreate(BaseModel):
    """Schema for creating a new submission."""

    title: str = Field(..., min_length=1, max_length=255)
    author_name: str = Field(..., min_length=1, max_length=255)
    amazon_url: HttpUrl
    goodreads_url: Optional[HttpUrl] = None
    author_site: Optional[HttpUrl] = None
    other_links: List[HttpUrl] = Field(default_factory=list)

    textual_information: Optional[str] = None
    run_immediately: bool = True
    schedule_execution: Optional[datetime] = None
    pipeline_id: str = Field("book_review_v2", min_length=1, max_length=120)
    main_category: Optional[str] = None
    content_schema_id: Optional[str] = None
    article_status: Optional[str] = None
    user_approval_required: bool = False

    @field_validator("goodreads_url", "author_site", mode="before")
    @classmethod
    def empty_optional_urls_to_none(cls, value):
        if isinstance(value, str) and value.strip() == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_schedule_rule(self):
        if not self.run_immediately and self.schedule_execution is None:
            raise ValueError("schedule_execution is required when run_immediately is false")
        return self


class SubmissionResponse(BaseModel):
    """Schema for submission response."""

    id: str
    title: str
    author_name: str
    amazon_url: str
    goodreads_url: Optional[str] = None
    author_site: Optional[str] = None
    other_links: List[str] = Field(default_factory=list)

    textual_information: Optional[str] = None
    run_immediately: bool = True
    schedule_execution: Optional[datetime] = None
    pipeline_id: str = "book_review_v2"
    main_category: Optional[str] = None
    content_schema_id: Optional[str] = None
    article_status: Optional[str] = None
    user_approval_required: bool = False

    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class BookExtracted(BaseModel):
    """Extracted book metadata."""

    title_original: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    theme: Optional[str] = None
    lang_original: Optional[str] = None
    lang_edition: Optional[str] = None
    edition: Optional[str] = None
    pub_date: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    pages: Optional[int] = None
    price_physical: Optional[float] = None
    price_ebook: Optional[float] = None
    amazon_rating: Optional[float] = None


class BookResponse(BaseModel):
    """Schema for book response."""

    id: str
    submission_id: str
    extracted: BookExtracted
    last_updated: datetime

    class Config:
        populate_by_name = True


class SummaryResponse(BaseModel):
    """Schema for summary response."""

    id: str
    book_id: str
    source_url: str
    source_domain: Optional[str] = None
    summary_text: str
    topics: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    credibility: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True


class ArticleSection(BaseModel):
    """Article section structure."""

    h2: str
    content: str
    h3_subsections: Optional[List[Dict[str, str]]] = None


class ArticleResponse(BaseModel):
    """Schema for article response."""

    id: str
    book_id: str
    submission_id: Optional[str] = None
    title: str
    content: str
    word_count: int
    status: ArticleStatus
    wordpress_post_id: Optional[str] = None
    wordpress_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class CredentialCreate(BaseModel):
    """Schema for creating a credential."""

    service: ServiceType
    key: str = Field(..., min_length=1)
    encrypted: bool = True
    name: Optional[str] = None
    url: Optional[str] = None
    username_email: Optional[str] = None
    active: bool = True


class CredentialUpdate(BaseModel):
    """Schema for updating a credential."""

    key: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    username_email: Optional[str] = None
    active: Optional[bool] = None


class PromptCreate(BaseModel):
    """Schema for creating a prompt."""

    name: str = Field(..., min_length=1, max_length=255)
    purpose: str
    category: str = Field("Book Review", min_length=1, max_length=120)
    provider: str = Field(DEFAULT_PROVIDER, min_length=1, max_length=80)
    short_description: Optional[str] = None
    system_prompt: str
    user_prompt: str
    model_id: str
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2000, ge=1)
    expected_output_format: Optional[str] = None
    schema_example: Optional[str] = None
    active: bool = True


class PromptUpdate(BaseModel):
    """Schema for updating prompt fields."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    purpose: Optional[str] = None
    category: Optional[str] = Field(None, min_length=1, max_length=120)
    provider: Optional[str] = Field(None, min_length=1, max_length=80)
    short_description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model_id: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1)
    expected_output_format: Optional[str] = None
    schema_example: Optional[str] = None
    active: Optional[bool] = None


class PromptResponse(BaseModel):
    """Schema for prompt response."""

    id: str
    name: str
    purpose: str
    category: str = "Book Review"
    provider: str = DEFAULT_PROVIDER
    short_description: Optional[str] = None
    system_prompt: str
    user_prompt: str
    model_id: str
    temperature: float
    max_tokens: int
    expected_output_format: Optional[str] = None
    schema_example: Optional[str] = None
    active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ContentSchemaTocItem(BaseModel):
    """TOC item configuration for article generation schema."""

    level: Literal["h2", "h3"] = "h2"
    title_template: str = Field(..., min_length=1, max_length=255)
    content_mode: Literal["specific", "dynamic"] = "dynamic"
    specific_content_hint: Optional[str] = None
    min_paragraphs: Optional[int] = Field(None, ge=0)
    max_paragraphs: Optional[int] = Field(None, ge=0)
    min_words: Optional[int] = Field(None, ge=0)
    max_words: Optional[int] = Field(None, ge=0)
    source_fields: List[str] = Field(default_factory=list)
    prompt_id: Optional[str] = None
    position: int = Field(0, ge=0)

    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.min_paragraphs is not None
            and self.max_paragraphs is not None
            and self.max_paragraphs < self.min_paragraphs
        ):
            raise ValueError("max_paragraphs must be greater than or equal to min_paragraphs")

        if self.min_words is not None and self.max_words is not None and self.max_words < self.min_words:
            raise ValueError("max_words must be greater than or equal to min_words")

        return self


class ContentSchemaCreate(BaseModel):
    """Schema for creating a content schema document."""

    name: str = Field(..., min_length=1, max_length=255)
    target_type: str = Field("book_review", min_length=1, max_length=100)
    description: Optional[str] = None
    min_total_words: Optional[int] = Field(None, ge=0)
    max_total_words: Optional[int] = Field(None, ge=0)
    toc_template: List[ContentSchemaTocItem] = Field(default_factory=list)
    internal_links_count: int = Field(0, ge=0)
    external_links_count: int = Field(0, ge=0)
    active: bool = True

    @model_validator(mode="after")
    def validate_total_word_range(self):
        if (
            self.min_total_words is not None
            and self.max_total_words is not None
            and self.max_total_words < self.min_total_words
        ):
            raise ValueError("max_total_words must be greater than or equal to min_total_words")
        return self


class ContentSchemaUpdate(BaseModel):
    """Schema for updating content schema fields."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    min_total_words: Optional[int] = Field(None, ge=0)
    max_total_words: Optional[int] = Field(None, ge=0)
    toc_template: Optional[List[ContentSchemaTocItem]] = None
    internal_links_count: Optional[int] = Field(None, ge=0)
    external_links_count: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None

    @model_validator(mode="after")
    def validate_total_word_range(self):
        if (
            self.min_total_words is not None
            and self.max_total_words is not None
            and self.max_total_words < self.min_total_words
        ):
            raise ValueError("max_total_words must be greater than or equal to min_total_words")
        return self


class ContentSchemaResponse(BaseModel):
    """Schema for content schema response."""

    id: str
    name: str
    target_type: str
    description: Optional[str] = None
    min_total_words: Optional[int] = None
    max_total_words: Optional[int] = None
    toc_template: List[ContentSchemaTocItem] = Field(default_factory=list)
    internal_links_count: int = 0
    external_links_count: int = 0
    active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class ArticleDraftPayload(BaseModel):
    """Payload for saving draft article content."""

    content: str = Field(..., min_length=1)
