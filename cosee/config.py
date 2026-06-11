"""Configuration management for CoSee.

Reads settings from:
  1. ``config/settings.yaml``  – static defaults.
  2. Environment variables (always win over YAML).
  3. A ``.env`` file in the project root (if present).

Usage::

    from cosee.config import settings
    print(settings.log_level)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Project root is the directory that contains the ``cosee`` package.
_PROJECT_ROOT = Path(__file__).parent.parent
_SETTINGS_FILE = _PROJECT_ROOT / "config" / "settings.yaml"
_ENV_FILE = _PROJECT_ROOT / ".env"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no third-party dependency required)."""
    if not path.exists():
        return
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            os.environ.setdefault(key, value)


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open() as fh:
        data = yaml.safe_load(fh) or {}
    return data


class Settings:
    """Central configuration object.

    All values can be overridden with environment variables that follow the
    pattern ``COSEE_<UPPER_KEY>`` (e.g. ``COSEE_LOG_LEVEL=DEBUG``).
    """

    def __init__(self) -> None:
        _load_dotenv(_ENV_FILE)
        self._data: Dict[str, Any] = _load_yaml(_SETTINGS_FILE)

    def get(self, key: str, default: Any = None) -> Any:
        env_key = f"COSEE_{key.upper()}"
        env_val = os.environ.get(env_key)
        if env_val is not None:
            return env_val
        return self._data.get(key, default)

    # ------------------------------------------------------------------
    # Typed convenience properties
    # ------------------------------------------------------------------

    @property
    def log_level(self) -> str:
        return str(self.get("log_level", "INFO")).upper()

    @property
    def log_format(self) -> str:
        return str(
            self.get(
                "log_format",
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            )
        )

    @property
    def default_window(self) -> int:
        return int(self.get("default_window", 30))

    @property
    def top_n_pairs(self) -> int:
        return int(self.get("top_n_pairs", 20))

    @property
    def data_source(self) -> str:
        return str(self.get("data_source", "yahoo_finance"))

    @property
    def alpha_vantage_api_key(self) -> Optional[str]:
        val = os.environ.get("ALPHA_VANTAGE_API_KEY")
        return val if val else None

    @property
    def assets_config_path(self) -> Path:
        raw = self.get("assets_config_path", "config/assets.yaml")
        p = Path(raw)
        if not p.is_absolute():
            p = _PROJECT_ROOT / p
        return p

    def __repr__(self) -> str:
        return (
            f"Settings(log_level={self.log_level!r}, "
            f"data_source={self.data_source!r}, "
            f"default_window={self.default_window})"
        )


# Singleton – import this directly.
settings = Settings()
