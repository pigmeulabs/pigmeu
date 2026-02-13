"""
Settings API: manage credentials and prompt templates.

Endpoints:
- GET/POST/PATCH/DELETE /settings/credentials
- GET /settings/wordpress/categories
- GET/POST/PATCH/DELETE /settings/prompts
- GET /settings/prompt-categories
- GET/POST/PATCH/DELETE /settings/content-schemas
- GET/PATCH /settings/pipelines
"""

import logging
import base64
from copy import deepcopy
from typing import List, Optional, Dict, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body

from src.api.dependencies import (
    get_credential_repo,
    get_prompt_repo,
    get_pipeline_repo,
    get_content_schema_repo,
)
from src.models.schemas import (
    CredentialCreate,
    CredentialUpdate,
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    ContentSchemaCreate,
    ContentSchemaUpdate,
    ContentSchemaResponse,
)
from src.workers.ai_defaults import (
    BOOK_REVIEW_ARTICLE_MODEL_ID,
    BOOK_REVIEW_ARTICLE_PROVIDER,
    BOOK_REVIEW_CONTEXT_MODEL_ID,
    BOOK_REVIEW_CONTEXT_PROVIDER,
    DEFAULT_PROVIDER,
    MODEL_GROQ_LLAMA_3_3_70B,
    MODEL_MISTRAL_LARGE_LATEST,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


BOOK_REVIEW_PIPELINE_ID = "book_review_v2"
LINKS_CONTENT_PIPELINE_ID = "links_content_v1"
DEFAULT_SUBMISSION_PIPELINE_ID = BOOK_REVIEW_PIPELINE_ID
DEFAULT_WORDPRESS_URL = "https://analisederequisitos.com.br"
DEFAULT_WORDPRESS_PASSWORD = "M3LS c2ny NdF1 5Xap 1tmT ibSg"

BOOK_REVIEW_PIPELINE_TEMPLATE: Dict[str, Any] = {
    "name": "Book Review",
    "slug": "book-review",
    "description": "Pipeline para extracao de dados, consolidacao de contexto e geracao de conteudo de Book Review.",
    "usage_type": "content_copilot",
    "version": "2.0",
    "steps": [
        {
            "id": "amazon_scrape",
            "name": "Amazon link scrape",
            "description": "Extrai metadados bibliograficos da pagina do livro na Amazon.",
            "type": "scraping",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "additional_links_scrape",
            "name": "Additional links scrape",
            "description": "Processa links adicionais e extrai dados bibliograficos via IA.",
            "type": "scraping+llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "mistral",
                "model_id": MODEL_MISTRAL_LARGE_LATEST,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "Mistral A",
                "default_prompt_purpose": "book_review_link_bibliography_extract",
            },
        },
        {
            "id": "summarize_additional_links",
            "name": "Summarize additional links",
            "description": "Gera resumo dos links adicionais com foco em livro e autor.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "groq",
                "model_id": MODEL_GROQ_LLAMA_3_3_70B,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "book_review_link_summary",
            },
        },
        {
            "id": "consolidate_book_data",
            "name": "Consolidate book data",
            "description": "Consolida dados bibliograficos sem duplicidade.",
            "type": "data-processing",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "internet_research",
            "name": "Internet research",
            "description": "Pesquisa web sobre livro/autor e sintetiza assuntos e temas.",
            "type": "search+llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "groq",
                "model_id": MODEL_GROQ_LLAMA_3_3_70B,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "book_review_web_research",
            },
        },
        {
            "id": "context_generation",
            "name": "Generate context",
            "description": "Gera base de conhecimento consolidada para suportar a escrita.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": BOOK_REVIEW_CONTEXT_PROVIDER,
                "model_id": BOOK_REVIEW_CONTEXT_MODEL_ID,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "context",
            },
        },
        {
            "id": "article_generation",
            "name": "Generate article",
            "description": "Gera artigo final em markdown a partir do contexto produzido.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": BOOK_REVIEW_ARTICLE_PROVIDER,
                "model_id": BOOK_REVIEW_ARTICLE_MODEL_ID,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "Mistral A",
                "default_prompt_purpose": "article",
            },
        },
        {
            "id": "ready_for_review",
            "name": "Ready for review",
            "description": "Etapa final de aprovacao para revisao/publicacao.",
            "type": "workflow",
            "uses_ai": False,
            "delay_seconds": 0,
        },
    ],
}

