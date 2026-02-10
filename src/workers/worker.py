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
    task_time_limit=30 * 60,  # 30 minutes hard limit
)


@app.task(name="ping")
def ping():
    """Simple ping task for testing."""
    return "pong"
