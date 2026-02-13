from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.models.enums import SubmissionStatus, ArticleStatus, ServiceType


class SchemaModel(BaseModel):
    """Base model for all schemas."""
    pass


class SubmissionCreate(BaseModel):
    """Schema for creating a new submission."""
    
    title: str = Field(..., description="Book title", min_length=1)
    author_name: str = Field(..., description="Author name", min_length=1)
    amazon_url: HttpUrl = Field(..., description="Amazon product URL")
    goodreads_url: Optional[HttpUrl] = Field(None, description="Goodreads book URL")
    author_site: Optional[HttpUrl] = Field(None, description="Author's website URL")
    other_links: Optional[List[HttpUrl]] = Field(default_factory=list, description="Other relevant links")
    textual_information: Optional[str] = Field(None, description="Additional text information about the book")
    run_immediately: bool = Field(True, description="Start processing immediately")
    schedule_execution: Optional[datetime] = Field(None, description="Schedule processing for later")
    pipeline_id: str = Field("book_review_v2", description="Pipeline configuration ID to use")
    main_category: Optional[str] = Field(None, description="Main category of the book")
    content_schema_id: Optional[str] = Field(None, description="Content schema to use for article generation")
    article_status: Optional[ArticleStatus] = Field(None, description="Initial article status")
    user_approval_required: bool = Field(False, description="Whether user approval is required before publishing")

    model_config = ConfigDict(populate_by_name=True)


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    
    id: str = Field(..., description="Submission ID")
    title: str
    author_name: str
    amazon_url: HttpUrl
    goodreads_url: Optional[HttpUrl] = None
    author_site: Optional[HttpUrl] = None
    other_links: List[HttpUrl] = Field(default_factory=list)
    textual_information: Optional[str] = None
    run_immediately: bool = True
    schedule_execution: Optional[datetime] = None
    pipeline_id: str
    main_category: Optional[str] = None
    content_schema_id: Optional[str] = None
    article_status: Optional[ArticleStatus] = None
    user_approval_required: bool = False
    status: SubmissionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class ArticleResponse(SchemaModel):
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
    approved_at: Optional[datetime] = None
    rejection_feedback: Optional[str] = None
    rejection_timestamp: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class CredentialCreate(BaseModel):
    """Schema for creating a credential."""
    
    service: ServiceType = Field(..., description="Service type")
    key: str = Field(..., description="API key or password", min_length=1)
    encrypted: bool = Field(False, description="Whether the key is already encrypted")
    name: Optional[str] = Field(None, description="Friendly name for this credential")
    url: Optional[str] = Field(None, description="Service URL (for WordPress)")
    username_email: Optional[str] = Field(None, description="Username or email")
    active: bool = Field(True, description="Whether this credential is active")

    model_config = ConfigDict(populate_by_name=True)


class CredentialUpdate(BaseModel):
    """Schema for updating a credential."""
    
    service: Optional[ServiceType] = None
    key: Optional[str] = None
    encrypted: Optional[bool] = None
    name: Optional[str] = None
    url: Optional[str] = None
    username_email: Optional[str] = None
    active: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class PromptCreate(BaseModel):
    """Schema for creating a prompt."""
    
    name: str = Field(..., description="Prompt name", min_length=1)
    purpose: str = Field(..., description="Purpose identifier", min_length=1)
    category: str = Field("Book Review", description="Prompt category")
    provider: Optional[str] = Field(None, description="AI provider (groq, mistral, openai, etc.)")
    short_description: Optional[str] = Field(None, description="Short description")
    system_prompt: Optional[str] = Field(None, description="System prompt text")
    user_prompt: Optional[str] = Field(None, description="User prompt template")
    model_id: Optional[str] = Field(None, description="Model identifier")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(2000, gt=0, description="Maximum tokens")
    expected_output_format: Optional[str] = Field(None, description="Expected output format")
    schema_example: Optional[str] = Field(None, description="Schema example")
    active: bool = Field(True, description="Whether this prompt is active")

    model_config = ConfigDict(populate_by_name=True)


class PromptUpdate(BaseModel):
    """Schema for updating a prompt."""
    
    name: Optional[str] = None
    purpose: Optional[str] = None
    category: Optional[str] = None
    provider: Optional[str] = None
    short_description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model_id: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0)
    expected_output_format: Optional[str] = None
    schema_example: Optional[str] = None
    active: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class PromptResponse(BaseModel):
    """Schema for prompt response."""
    
    id: str
    name: str
    purpose: str
    category: str
    provider: str
    short_description: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    model_id: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    expected_output_format: Optional[str] = None
    schema_example: Optional[str] = None
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)


class ContentSchemaCreate(BaseModel):
    """Schema for creating a content schema."""
    
    name: str = Field(..., description="Schema name", min_length=1)
    target_type: str = Field("book_review", description="Target content type")
    description: Optional[str] = Field(None, description="Schema description")
    min_total_words: Optional[int] = Field(None, gt=0, description="Minimum total words")
    max_total_words: Optional[int] = Field(None, gt=0, description="Maximum total words")
    toc_template: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Table of contents template")
    internal_links_count: int = Field(0, ge=0, description="Number of internal links")
    external_links_count: int = Field(0, ge=0, description="Number of external links")
    active: bool = Field(True, description="Whether this schema is active")

    model_config = ConfigDict(populate_by_name=True)


class ContentSchemaUpdate(BaseModel):
    """Schema for updating a content schema."""
    
    name: Optional[str] = None
    target_type: Optional[str] = None
    description: Optional[str] = None
    min_total_words: Optional[int] = Field(None, gt=0)
    max_total_words: Optional[int] = Field(None, gt=0)
    toc_template: Optional[List[Dict[str, Any]]] = None
    internal_links_count: Optional[int] = Field(None, ge=0)
    external_links_count: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class ContentSchemaResponse(BaseModel):
    """Schema for content schema response."""
    
    id: str
    name: str
    target_type: str = "book_review"
    description: Optional[str] = None
    min_total_words: Optional[int] = None
    max_total_words: Optional[int] = None
    toc_template: List[Dict[str, Any]] = Field(default_factory=list)
    internal_links_count: int = 0
    external_links_count: int = 0
    active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)