LINKS_CONTENT_PIPELINE_TEMPLATE: Dict[str, Any] = {
    "name": "Links Content",
    "slug": "links-content",
    "description": "Pipeline para gerar artigo a partir de links fornecidos pelo usuario.",
    "usage_type": "content_copilot",
    "version": "1.0",
    "steps": [
        {
            "id": "links_scrape",
            "name": "Analyze source links",
            "description": "Leitura e analise de cada link informado para extrair dados relevantes.",
            "type": "scraping+llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "groq",
                "model_id": MODEL_GROQ_LLAMA_3_3_70B,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "links_content_analyze",
            },
        },
        {
            "id": "extract_facts",
            "name": "Extract structured facts",
            "description": "Extrai fatos estruturados dos links processados.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": "mistral",
                "model_id": MODEL_MISTRAL_LARGE_LATEST,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "Mistral A",
                "default_prompt_purpose": "links_content_extract_facts",
            },
        },
        {
            "id": "consolidate_data",
            "name": "Consolidate data",
            "description": "Consolida dados sem duplicidades e prepara contexto.",
            "type": "data-processing",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "context_generation",
            "name": "Generate context",
            "description": "Gera contexto estruturado para redação do artigo.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": BOOK_REVIEW_CONTEXT_PROVIDER,
                "model_id": BOOK_REVIEW_CONTEXT_MODEL_ID,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "GROC A",
                "default_prompt_purpose": "context",
            },
        },
        {
            "id": "article_generation",
            "name": "Generate article",
            "description": "Gera artigo final em markdown a partir dos dados consolidados.",
            "type": "llm",
            "uses_ai": True,
            "delay_seconds": 0,
            "ai": {
                "provider": BOOK_REVIEW_ARTICLE_PROVIDER,
                "model_id": BOOK_REVIEW_ARTICLE_MODEL_ID,
                "credential_id": None,
                "prompt_id": None,
                "default_credential_name": "Mistral A",
                "default_prompt_purpose": "article",
            },
        },
        {
            "id": "quality_validation",
            "name": "Quality validation",
            "description": "Valida estrutura, consistencia e requisitos de qualidade do artigo.",
            "type": "quality-gate",
            "uses_ai": False,
            "delay_seconds": 0,
        },
        {
            "id": "ready_for_review",
            "name": "Ready for review",
            "description": "Etapa final de aprovacao para revisao/publicacao.",
            "type": "workflow",
            "uses_ai": False,
            "delay_seconds": 0,
        },
    ],
}

PIPELINE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    BOOK_REVIEW_PIPELINE_ID: BOOK_REVIEW_PIPELINE_TEMPLATE,
    LINKS_CONTENT_PIPELINE_ID: LINKS_CONTENT_PIPELINE_TEMPLATE,
}

DEFAULT_BOOTSTRAP_CREDENTIALS: List[Dict[str, Any]] = [
    {
        "name": "Mistral A",
        "service": "mistral",
        "key": "CN9fTAtnszPRB9HNSvOCSdeQltb86RGL",
        "active": True,
    },
    {
        "name": "GROC A",
        "service": "groq",
        "key": "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",
        "active": True,
    },
    {
        "name": "Wordpress Default",
        "service": "wordpress",
        "key": DEFAULT_WORDPRESS_PASSWORD,
        "url": DEFAULT_WORDPRESS_URL,
        "username_email": "",
        "active": True,
    },
]

DEFAULT_CONTENT_SCHEMA_NAME = "Book Review - Estrutura Completa v1"


def _pipeline_card_response(doc: Dict[str, Any]) -> Dict[str, Any]:
    steps = doc.get("steps", []) if isinstance(doc.get("steps"), list) else []
    ai_steps = [step for step in steps if bool(step.get("uses_ai"))]
    return {
        "id": doc.get("pipeline_id"),
        "name": doc.get("name"),
        "slug": doc.get("slug"),
        "description": doc.get("description"),
        "usage_type": doc.get("usage_type"),
        "version": doc.get("version"),
        "steps_count": len(steps),
        "ai_steps_count": len(ai_steps),
    }


def _credential_option(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name"),
        "url": _extract_credential_url(doc),
        "service": doc.get("service"),
        "active": bool(doc.get("active", True)),
    }


def _prompt_option(doc: Dict[str, Any]) -> Dict[str, Any]:
    model_id = str(doc.get("model_id") or "").strip()
    provider = str(doc.get("provider") or "").strip().lower()
    if not provider:
        if model_id.startswith("mistral"):
            provider = "mistral"
        elif model_id.startswith("llama") or model_id.startswith("mixtral"):
            provider = "groq"
        else:
            provider = DEFAULT_PROVIDER

    return {
        "id": str(doc.get("_id")),
        "name": doc.get("name"),
        "purpose": doc.get("purpose"),
        "category": doc.get("category") or "Book Review",
        "provider": provider,
        "model_id": doc.get("model_id"),
        "active": bool(doc.get("active", True)),
    }


