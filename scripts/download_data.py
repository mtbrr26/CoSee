"""Download and cache market data as local Parquet files.

Fetches daily OHLCV data for all assets defined in ``config/assets.yaml``
via the Yahoo Finance connector and stores each asset as a separate Parquet
file under ``data/raw/``.

Re-running is incremental: if a Parquet file already exists for an asset,
only the missing dates (from the last stored date to today) are fetched and
appended. Use ``--full`` to force a complete re-download.

Usage (from the project root)::

    python scripts/download_data.py
    python scripts/download_data.py --start 2015-01-01
    python scripts/download_data.py --assets config/assets.yaml
    python scripts/download_data.py --full          # re-download everything
    python scripts/download_data.py --log-level DEBUG
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yaml

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from cosee.ingestion.base import ConnectorError
from cosee.ingestion.yahoo_finance import YahooFinanceConnector
from cosee.logging_config import configure_logging
from cosee.models.asset import Asset, AssetType

logger = logging.getLogger(__name__)

_DATA_DIR = _PROJECT_ROOT / "data" / "raw"
_DEFAULT_START = date(2015, 1, 1)
_RATE_LIMIT_SLEEP = 1.5  # seconds between requests to avoid rate limiting
_INCREMENTAL_GRACE_DAYS = 4  # treat empty result as up-to-date if gap is ≤ this many days


# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------

def _load_assets(config_path: Path) -> List[Asset]:
    """Load assets from YAML config."""
    if not config_path.exists():
        logger.error("Asset config not found: %s", config_path)
        return []
    with config_path.open() as fh:
        data = yaml.safe_load(fh) or {}
    assets = []
    for entry in data.get("assets", []):
        try:
            assets.append(Asset(
                ticker=entry["ticker"],
                name=entry.get("name", ""),
                asset_type=AssetType(entry.get("asset_type", "unknown")),
                exchange=entry.get("exchange", ""),
                currency=entry.get("currency", "USD"),
            ))
        except Exception as exc:
            logger.warning("Skipping invalid asset entry %s: %s", entry, exc)
    return assets


# ---------------------------------------------------------------------------
# Parquet helpers
# ---------------------------------------------------------------------------

def _parquet_path(ticker: str) -> Path:
    """Return the Parquet file path for *ticker*."""
    safe = ticker.replace("/", "_").replace("=", "_").replace("^", "_").replace("-", "_")
    return _DATA_DIR / f"{safe}.parquet"


def _read_existing(ticker: str) -> Optional[pd.DataFrame]:
    """Return the stored DataFrame for *ticker*, or None if absent."""
    path = _parquet_path(ticker)
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _write(ticker: str, df: pd.DataFrame) -> None:
    """Write *df* to the Parquet cache for *ticker*."""
    path = _parquet_path(ticker)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, engine="pyarrow", compression="snappy")


def _last_stored_date(df: pd.DataFrame) -> date:
    """Return the most recent date in a stored DataFrame."""
    return pd.to_datetime(df.index).max().date()


# ---------------------------------------------------------------------------
# Download logic
# ---------------------------------------------------------------------------

def _download_asset(
    connector: YahooFinanceConnector,
    asset: Asset,
    start: date,
    full: bool,
) -> bool:
    """Fetch data for *asset* and update the local cache.

    Returns True on success, False on failure.
    """
    existing = None if full else _read_existing(asset.ticker)

    if existing is not None:
        last = _last_stored_date(existing)
        fetch_start = last + timedelta(days=1)
        if fetch_start >= date.today():
            logger.info("%-15s already up to date (last: %s)", asset.ticker, last)
            return True
        logger.info("%-15s updating %s → today", asset.ticker, fetch_start)
    else:
        fetch_start = start
        logger.info("%-15s full download from %s", asset.ticker, fetch_start)

    try:
        new_df = connector.fetch(asset, start=fetch_start)
    except ConnectorError as exc:
        # Incremental fetch over a weekend/holiday window will legitimately
        # return no data — treat it as up-to-date rather than a failure.
        gap_days = (date.today() - fetch_start).days
        if existing is not None and gap_days <= _INCREMENTAL_GRACE_DAYS:
            logger.info("%-15s up to date (no trading days in gap)", asset.ticker)
            return True
        logger.warning("%-15s FAILED: %s", asset.ticker, exc)
        return False

    if existing is not None and not full:
        combined = pd.concat([existing, new_df])
        combined = combined[~combined.index.duplicated(keep="last")]
        combined.sort_index(inplace=True)
    else:
        combined = new_df

    _write(asset.ticker, combined)
    logger.info(
        "%-15s saved %d rows → %s",
        asset.ticker,
        len(combined),
        _parquet_path(asset.ticker).name,
    )
    return True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and cache daily OHLCV data for the CoSee asset universe.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=_PROJECT_ROOT / "config" / "assets.yaml",
        help="Path to asset config YAML (default: config/assets.yaml).",
    )
    parser.add_argument(
        "--start",
        type=date.fromisoformat,
        default=_DEFAULT_START,
        help=f"Start date for full downloads (default: {_DEFAULT_START}).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Force complete re-download, ignoring existing cache.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log verbosity (default: INFO).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    configure_logging(args.log_level)

    assets = _load_assets(args.assets)
    if not assets:
        logger.error("No assets loaded — aborting.")
        sys.exit(1)

    logger.info("Loaded %d assets from %s", len(assets), args.assets)
    logger.info("Cache directory: %s", _DATA_DIR)
    if args.full:
        logger.info("--full flag set: ignoring existing cache")

    connector = YahooFinanceConnector()
    success, failed = 0, 0

    for i, asset in enumerate(assets, start=1):
        logger.debug("[%d/%d] %s", i, len(assets), asset.ticker)
        ok = _download_asset(connector, asset, start=args.start, full=args.full)
        if ok:
            success += 1
        else:
            failed += 1
        # Polite rate limiting
        if i < len(assets):
            time.sleep(_RATE_LIMIT_SLEEP)

    logger.info(
        "Done. %d succeeded, %d failed. Cache: %s",
        success,
        failed,
        _DATA_DIR,
    )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
