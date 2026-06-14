"""Tests for scripts/download_data.py."""

import sys
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

# Ensure project root is importable when running directly.
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.download_data import (
    _last_stored_date,
    _load_assets,
    _parquet_path,
    _download_asset,
)
from cosee.models.asset import Asset, AssetType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 5, start: str = "2023-01-01") -> pd.DataFrame:
    idx = pd.date_range(start, periods=n, freq="B")
    df = pd.DataFrame(
        {
            "open": range(100, 100 + n),
            "high": range(101, 101 + n),
            "low": range(99, 99 + n),
            "close": range(100, 100 + n),
            "volume": [1_000_000] * n,
        },
        index=idx,
    )
    df.index.name = "date"
    return df


_SAMPLE_ASSET = Asset(ticker="AAPL", name="Apple Inc.", asset_type=AssetType.STOCK)


# ---------------------------------------------------------------------------
# _load_assets
# ---------------------------------------------------------------------------

class TestLoadAssets:
    def test_returns_empty_for_missing_file(self, tmp_path):
        result = _load_assets(tmp_path / "nonexistent.yaml")
        assert result == []

    def test_loads_valid_yaml(self, tmp_path):
        yaml_content = """
assets:
  - ticker: AAPL
    name: Apple Inc.
    asset_type: stock
    exchange: NASDAQ
    currency: USD
  - ticker: GC=F
    name: Gold Futures
    asset_type: commodity
"""
        config = tmp_path / "assets.yaml"
        config.write_text(yaml_content)
        assets = _load_assets(config)
        assert len(assets) == 2
        assert assets[0].ticker == "AAPL"
        assert assets[1].ticker == "GC=F"

    def test_skips_invalid_entries(self, tmp_path):
        yaml_content = """
assets:
  - ticker: AAPL
    asset_type: stock
  - ticker: ""
    asset_type: stock
"""
        config = tmp_path / "assets.yaml"
        config.write_text(yaml_content)
        assets = _load_assets(config)
        # Empty ticker raises ValueError in Asset.__post_init__, should be skipped
        assert len(assets) == 1
        assert assets[0].ticker == "AAPL"


# ---------------------------------------------------------------------------
# _parquet_path
# ---------------------------------------------------------------------------

class TestParquetPath:
    def test_safe_filename_for_normal_ticker(self):
        path = _parquet_path("AAPL")
        assert path.name == "AAPL.parquet"

    def test_safe_filename_for_futures_ticker(self):
        path = _parquet_path("GC=F")
        assert "=" not in path.name
        assert path.suffix == ".parquet"

    def test_safe_filename_for_index_ticker(self):
        path = _parquet_path("^GSPC")
        assert "^" not in path.name

    def test_safe_filename_for_fx_ticker(self):
        path = _parquet_path("BTC-USD")
        assert "-" not in path.name


# ---------------------------------------------------------------------------
# _last_stored_date
# ---------------------------------------------------------------------------

class TestLastStoredDate:
    def test_returns_latest_date(self):
        df = _make_ohlcv(n=5, start="2023-01-02")
        last = _last_stored_date(df)
        assert last == pd.date_range("2023-01-02", periods=5, freq="B")[-1].date()


# ---------------------------------------------------------------------------
# _download_asset
# ---------------------------------------------------------------------------

class TestDownloadAsset:
    def test_full_download_writes_parquet(self, tmp_path):
        connector = MagicMock()
        connector.fetch.return_value = _make_ohlcv()

        with patch("scripts.download_data._DATA_DIR", tmp_path):
            ok = _download_asset(connector, _SAMPLE_ASSET, start=date(2023, 1, 1), full=True)

        assert ok is True
        connector.fetch.assert_called_once()
        assert (tmp_path / "AAPL.parquet").exists()

    def test_incremental_skips_if_up_to_date(self, tmp_path):
        df = _make_ohlcv(n=3, start=str(date.today() - timedelta(days=3)))
        df.index = pd.date_range(date.today() - timedelta(days=2), periods=3, freq="B")
        df.to_parquet(tmp_path / "AAPL.parquet", engine="pyarrow")

        connector = MagicMock()

        with patch("scripts.download_data._DATA_DIR", tmp_path):
            ok = _download_asset(connector, _SAMPLE_ASSET, start=date(2023, 1, 1), full=False)

        assert ok is True
        connector.fetch.assert_not_called()

    def test_returns_false_on_connector_error_full_download(self, tmp_path):
        from cosee.ingestion.base import ConnectorError

        connector = MagicMock()
        connector.fetch.side_effect = ConnectorError("network error")

        with patch("scripts.download_data._DATA_DIR", tmp_path):
            ok = _download_asset(connector, _SAMPLE_ASSET, start=date(2023, 1, 1), full=True)

        assert ok is False

    def test_returns_true_on_weekend_gap_incremental(self, tmp_path):
        """Empty result over a weekend/holiday gap should not count as failure."""
        from cosee.ingestion.base import ConnectorError

        # Store data up to yesterday
        yesterday = date.today() - timedelta(days=1)
        df = _make_ohlcv(n=5, start=str(yesterday - timedelta(days=6)))
        df.index = pd.date_range(yesterday - timedelta(days=4), periods=5, freq="B")
        df.to_parquet(tmp_path / "AAPL.parquet", engine="pyarrow")

        connector = MagicMock()
        connector.fetch.side_effect = ConnectorError("no data")

        with patch("scripts.download_data._DATA_DIR", tmp_path):
            ok = _download_asset(connector, _SAMPLE_ASSET, start=date(2023, 1, 1), full=False)

        assert ok is True

    def test_incremental_appends_new_rows(self, tmp_path):
        old_df = _make_ohlcv(n=5, start="2023-01-02")
        old_df.to_parquet(tmp_path / "AAPL.parquet", engine="pyarrow")

        new_df = _make_ohlcv(n=3, start="2023-01-10")
        connector = MagicMock()
        connector.fetch.return_value = new_df

        with patch("scripts.download_data._DATA_DIR", tmp_path):
            ok = _download_asset(connector, _SAMPLE_ASSET, start=date(2023, 1, 1), full=False)

        assert ok is True
        result = pd.read_parquet(tmp_path / "AAPL.parquet")
        assert len(result) == 8
