"""CoSee pipeline runner script.

Loads assets from config/assets.yaml, fetches market data, runs the
processing pipeline, computes pairwise correlations, and prints the top
correlated pairs.

Usage (from the project root)::

    python scripts/run_pipeline.py [OPTIONS]

Options::

    --start     Start date (YYYY-MM-DD). Default: 1 year ago.
    --end       End date   (YYYY-MM-DD). Default: today.
    --window    Rolling window in trading days. Default: from settings.
    --top-n     Number of top pairs to display. Default: from settings.
    --source    Data source: yahoo_finance | alpha_vantage.
    --assets    Path to asset config YAML. Default: config/assets.yaml.
    --output    Output format: table | csv | json. Default: table.
    --log-level Log level: DEBUG | INFO | WARNING. Default: INFO.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yaml

# Ensure the project root is on the path when run directly.
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from cosee.config import settings
from cosee.correlation.engine import CorrelationEngine
from cosee.ingestion.factory import get_connector
from cosee.logging_config import configure_logging
from cosee.models.asset import Asset, AssetType
from cosee.models.correlation_result import CorrelationResult
from cosee.processing.pipeline import ProcessingPipeline

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Asset loading
# ---------------------------------------------------------------------------

def load_assets(config_path: Path) -> List[Asset]:
    """Load assets from *config_path* YAML file."""
    if not config_path.exists():
        logger.error("Asset config not found: %s", config_path)
        return []
    with config_path.open() as fh:
        data = yaml.safe_load(fh) or {}
    assets = []
    for entry in data.get("assets", []):
        try:
            assets.append(
                Asset(
                    ticker=entry["ticker"],
                    name=entry.get("name", ""),
                    asset_type=AssetType(entry.get("asset_type", "unknown")),
                    exchange=entry.get("exchange", ""),
                    currency=entry.get("currency", "USD"),
                )
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipping invalid asset entry %s: %s", entry, exc)
    logger.info("Loaded %d assets from %s.", len(assets), config_path)
    return assets


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def _print_table(results: List[CorrelationResult], top_n: int) -> None:
    header = f"{'Rank':<5} {'Pair':<20} {'Correlation':>12} {'Window':>8} {'P-Value':>10}"
    print("\n" + "=" * len(header))
    print(" TOP CORRELATED ASSET PAIRS")
    print("=" * len(header))
    print(header)
    print("-" * len(header))
    for rank, r in enumerate(results[:top_n], start=1):
        pval_str = f"{r.p_value:.4f}" if r.p_value is not None else "N/A"
        win_str = str(r.window) if r.window is not None else "full"
        print(
            f"{rank:<5} {r.pair_key:<20} {r.correlation:>12.6f} "
            f"{win_str:>8} {pval_str:>10}"
        )
    print("=" * len(header) + "\n")


def _print_csv(results: List[CorrelationResult]) -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(["rank", "pair", "correlation", "window", "p_value"])
    for rank, r in enumerate(results, start=1):
        writer.writerow(
            [rank, r.pair_key, r.correlation, r.window, r.p_value]
        )


def _print_json(results: List[CorrelationResult]) -> None:
    records = [
        {
            "rank": rank,
            "pair": r.pair_key,
            "asset_a": r.asset_a.ticker,
            "asset_b": r.asset_b.ticker,
            "correlation": r.correlation,
            "window": r.window,
            "p_value": r.p_value,
        }
        for rank, r in enumerate(results, start=1)
    ]
    print(json.dumps(records, indent=2))


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run_pipeline",
        description="CoSee – Correlated Asset Pair Identification Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--start",
        type=str,
        default=None,
        help="Start date YYYY-MM-DD (default: 1 year ago)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=None,
        help="End date YYYY-MM-DD (default: today)",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=None,
        help="Rolling window in trading days (0 = full-period static)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Number of top pairs to display",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Data source: yahoo_finance | alpha_vantage",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=None,
        help="Path to assets YAML config",
    )
    parser.add_argument(
        "--output",
        choices=["table", "csv", "json"],
        default="table",
        help="Output format",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Logging level: DEBUG | INFO | WARNING | ERROR",
    )
    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(level=args.log_level)

    # --- Resolve parameters (CLI > settings > defaults) ---
    start_str = args.start or settings.get("start_date") or ""
    end_str = args.end or settings.get("end_date") or ""

    start_date: date = (
        date.fromisoformat(start_str) if start_str else date.today() - timedelta(days=365)
    )
    end_date: date = date.fromisoformat(end_str) if end_str else date.today()

    window: Optional[int] = args.window if args.window is not None else settings.default_window
    if window == 0:
        window = None  # full-period static correlation

    top_n: int = args.top_n if args.top_n is not None else settings.top_n_pairs
    source: str = args.source or settings.data_source
    assets_path: Path = args.assets or settings.assets_config_path

    logger.info(
        "Pipeline: %s → %s | window=%s | top_n=%d | source=%s",
        start_date,
        end_date,
        window,
        top_n,
        source,
    )

    # --- Load assets ---
    assets = load_assets(assets_path)
    if not assets:
        logger.error("No assets to process. Exiting.")
        return 1

    # --- Fetch data ---
    connector = get_connector(source)
    logger.info("Fetching data for %d assets…", len(assets))
    raw_data = connector.fetch_many(assets, start=start_date, end=end_date)

    if not raw_data:
        logger.error("No market data retrieved. Exiting.")
        return 1

    logger.info("Retrieved data for %d / %d assets.", len(raw_data), len(assets))

    # --- Process ---
    pipeline = ProcessingPipeline()
    aligned = pipeline.run(raw_data)

    if aligned.empty:
        logger.error("Processing produced an empty matrix. Exiting.")
        return 1

    # --- Correlate ---
    engine = CorrelationEngine(window=window, top_n=top_n, compute_pvalue=True)
    results = engine.run(aligned)

    if not results:
        logger.warning("No correlation results found.")
        return 0

    # --- Output ---
    if args.output == "table":
        _print_table(results, top_n)
    elif args.output == "csv":
        _print_csv(results)
    elif args.output == "json":
        _print_json(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
