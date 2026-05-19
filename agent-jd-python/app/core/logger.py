import sys

from loguru import logger

from app.core.settings import settings


def setup_logging() -> None:
    logger.remove()
    logger.add(
        sys.stdout,
        level="DEBUG" if settings.app_env == "dev" else "INFO",
        serialize=settings.app_env != "dev",
        enqueue=True,
        backtrace=False,
        diagnose=False,
    )
