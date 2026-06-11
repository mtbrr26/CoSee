"""Centralised logging setup for CoSee.

Call ``configure_logging()`` once at application startup (the CLI does this
automatically).  All other modules simply call ``logging.getLogger(__name__)``.

Usage::

    from cosee.logging_config import configure_logging
    configure_logging()
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


def configure_logging(
    level: Optional[str] = None,
    fmt: Optional[str] = None,
) -> None:
    """Configure the root logger for CoSee.

    Args:
        level: Log level string (e.g. ``"DEBUG"``).  Falls back to the
               ``settings.log_level`` value if not provided.
        fmt:   Log format string.  Falls back to ``settings.log_format``.
    """
    # Import here to avoid circular imports at module load time.
    from cosee.config import settings  # noqa: PLC0415

    effective_level = (level or settings.log_level).upper()
    effective_fmt = fmt or settings.log_format

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(effective_fmt))

    root = logging.getLogger()
    root.setLevel(effective_level)
    # Avoid adding duplicate handlers when called multiple times.
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)

    # Suppress overly chatty third-party loggers.
    for noisy in ("urllib3", "requests", "yfinance", "peewee"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
