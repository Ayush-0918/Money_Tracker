"""
app/utils/logging_config.py
─────────────────────────────────────────────────────────────────────────────
Structured logging configuration for the Money Tracker backend.

Sets up a consistent log format with timestamps, level, module name, and
message. In production environments JSON logging could replace this, but
plain-text is easier to read during development and on Supabase/Railway logs.

Usage:
    from app.utils.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Transaction saved", extra={"transaction_id": str(txn.id)})
"""

import logging
import sys


def configure_logging() -> None:
    """
    Configure the root logger for the application.

    Called once at application startup (inside main.py lifespan).
    Sets log level based on ENVIRONMENT setting:
      - development → DEBUG (verbose, shows all internal details)
      - production  → INFO  (avoids leaking sensitive debug data)

    NOTE: settings is imported here (not at module level) so that test
    collection works without a .env file present.
    """
    from app.config import settings  # lazy import — avoids Settings() at import time

    log_level = logging.DEBUG if settings.ENVIRONMENT == "development" else logging.INFO

    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Suppress noisy third-party loggers in production
    if settings.ENVIRONMENT == "production":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        "Logging configured | environment=%s | level=%s",
        settings.ENVIRONMENT,
        logging.getLevelName(log_level),
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger instance.

    Args:
        name: Typically __name__ of the calling module.

    Returns:
        A Logger instance scoped to the given module name.
    """
    return logging.getLogger(name)
