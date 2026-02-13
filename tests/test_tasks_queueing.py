"""
Regression tests for task queue dispatch from API endpoints.

These tests ensure API routes always enqueue using the project Celery app
instead of relying on thread-local shared-task proxy resolution.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.db.connection import get_database
from src.db.repositories import ArticleRepository, BookRepository


class DummyAsyncResult:
    def __init__(self, task_id: str):
        self.id = task_id


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _future_iso() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()


def _create_submission(client: TestClient, suffix: str, user_approval_required: bool = False) -> str:
    payload = {
        "title": f"Queueing Test {suffix}",
        "author_name": "Queue Tester",
        "amazon_url": f"https://www.amazon.com/queueing-test-{suffix}/",
        "run_immediately": False,
        "schedule_execution": _future_iso(),
        "user_approval_required": user_approval_required,
    }
    response = client.post("/submit", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def _seed_book_and_article(submission_id: str) -> str:
    db = await get_database()
    book_repo = BookRepository(db)
    article_repo = ArticleRepository(db)

    book_id = await book_repo.create_or_update(
        submission_id=submission_id,
        extracted={"title": "Queueing Test", "authors": ["Queue Tester"]},
    )
    article_id = await article_repo.create(
        book_id=book_id,
        submission_id=submission_id,
        title="Queueing Test Article",
        content="# Queueing Test\n\nConteudo inicial",
        word_count=4,
        status="draft",
    )
    return article_id


def test_generate_context_enqueue_uses_project_celery_app(monkeypatch, client: TestClient):
    submission_id = _create_submission(client, "context")

    captured = {}

    def fake_send_task(task_name: str, kwargs=None, **_):
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs or {}
        return DummyAsyncResult("ctx-task-id")

    monkeypatch.setattr("src.api.tasks.celery_app.send_task", fake_send_task)

    response = client.post(f"/tasks/{submission_id}/generate_context")
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert body["task"] == "generate_context"
    assert captured["task_name"] == "src.workers.scraper_tasks.generate_context_task"
    assert captured["kwargs"] == {"submission_id": submission_id}


def test_generate_article_enqueue_uses_project_celery_app(monkeypatch, client: TestClient):
    submission_id = _create_submission(client, "article")

    captured = {}

    def fake_send_task(task_name: str, kwargs=None, **_):
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs or {}
        return DummyAsyncResult("article-task-id")

    monkeypatch.setattr("src.api.tasks.celery_app.send_task", fake_send_task)

    response = client.post(f"/tasks/{submission_id}/generate_article")
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert body["task"] == "generate_article"
    assert captured["task_name"] == "src.workers.article_tasks.generate_article_task"
    assert captured["kwargs"] == {"submission_id": submission_id}


def test_retry_step_enqueue_uses_explicit_task_name(monkeypatch, client: TestClient):
    submission_id = _create_submission(client, "retry-step")

    captured = {}

    def fake_send_task(task_name: str, kwargs=None, **_):
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs or {}
        return DummyAsyncResult("retry-step-task-id")

    monkeypatch.setattr("src.api.tasks.celery_app.send_task", fake_send_task)

    response = client.post(f"/tasks/{submission_id}/retry_step", json={"stage": "amazon_scrape"})
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["stage"] == "amazon_scrape"
    assert captured["task_name"] == "src.workers.scraper_tasks.scrape_amazon_task"
    assert captured["kwargs"] == {
        "submission_id": submission_id,
        "amazon_url": "https://www.amazon.com/queueing-test-retry-step/",
    }


def test_publish_article_enqueue_uses_project_celery_app(monkeypatch, client: TestClient):
    submission_id = _create_submission(client, "publish")
    article_id = pytest.run(async_fn=_seed_book_and_article, submission_id=submission_id)

    captured = {}

    def fake_send_task(task_name: str, kwargs=None, **_):
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs or {}
        return DummyAsyncResult("publish-task-id")

    monkeypatch.setattr("src.api.tasks.celery_app.send_task", fake_send_task)

    response = client.post(f"/tasks/{submission_id}/publish_article")
    assert response.status_code == 202, response.text
    body = response.json()
    assert body["status"] == "queued"
    assert body["celery_task_id"] == "publish-task-id"
    assert captured["task_name"] == "src.workers.publishing_tasks.publish_article_task"
    assert captured["kwargs"] == {"article_id": article_id, "submission_id": submission_id}

