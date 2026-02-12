"""Minimal WordPress REST API client."""

from __future__ import annotations

import base64
from typing import Dict, Any, Optional, List, Tuple

import httpx


class WordPressClient:
    """Client for WordPress post publication via REST API."""

    def __init__(self, wordpress_url: str, username: str, password: str):
        self.base_url = wordpress_url.rstrip("/")
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
        self.headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

    async def _find_or_create_term(self, taxonomy: str, name: str) -> Optional[int]:
        """Find taxonomy term by name, creating it if missing."""
        clean_name = (name or "").strip()
        if not clean_name:
            return None

        endpoint = f"{self.base_url}/wp-json/wp/v2/{taxonomy}"

        async with httpx.AsyncClient(timeout=20) as client:
            search_resp = await client.get(
                endpoint,
                params={"search": clean_name, "per_page": 50},
                headers=self.headers,
            )
            search_resp.raise_for_status()
            items = search_resp.json()

            for item in items:
                if str(item.get("name", "")).strip().lower() == clean_name.lower():
                    return int(item.get("id"))

            create_resp = await client.post(
                endpoint,
                json={"name": clean_name},
                headers=self.headers,
            )
            if create_resp.status_code in (400, 409):
                # Term may have been created concurrently; retry search.
                retry_resp = await client.get(
                    endpoint,
                    params={"search": clean_name, "per_page": 50},
                    headers=self.headers,
                )
                retry_resp.raise_for_status()
                retry_items = retry_resp.json()
                for item in retry_items:
                    if str(item.get("name", "")).strip().lower() == clean_name.lower():
                        return int(item.get("id"))
                return None

            create_resp.raise_for_status()
            created = create_resp.json()
            return int(created.get("id")) if created.get("id") is not None else None

    async def resolve_categories_and_tags(
        self,
        categories: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Tuple[List[int], List[int]]:
        """Resolve category and tag names into WordPress taxonomy IDs."""
        category_ids: List[int] = []
        tag_ids: List[int] = []

        for name in categories or []:
            term_id = await self._find_or_create_term("categories", name)
            if term_id:
                category_ids.append(term_id)

        for name in tags or []:
            term_id = await self._find_or_create_term("tags", name)
            if term_id:
                tag_ids.append(term_id)

        return category_ids, tag_ids

    async def create_post(
        self,
        title: str,
        content_html: str,
        excerpt: Optional[str] = None,
        categories: Optional[list[int]] = None,
        tags: Optional[list[int]] = None,
        status: str = "publish",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "title": title,
            "content": content_html,
            "status": status,
        }

        if excerpt:
            payload["excerpt"] = excerpt
        if categories:
            payload["categories"] = categories
        if tags:
            payload["tags"] = tags
        if meta:
            payload["meta"] = meta

        endpoint = f"{self.base_url}/wp-json/wp/v2/posts"
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
