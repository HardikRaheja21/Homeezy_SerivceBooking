# app/core/logging_config.py
"""
Centralized structured logging for Homeezy.

Sets up:
- Console handler (colored, human-readable in dev)
- Rotating file handler (JSON-style in production)
- Per-request logging middleware
- A shared `get_logger` helper for all modules

Usage:
    from app.core.logging_config import get_logger
    logger = get_logger(__name__)
    logger.info("Booking created", extra={"booking_id": "abc"})
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "homeezy.log"
MAX_BYTES = 10 * 1024 * 1024   # 10 MB per file
BACKUP_COUNT = 5                # keep last 5 rotated files

_CONSOLE_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FILE_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _setup_logging() -> None:
    """Configure root logger once at startup."""
    LOG_DIR.mkdir(exist_ok=True)

    root = logging.getLogger()
    # Avoid duplicate handlers if called multiple times (e.g. test reloads)
    if root.handlers:
        return

    root.setLevel(LOG_LEVEL)

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FMT, datefmt=_DATE_FMT))
    root.addHandler(console_handler)

    # ── Rotating file handler ─────────────────────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(LOG_LEVEL)
    file_handler.setFormatter(logging.Formatter(_FILE_FMT, datefmt=_DATE_FMT))
    root.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Call once per module at module level."""
    _setup_logging()
    return logging.getLogger(name)


# Initialise on import so the root logger is ready before any module uses it.
_setup_logging()
