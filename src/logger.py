import logging
import sys
import os
from src.config import settings


def setup_logger():
    """Configure logging for the application."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # ensure logs directory exists so FileHandler won't fail during tests
    os.makedirs("logs", exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log"),
        ],
    )
    
    # Suppress verbose logs from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


logger = logging.getLogger(__name__)
