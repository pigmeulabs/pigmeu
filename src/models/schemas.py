from pydantic import BaseModel, HttpUrl, Field, field_validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.models.enums import SubmissionStatus, ArticleStatus, ServiceType


class SubmissionCreate(BaseModel):
    """Schema for creating a new submission."""
    title: str = Field(..., min_length=1, max_length=255)
    author_name: str = Field(..., min_length=1, max_length=255)
    amazon_url: HttpUrl
    goodreads_url: Optional[HttpUrl] = None
    author_site: Optional[HttpUrl] = None
    other_links: Optional[List[HttpUrl]] = []

    @field_validator("goodreads_url", "author_site", mode="before")
    @classmethod
    def empty_optional_urls_to_none(cls, value):
        if isinstance(value, str) and value.strip() == "":
            return None
        return value


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    id: str
    title: str
    author_name: str
    amazon_url: str
    goodreads_url: Optional[str] = None
    author_site: Optional[str] = None
    other_links: List[str] = []
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class BookExtracted(BaseModel):
    """Extracted book metadata."""
    title_original: Optional[str] = None
    authors: List[str] = []
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
    summary_text: str
    topics: List[str] = []
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
    title: str
    content: str
    word_count: int
    status: ArticleStatus
    created_at: datetime

    class Config:
        populate_by_name = True


class CredentialCreate(BaseModel):
    """Schema for creating a credential."""
    service: ServiceType
    key: str
    encrypted: bool = True


class PromptCreate(BaseModel):
    """Schema for creating a prompt."""
    name: str = Field(..., min_length=1, max_length=255)
    purpose: str
    system_prompt: str
    user_prompt: str
    model_id: str
    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2000, ge=1)
    schema_example: Optional[str] = None


class PromptResponse(BaseModel):
    """Schema for prompt response."""
    id: str
    name: str
    purpose: str
    system_prompt: str
    user_prompt: str
    model_id: str
    temperature: float
    max_tokens: int
    schema_example: Optional[str]
    created_at: datetime

    class Config:
        populate_by_name = True
