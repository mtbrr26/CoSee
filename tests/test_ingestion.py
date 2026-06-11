"""Tests for the data ingestion layer."""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

import pandas as pd

from cosee.ingestion.base import BaseConnector, ConnectorError
from cosee.ingestion.factory import get_connector
from cosee.ingestion.alpha_vantage import AlphaVantageConnector
from cosee.models.asset import Asset


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ohlcv(n: int = 10) -> pd.DataFrame:
    """Create a minimal OHLCV DataFrame with a DatetimeIndex."""
    idx = pd.date_range("2023-01-01", periods=n, freq="B")
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


# ---------------------------------------------------------------------------
# BaseConnector
# ---------------------------------------------------------------------------

class ConcreteConnector(BaseConnector):
    """Minimal concrete implementation for testing the abstract base class."""

    def fetch(self, asset, start, end=None, interval="1d"):
        return _make_ohlcv()


class TestBaseConnector:
    def test_validate_dataframe_raises_on_empty(self):
        with pytest.raises(ConnectorError, match="No data"):
            BaseConnector._validate_dataframe(pd.DataFrame(), "TEST")

    def test_validate_dataframe_raises_missing_close(self):
        df = pd.DataFrame({"open": [1]}, index=pd.to_datetime(["2023-01-01"]))
        with pytest.raises(ConnectorError, match="missing required 'close'"):
            BaseConnector._validate_dataframe(df, "TEST")

    def test_validate_dataframe_raises_non_datetime_index(self):
        df = pd.DataFrame({"close": [100]}, index=[0])
        with pytest.raises(ConnectorError, match="DatetimeIndex"):
            BaseConnector._validate_dataframe(df, "TEST")

    def test_validate_valid_dataframe_passes(self):
        df = _make_ohlcv()
        result = BaseConnector._validate_dataframe(df, "TEST")
        assert not result.empty

    def test_fetch_many_skips_failures(self):
        connector = ConcreteConnector()
        assets = [Asset("AAPL"), Asset("MSFT")]
        result = connector.fetch_many(assets, start=date(2023, 1, 1))
        assert "AAPL" in result
        assert "MSFT" in result

    def test_repr(self):
        c = ConcreteConnector(timeout=60)
        assert "ConcreteConnector" in repr(c)
        assert "60" in repr(c)


# ---------------------------------------------------------------------------
# AlphaVantageConnector (placeholder)
# ---------------------------------------------------------------------------

class TestAlphaVantageConnector:
    def test_raises_without_api_key(self):
        conn = AlphaVantageConnector(api_key=None)
        # Ensure no env var leaks in
        with patch.dict("os.environ", {}, clear=True):
            conn._api_key = None
            with pytest.raises(ConnectorError, match="API key"):
                conn.fetch(Asset("MSFT"), start=date(2023, 1, 1))

    def test_raises_for_unsupported_interval(self):
        conn = AlphaVantageConnector(api_key="fake")
        with pytest.raises(ConnectorError, match="Unsupported interval"):
            conn.fetch(Asset("MSFT"), start=date(2023, 1, 1), interval="5m")

    def test_parse_response_empty_on_missing_key(self):
        df = AlphaVantageConnector._parse_response(
            {}, date(2023, 1, 1), date(2023, 12, 31)
        )
        assert df.empty

    def test_parse_response_filters_by_date(self):
        raw = {
            "Time Series (Daily)": {
                "2023-06-01": {
                    "1. open": "100",
                    "2. high": "101",
                    "3. low": "99",
                    "4. close": "100",
                    "5. adjusted close": "100",
                    "6. volume": "1000",
                },
                "2024-01-01": {
                    "1. open": "200",
                    "2. high": "201",
                    "3. low": "199",
                    "4. close": "200",
                    "5. adjusted close": "200",
                    "6. volume": "2000",
                },
            }
        }
        df = AlphaVantageConnector._parse_response(
            raw, date(2023, 1, 1), date(2023, 12, 31)
        )
        assert len(df) == 1
        assert df.iloc[0]["close"] == 100.0


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestFactory:
    def test_get_yahoo_connector(self):
        conn = get_connector("yahoo_finance")
        from cosee.ingestion.yahoo_finance import YahooFinanceConnector
        assert isinstance(conn, YahooFinanceConnector)

    def test_get_alpha_vantage_connector(self):
        conn = get_connector("alpha_vantage")
        assert isinstance(conn, AlphaVantageConnector)

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown data source"):
            get_connector("nonexistent_source")
