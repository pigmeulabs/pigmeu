from celery import Celery

from src.config import settings

# Initialize Celery app
app = Celery(
    "pigmeu",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_ignore_result=True,
)

# Ensure shared tasks are imported and registered at worker startup.
import src.workers.scraper_tasks  # noqa: E402,F401
import src.workers.article_tasks  # noqa: E402,F401
import src.workers.publishing_tasks  # noqa: E402,F401
import src.workers.link_tasks  # noqa: E402,F401


@app.task(name="ping")
def ping():
    """Simple ping task for testing."""
    return "pong"


@app.task(name="start_pipeline")
def start_pipeline(submission_id: str, amazon_url: str, pipeline_id: str = "book_review_v2"):
    """Entry task to start scraping pipeline from web requests."""
    try:
        from src.workers.scraper_tasks import start_scraping_pipeline

        start_scraping_pipeline(
            submission_id=submission_id,
            amazon_url=amazon_url,
            pipeline_id=pipeline_id,
        )
        return {"status": "started", "submission_id": submission_id, "pipeline_id": pipeline_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}