def _prompt_response(doc: Dict[str, Any]) -> PromptResponse:
    model_id = str(doc.get("model_id") or "").strip()
    provider = str(doc.get("provider") or "").strip().lower()
    if not provider:
        if model_id.startswith("mistral"):
            provider = "mistral"
        elif model_id.startswith("llama") or model_id.startswith("mixtral"):
            provider = "groq"
        else:
            provider = DEFAULT_PROVIDER

    return PromptResponse(
        id=str(doc.get("_id")),
        name=doc.get("name"),
        purpose=doc.get("purpose"),
        category=doc.get("category") or "Book Review",
        provider=provider,
        short_description=doc.get("short_description"),
        system_prompt=doc.get("system_prompt"),
        user_prompt=doc.get("user_prompt"),
        model_id=doc.get("model_id"),
        temperature=doc.get("temperature", 0.7),
        max_tokens=doc.get("max_tokens", 2000),
        expected_output_format=doc.get("expected_output_format"),
        schema_example=doc.get("schema_example"),
        active=doc.get("active", True),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


def _content_schema_response(doc: Dict[str, Any]) -> ContentSchemaResponse:
    toc_template = doc.get("toc_template") if isinstance(doc.get("toc_template"), list) else []
    return ContentSchemaResponse(
        id=str(doc.get("_id")),
        name=doc.get("name"),
        target_type=doc.get("target_type", "book_review"),
        description=doc.get("description"),
        min_total_words=doc.get("min_total_words"),
        max_total_words=doc.get("max_total_words"),
        toc_template=toc_template,
        internal_links_count=doc.get("internal_links_count", 0),
        external_links_count=doc.get("external_links_count", 0),
        active=bool(doc.get("active", True)),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


def _safe_delay_seconds(value: Any) -> int:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _extract_credential_url(doc: Dict[str, Any]) -> Optional[str]:
    url = str(doc.get("url") or "").strip()
    if url:
        return url.rstrip("/")

    name = str(doc.get("name") or "").strip()
    if name.startswith("http://") or name.startswith("https://"):
        return name.rstrip("/")

    return None


def _build_wordpress_auth_headers(doc: Dict[str, Any]) -> Dict[str, str]:
    username = str(doc.get("username_email") or "").strip()
    password = str(doc.get("key") or "").strip()
    if not username or not password:
        return {}

    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {token}"}


def _pick_default_wordpress_credential(items: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not items:
        return None

    by_default_url = next(
        (
            item
            for item in items
            if str(_extract_credential_url(item) or "").lower() == DEFAULT_WORDPRESS_URL.lower().rstrip("/")
        ),
        None,
    )
    if by_default_url:
        return by_default_url

    return items[0]


async def _fetch_wordpress_categories_from_site(credential_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    wordpress_url = _extract_credential_url(credential_doc)
    if not wordpress_url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected credential has no WordPress URL configured",
        )

    endpoint = f"{wordpress_url}/wp-json/wp/v2/categories"
    categories: List[Dict[str, Any]] = []
    page = 1
    headers = _build_wordpress_auth_headers(credential_doc)

    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            response = await client.get(
                endpoint,
                params={
                    "per_page": 100,
                    "page": page,
                    "orderby": "name",
                    "order": "asc",
                    "_fields": "id,name,slug",
                },
                headers=headers,
            )

            if response.status_code in (400, 401, 403):
                # Retry without auth for public category listing.
                response = await client.get(
                    endpoint,
                    params={
                        "per_page": 100,
                        "page": page,
                        "orderby": "name",
                        "order": "asc",
                        "_fields": "id,name,slug",
                    },
                )

            if response.status_code == 400:
                # WordPress returns 400 for page out of range in some setups.
                break

            response.raise_for_status()
            batch = response.json()
            if not isinstance(batch, list) or len(batch) == 0:
                break

            for item in batch:
                categories.append(
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "slug": item.get("slug"),
                    }
                )

            if len(batch) < 100:
                break
            page += 1

    return categories


def _default_book_review_content_schema_payload() -> Dict[str, Any]:
    toc_template = [
        {
            "level": "h2",
            "title_template": "Introdução ao Tema do Livro",
            "content_mode": "specific",
            "specific_content_hint": "Abrir com contexto claro, relevância prática e promessa de valor para o leitor.",
            "min_paragraphs": 2,
            "max_paragraphs": 4,
            "min_words": 150,
            "max_words": 240,
            "source_fields": ["title", "author", "consolidated_bibliographic.theme", "web_research.topics"],
            "prompt_id": None,
            "position": 0,
        },
        {
            "level": "h2",
            "title_template": "Resumo da Obra",
            "content_mode": "specific",
            "specific_content_hint": "Síntese do argumento central, sem spoiler excessivo, em tom objetivo.",
            "min_paragraphs": 2,
            "max_paragraphs": 4,
            "min_words": 150,
            "max_words": 240,
            "source_fields": ["context_markdown", "summaries.summary_text", "consolidated_bibliographic"],
            "prompt_id": None,
            "position": 1,
        },
        {
            "level": "h2",
            "title_template": "Contexto e Motivação",
            "content_mode": "specific",
            "specific_content_hint": "Problemas que o livro resolve e lacunas na literatura.",
            "min_paragraphs": 2,
            "max_paragraphs": 4,
            "min_words": 150,
            "max_words": 240,
            "source_fields": ["consolidated_bibliographic", "web_research.key_insights"],
            "prompt_id": None,
            "position": 2,
        },
        {
            "level": "h2",
            "title_template": "Impacto e Aplicabilidade",
            "content_mode": "dynamic",
            "specific_content_hint": "Aplicação prática dos conceitos e casos de uso.",
            "min_paragraphs": 2,
            "max_paragraphs": 4,
            "min_words": 150,
            "max_words": 280,
            "source_fields": ["web_research.research_markdown", "summaries.summary_text"],
            "prompt_id": None,
            "position": 3,
        },
        {
            "level": "h2",
            "title_template": "[Tópico Específico do Livro]",
            "content_mode": "dynamic",
            "specific_content_hint": "Selecionar o tópico mais relevante ao livro com base nos dados consolidados.",
            "min_paragraphs": 3,
            "max_paragraphs": 5,
            "min_words": 200,
            "max_words": 360,
            "source_fields": ["web_research.topics", "summaries.topics"],
            "prompt_id": None,
            "position": 4,
        },
        {
            "level": "h3",
            "title_template": "[Subtema 1]",
            "content_mode": "dynamic",
            "specific_content_hint": "",
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "min_words": 80,
            "max_words": 160,
            "source_fields": ["summaries.key_points"],
            "prompt_id": None,
            "position": 5,
        },
        {
            "level": "h3",
            "title_template": "[Subtema 2]",
            "content_mode": "dynamic",
            "specific_content_hint": "",
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "min_words": 80,
            "max_words": 160,
            "source_fields": ["summaries.key_points"],
            "prompt_id": None,
            "position": 6,
        },
        {
            "level": "h3",
            "title_template": "[Subtema 3] (opcional)",
            "content_mode": "dynamic",
            "specific_content_hint": "",
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "min_words": 80,
            "max_words": 160,
            "source_fields": ["summaries.key_points"],
            "prompt_id": None,
            "position": 7,
        },
        {
            "level": "h3",
            "title_template": "[Subtema 4] (opcional)",
            "content_mode": "dynamic",
            "specific_content_hint": "",
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "min_words": 80,
            "max_words": 160,
            "source_fields": ["summaries.key_points"],
            "prompt_id": None,
            "position": 8,
        },
        {
            "level": "h2",
            "title_template": "Pontos Fortes e Limitações",
            "content_mode": "specific",
            "specific_content_hint": "Avaliação crítica equilibrada: vantagens práticas e limites do livro.",
            "min_paragraphs": 2,
            "max_paragraphs": 3,
            "min_words": 120,
            "max_words": 220,
            "source_fields": ["summaries.key_points", "web_research.key_insights", "context_markdown"],
            "prompt_id": None,
            "position": 9,
        },
        {
            "level": "h2",
            "title_template": "Detalhes do Livro",
            "content_mode": "specific",
            "specific_content_hint": "Incluir dados bibliográficos técnicos com links para Amazon/Goodreads.",
            "min_paragraphs": 1,
            "max_paragraphs": 3,
            "min_words": 100,
            "max_words": 220,
            "source_fields": ["consolidated_bibliographic", "metadata.amazon_url", "goodreads_url"],
            "prompt_id": None,
            "position": 10,
        },
        {
            "level": "h2",
            "title_template": "Sobre o Autor",
            "content_mode": "specific",
            "specific_content_hint": "Biografia resumida e principais obras.",
            "min_paragraphs": 1,
            "max_paragraphs": 3,
            "min_words": 100,
            "max_words": 220,
            "source_fields": ["author", "web_research.research_markdown", "summaries.summary_text"],
            "prompt_id": None,
            "position": 11,
        },
        {
            "level": "h2",
            "title_template": "Conclusão e Recomendação",
            "content_mode": "specific",
            "specific_content_hint": "Encerrar com recomendação objetiva: para quem vale a leitura e por quê.",
            "min_paragraphs": 2,
            "max_paragraphs": 3,
            "min_words": 100,
            "max_words": 180,
            "source_fields": ["context_markdown", "summaries.summary_text", "web_research.key_insights"],
            "prompt_id": None,
            "position": 12,
        },
        {
            "level": "h2",
            "title_template": "Perguntas Frequentes",
            "content_mode": "dynamic",
            "specific_content_hint": "Gerar 3-5 perguntas e respostas curtas em formato de FAQ.",
            "min_paragraphs": 2,
            "max_paragraphs": 4,
            "min_words": 100,
            "max_words": 200,
            "source_fields": ["web_research.faq_candidates", "summaries.summary_text", "context_markdown"],
            "prompt_id": None,
            "position": 13,
        },
        {
            "level": "h2",
            "title_template": "Onde Comprar e Formatos",
            "content_mode": "specific",
            "specific_content_hint": "Links para compra/download legal do livro.",
            "min_paragraphs": 1,
            "max_paragraphs": 2,
            "min_words": 60,
            "max_words": 140,
            "source_fields": ["metadata.amazon_url", "goodreads_url", "other_links"],
            "prompt_id": None,
            "position": 14,
        },
        {
            "level": "h2",
            "title_template": "Assuntos Relacionados",
            "content_mode": "dynamic",
            "specific_content_hint": "Lista de tópicos com links internos para SEO.",
            "min_paragraphs": 1,
            "max_paragraphs": 3,
            "min_words": 80,
            "max_words": 180,
            "source_fields": ["web_research.topics", "summaries.topics"],
            "prompt_id": None,
            "position": 15,
        },
        {
            "level": "h2",
            "title_template": "Artigos Recomendados",
            "content_mode": "dynamic",
            "specific_content_hint": "Incluir 3-5 artigos relacionados com links internos.",
            "min_paragraphs": 1,
            "max_paragraphs": 3,
            "min_words": 80,
            "max_words": 180,
            "source_fields": ["web_research.topics"],
            "prompt_id": None,
            "position": 16,
        },
    ]

    return {
        "name": DEFAULT_CONTENT_SCHEMA_NAME,
        "target_type": "book_review",
        "description": "Schema padrão editorial para book review técnico em pt-BR, com foco em SEO e aplicabilidade.",
        "min_total_words": 1600,
        "max_total_words": 3200,
        "toc_template": toc_template,
        "internal_links_count": 5,
        "external_links_count": 3,
        "active": True,
    }


async def _ensure_default_credentials(credential_repo) -> None:
    existing = await credential_repo.list_all()
    indexed = {
        (str(item.get("service") or "").strip().lower(), str(item.get("name") or "").strip().lower()): item
        for item in existing
    }
    for item in DEFAULT_BOOTSTRAP_CREDENTIALS:
        key = (str(item.get("service") or "").lower(), str(item.get("name") or "").lower())
        found = indexed.get(key)
        if found:
            update_fields: Dict[str, Any] = {}
            if item.get("url") and not found.get("url"):
                update_fields["url"] = item.get("url")
            if item.get("username_email") is not None and found.get("username_email") in (None, ""):
                update_fields["username_email"] = item.get("username_email")
            if not bool(found.get("active", True)):
                update_fields["active"] = True
            if update_fields:
                await credential_repo.update(str(found.get("_id")), update_fields)
            continue

        await credential_repo.create(
            service=str(item.get("service")),
            key=str(item.get("key") or ""),
            encrypted=True,
            name=str(item.get("name") or item.get("service") or ""),
            url=item.get("url"),
            username_email=item.get("username_email"),
            active=bool(item.get("active", True)),
        )


async def _ensure_default_content_schema(content_schema_repo) -> None:
    all_items = await content_schema_repo.list_all()
    exists = any(str(item.get("name") or "") == DEFAULT_CONTENT_SCHEMA_NAME for item in all_items)
    if exists:
        return
    await content_schema_repo.create(_default_book_review_content_schema_payload())


async def _ensure_default_pipelines(pipeline_repo) -> None:
    for pipeline_id, template in PIPELINE_TEMPLATES.items():
        existing = await pipeline_repo.get_by_pipeline_id(pipeline_id)
        if existing:
            continue
        await pipeline_repo.create_or_update(pipeline_id, deepcopy(template))


async def _ensure_system_defaults(
    pipeline_repo,
    credential_repo=None,
    content_schema_repo=None,
) -> None:
    await _ensure_default_pipelines(pipeline_repo)
    if credential_repo is not None:
        await _ensure_default_credentials(credential_repo)
    if content_schema_repo is not None:
        await _ensure_default_content_schema(content_schema_repo)


async def _ensure_pipeline_by_id(pipeline_repo, pipeline_id: str) -> Optional[Dict[str, Any]]:
    normalized = str(pipeline_id or "").strip()
    if not normalized:
        return None

    doc = await pipeline_repo.get_by_pipeline_id(normalized)
    if doc:
        return doc

    template = PIPELINE_TEMPLATES.get(normalized)
    if not template:
        return None

    await pipeline_repo.create_or_update(normalized, deepcopy(template))
    return await pipeline_repo.get_by_pipeline_id(normalized)


async def _build_pipeline_detail_response(
    pipeline_doc: Dict[str, Any],
    credential_repo,
    prompt_repo,
) -> Dict[str, Any]:
    credentials = await credential_repo.list_all()
    prompts = await prompt_repo.list_all(limit=300)

    credential_options = [_credential_option(item) for item in credentials]
    prompt_options = [_prompt_option(item) for item in prompts]
    cred_by_id = {item["id"]: item for item in credential_options}
    prompt_by_id = {item["id"]: item for item in prompt_options}

    steps: List[Dict[str, Any]] = []
    raw_steps = pipeline_doc.get("steps", []) if isinstance(pipeline_doc.get("steps"), list) else []
    for item in raw_steps:
        step = {
            "id": item.get("id"),
            "name": item.get("name"),
            "description": item.get("description"),
            "type": item.get("type"),
            "uses_ai": bool(item.get("uses_ai")),
            "delay_seconds": _safe_delay_seconds(item.get("delay_seconds", 0)),
        }

        if step["uses_ai"]:
            ai = item.get("ai", {}) if isinstance(item.get("ai"), dict) else {}
            selected_credential = cred_by_id.get(str(ai.get("credential_id") or ""))
            selected_prompt = prompt_by_id.get(str(ai.get("prompt_id") or ""))
            step["ai"] = {
                "provider": ai.get("provider"),
                "model_id": ai.get("model_id"),
                "credential_id": str(ai.get("credential_id")) if ai.get("credential_id") else None,
                "credential_name": selected_credential.get("name") if selected_credential else None,
                "credential_service": selected_credential.get("service") if selected_credential else None,
                "prompt_id": str(ai.get("prompt_id")) if ai.get("prompt_id") else None,
                "prompt_name": selected_prompt.get("name") if selected_prompt else None,
                "prompt_purpose": selected_prompt.get("purpose") if selected_prompt else ai.get("default_prompt_purpose"),
                "default_credential_name": ai.get("default_credential_name"),
                "default_prompt_purpose": ai.get("default_prompt_purpose"),
            }

        steps.append(step)

    return {
        "id": pipeline_doc.get("pipeline_id"),
        "name": pipeline_doc.get("name"),
        "slug": pipeline_doc.get("slug"),
        "description": pipeline_doc.get("description"),
        "usage_type": pipeline_doc.get("usage_type"),
        "version": pipeline_doc.get("version"),
        "steps": steps,
        "available_credentials": credential_options,
        "available_prompts": prompt_options,
    }


def _mask_credential(doc: dict) -> dict:
    item = {**doc}
    item["id"] = str(item.get("_id"))
    item.pop("_id", None)
    item["url"] = _extract_credential_url(item)

    key = item.get("key")
    if isinstance(key, str) and len(key) > 8:
        item["key"] = key[:4] + "..." + key[-4:]
    elif isinstance(key, str):
        item["key"] = "****"

    return item


@router.get("/credentials", response_model=List[dict])
async def list_credentials(
    service: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    repo=Depends(get_credential_repo),
):
    try:
        if active is True:
            items = await repo.list_active(service=service)
        else:
            items = await repo.list_all()
            if service:
                items = [item for item in items if item.get("service") == service]
            if active is not None:
                items = [item for item in items if bool(item.get("active", True)) is active]

        return [_mask_credential(item) for item in items]
    except Exception as e:
        logger.error("Error listing credentials: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/credentials/{cred_id}", response_model=dict)
async def get_credential(cred_id: str, repo=Depends(get_credential_repo)):
    doc = await repo.get_by_id(cred_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    return _mask_credential(doc)


@router.post("/credentials", status_code=status.HTTP_201_CREATED)
async def create_credential(payload: CredentialCreate, repo=Depends(get_credential_repo)):
    try:
        cid = await repo.create(
            service=payload.service.value,
            key=payload.key,
            encrypted=payload.encrypted,
            name=payload.name,
            url=payload.url,
            username_email=payload.username_email,
            active=payload.active,
        )
        return {"id": cid, "service": payload.service.value}
    except Exception as e:
        logger.error("Error creating credential: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/credentials/{cred_id}", status_code=status.HTTP_200_OK)
async def update_credential(cred_id: str, payload: CredentialUpdate, repo=Depends(get_credential_repo)):
    existing = await repo.get_by_id(cred_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")

    ok = await repo.update(cred_id, update_data)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update credential")

    updated = await repo.get_by_id(cred_id)
    return _mask_credential(updated)


@router.delete("/credentials/{cred_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(cred_id: str, repo=Depends(get_credential_repo)):
    try:
        ok = await repo.delete(cred_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting credential: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/wordpress/categories", response_model=dict)
async def list_wordpress_categories(
    credential_id: Optional[str] = Query(None),
    credential_repo=Depends(get_credential_repo),
):
    try:
        selected_credential: Optional[Dict[str, Any]] = None

        if credential_id:
            doc = await credential_repo.get_by_id(credential_id)
            if not doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
            if str(doc.get("service")) != "wordpress":
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Selected credential is not a WordPress credential",
                )
            if not bool(doc.get("active", True)):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Selected credential is inactive",
                )
            selected_credential = doc
        else:
            active_wp_credentials = await credential_repo.list_active(service="wordpress")
            selected_credential = _pick_default_wordpress_credential(active_wp_credentials)

        if not selected_credential:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active WordPress credential found")

        categories = await _fetch_wordpress_categories_from_site(selected_credential)
        await credential_repo.touch_last_used(str(selected_credential.get("_id")))

        return {
            "credential_id": str(selected_credential.get("_id")),
            "credential_name": selected_credential.get("name"),
            "credential_url": _extract_credential_url(selected_credential),
            "categories": categories,
            "count": len(categories),
        }
    except HTTPException:
        raise
    except httpx.HTTPError as e:
        logger.error("Error fetching WordPress categories: %s", e)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to fetch WordPress categories")
    except Exception as e:
        logger.error("Unexpected error fetching WordPress categories: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/content-schemas", response_model=List[ContentSchemaResponse])
async def list_content_schemas(
    active: Optional[bool] = Query(None),
    target_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    repo=Depends(get_content_schema_repo),
):
    try:
        items = await repo.list_all(active=active, target_type=target_type, search=search)
        return [_content_schema_response(item) for item in items]
    except Exception as e:
        logger.error("Error listing content schemas: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/content-schemas/{schema_id}", response_model=ContentSchemaResponse)
async def get_content_schema(schema_id: str, repo=Depends(get_content_schema_repo)):
    try:
        doc = await repo.get_by_id(schema_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content schema not found")
        return _content_schema_response(doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching content schema: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/content-schemas", status_code=status.HTTP_201_CREATED, response_model=ContentSchemaResponse)
async def create_content_schema(payload: ContentSchemaCreate, repo=Depends(get_content_schema_repo)):
    try:
        schema_id = await repo.create(payload.model_dump())
        doc = await repo.get_by_id(schema_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create content schema")
        return _content_schema_response(doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating content schema: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/content-schemas/{schema_id}", response_model=ContentSchemaResponse)
async def update_content_schema(
    schema_id: str,
    payload: ContentSchemaUpdate,
    repo=Depends(get_content_schema_repo),
):
    existing = await repo.get_by_id(schema_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content schema not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")

    merged_min_words = (
        update_data["min_total_words"]
        if "min_total_words" in update_data
        else existing.get("min_total_words")
    )
    merged_max_words = (
        update_data["max_total_words"]
        if "max_total_words" in update_data
        else existing.get("max_total_words")
    )
    if (
        merged_min_words is not None
        and merged_max_words is not None
        and merged_max_words < merged_min_words
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="max_total_words must be greater than or equal to min_total_words",
        )

    ok = await repo.update(schema_id, update_data)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update content schema")

    doc = await repo.get_by_id(schema_id)
    return _content_schema_response(doc)


@router.delete("/content-schemas/{schema_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_schema(schema_id: str, repo=Depends(get_content_schema_repo)):
    try:
        ok = await repo.delete(schema_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting content schema: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/pipelines", response_model=List[dict])
async def list_pipelines(
    pipeline_repo=Depends(get_pipeline_repo),
    credential_repo=Depends(get_credential_repo),
    content_schema_repo=Depends(get_content_schema_repo),
):
    try:
        await _ensure_system_defaults(
            pipeline_repo=pipeline_repo,
            credential_repo=credential_repo,
            content_schema_repo=content_schema_repo,
        )
        items = await pipeline_repo.list_all()
        return [_pipeline_card_response(item) for item in items]
    except Exception as e:
        logger.error("Error listing pipelines: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list pipelines")


@router.get("/pipelines/{pipeline_id}", response_model=dict)
async def get_pipeline_detail(
    pipeline_id: str,
    pipeline_repo=Depends(get_pipeline_repo),
    credential_repo=Depends(get_credential_repo),
    prompt_repo=Depends(get_prompt_repo),
    content_schema_repo=Depends(get_content_schema_repo),
):
    try:
        await _ensure_system_defaults(
            pipeline_repo=pipeline_repo,
            credential_repo=credential_repo,
            content_schema_repo=content_schema_repo,
        )
        pipeline_doc = await _ensure_pipeline_by_id(pipeline_repo, pipeline_id)
        if not pipeline_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
        return await _build_pipeline_detail_response(
            pipeline_doc=pipeline_doc,
            credential_repo=credential_repo,
            prompt_repo=prompt_repo,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error loading pipeline detail: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load pipeline detail")


@router.patch("/pipelines/{pipeline_id}/steps/{step_id}", response_model=dict)
async def update_pipeline_step_ai(
    pipeline_id: str,
    step_id: str,
    payload: Dict[str, Any] = Body(...),
    pipeline_repo=Depends(get_pipeline_repo),
    credential_repo=Depends(get_credential_repo),
    prompt_repo=Depends(get_prompt_repo),
    content_schema_repo=Depends(get_content_schema_repo),
):
    update_credential = "credential_id" in payload
    update_prompt = "prompt_id" in payload
    update_delay = "delay_seconds" in payload
    if not update_credential and not update_prompt and not update_delay:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="credential_id, prompt_id or delay_seconds is required",
        )

    await _ensure_system_defaults(
        pipeline_repo=pipeline_repo,
        credential_repo=credential_repo,
        content_schema_repo=content_schema_repo,
    )
    pipeline_doc = await _ensure_pipeline_by_id(pipeline_repo, pipeline_id)
    if not pipeline_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    steps = pipeline_doc.get("steps", []) if isinstance(pipeline_doc.get("steps"), list) else []
    step = next((item for item in steps if item.get("id") == step_id), None)
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline step not found")

    uses_ai = bool(step.get("uses_ai"))
    if (update_credential or update_prompt) and not uses_ai:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="This step does not use AI settings")

    ai = step.get("ai", {}) if isinstance(step.get("ai"), dict) else {}

    if update_credential:
        credential_id = payload.get("credential_id")
        if credential_id in ("", None):
            ai["credential_id"] = None
        else:
            credential = await credential_repo.get_by_id(str(credential_id))
            if not credential:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
            ai["credential_id"] = str(credential.get("_id"))

    if update_prompt:
        prompt_id = payload.get("prompt_id")
        if prompt_id in ("", None):
            ai["prompt_id"] = None
        else:
            prompt = await prompt_repo.get_by_id(str(prompt_id))
            if not prompt:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")
            ai["prompt_id"] = str(prompt.get("_id"))

    if uses_ai:
        step["ai"] = ai

    if update_delay:
        raw_delay = payload.get("delay_seconds")
        if raw_delay in (None, ""):
            delay_seconds = 0
        else:
            try:
                delay_seconds = int(raw_delay)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="delay_seconds must be an integer >= 0",
                )
            if delay_seconds < 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="delay_seconds must be >= 0",
                )
            if delay_seconds > 86400:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="delay_seconds must be <= 86400",
                )

        step["delay_seconds"] = delay_seconds

    pipeline_doc["steps"] = steps

    save_payload = {
        "name": pipeline_doc.get("name"),
        "slug": pipeline_doc.get("slug"),
        "description": pipeline_doc.get("description"),
        "usage_type": pipeline_doc.get("usage_type"),
        "version": pipeline_doc.get("version"),
        "steps": steps,
    }
    await pipeline_repo.create_or_update(pipeline_id, save_payload)
    updated_doc = await pipeline_repo.get_by_pipeline_id(pipeline_id)
    if not updated_doc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update pipeline step")

    details = await _build_pipeline_detail_response(
        pipeline_doc=updated_doc,
        credential_repo=credential_repo,
        prompt_repo=prompt_repo,
    )
    updated_step = next((item for item in details.get("steps", []) if item.get("id") == step_id), None)
    return {
        "status": "ok",
        "pipeline_id": pipeline_id,
        "step": updated_step,
    }


@router.get("/prompts", response_model=List[PromptResponse])
async def list_prompts(
    active: Optional[bool] = Query(None),
    purpose: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    repo=Depends(get_prompt_repo),
):
    try:
        normalized_provider = str(provider or "").strip().lower() or None
        items = await repo.list_all(
            active=active,
            purpose=purpose,
            category=category,
            provider=normalized_provider,
            name=name,
            search=search,
        )
        return [_prompt_response(d) for d in items]
    except Exception as e:
        logger.error("Error listing prompts: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/prompt-categories", response_model=List[str])
async def list_prompt_categories(
    content_schema_repo=Depends(get_content_schema_repo),
    prompt_repo=Depends(get_prompt_repo),
):
    try:
        categories = {"Book Review"}
        schemas = await content_schema_repo.list_all()
        for item in schemas:
            name = str(item.get("name") or "").strip()
            if name:
                categories.add(name)

        prompts = await prompt_repo.list_all(limit=500)
        for item in prompts:
            category = str(item.get("category") or "").strip()
            if category:
                categories.add(category)

        return sorted(categories, key=str.casefold)
    except Exception as e:
        logger.error("Error listing prompt categories: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/prompts/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str, repo=Depends(get_prompt_repo)):
    try:
        doc = await repo.get_by_id(prompt_id)
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return _prompt_response(doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching prompt: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.post("/prompts", status_code=status.HTTP_201_CREATED, response_model=PromptResponse)
async def create_prompt(payload: PromptCreate, repo=Depends(get_prompt_repo)):
    try:
        data = payload.model_dump()
        data["provider"] = str(data.get("provider") or DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
        data["category"] = str(data.get("category") or "Book Review").strip() or "Book Review"
        pid = await repo.create(data)
        doc = await repo.get_by_id(pid)
        return _prompt_response(doc)
    except Exception as e:
        logger.error("Error creating prompt: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/prompts/{prompt_id}", response_model=PromptResponse)
async def update_prompt(prompt_id: str, payload: PromptUpdate, repo=Depends(get_prompt_repo)):
    existing = await repo.get_by_id(prompt_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found")

    update_data = payload.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update")

    if "provider" in update_data:
        update_data["provider"] = str(update_data.get("provider") or DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
    if "category" in update_data:
        update_data["category"] = str(update_data.get("category") or "Book Review").strip() or "Book Review"

    ok = await repo.update(prompt_id, update_data)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update prompt")

    doc = await repo.get_by_id(prompt_id)
    return _prompt_response(doc)


@router.delete("/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt(prompt_id: str, repo=Depends(get_prompt_repo)):
    try:
        ok = await repo.delete(prompt_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        return {}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting prompt: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
