"""Yahoo Finance connector (uses the ``yfinance`` library).

This connector is the default data source and requires no API key.

Example::

    from cosee.ingestion.yahoo_finance import YahooFinanceConnector
    from cosee.models.asset import Asset
    from datetime import date

    conn = YahooFinanceConnector()
    df = conn.fetch(Asset("AAPL"), start=date(2023, 1, 1))
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

import pandas as pd

from cosee.ingestion.base import BaseConnector, ConnectorError
from cosee.models.asset import Asset

logger = logging.getLogger(__name__)

_COLUMN_MAP = {
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume",
    "Adj Close": "adj_close",
}


class YahooFinanceConnector(BaseConnector):
    """Fetches OHLCV data via ``yfinance``.

    ``yfinance`` is a community-maintained library that scrapes Yahoo Finance.
    It works well for daily/weekly/monthly data and requires no API key.

    Args:
        timeout: HTTP timeout in seconds (passed to yfinance).
        retries: Not directly used by yfinance but reserved for future wrapper.
    """

    def fetch(
        self,
        asset: Asset,
        start: date,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch data for *asset* from Yahoo Finance.

        Args:
            asset: Asset to fetch.
            start: Inclusive start date.
            end: Inclusive end date (defaults to today).
            interval: yfinance interval string (``"1d"``, ``"1wk"``, etc.).

        Returns:
            Normalised OHLCV DataFrame.

        Raises:
            ConnectorError: When yfinance is unavailable or returns no data.
        """
        try:
            import yfinance as yf  # lazy import – optional dependency
        except ImportError as exc:
            raise ConnectorError(
                "yfinance is not installed. Run: pip install yfinance"
            ) from exc

        end_date = end or date.today()
        logger.debug(
            "Fetching %s from Yahoo Finance (%s to %s, interval=%s)",
            asset.ticker,
            start,
            end_date,
            interval,
        )

        try:
            raw: pd.DataFrame = yf.download(
                asset.ticker,
                start=start.isoformat(),
                end=end_date.isoformat(),
                interval=interval,
                progress=False,
                auto_adjust=False,
            )
        except Exception as exc:
            raise ConnectorError(
                f"yfinance download failed for {asset.ticker}: {exc}"
            ) from exc

        if raw.empty:
            raise ConnectorError(
                f"Yahoo Finance returned no data for {asset.ticker} "
                f"({start} – {end_date})."
            )

        # Flatten MultiIndex columns produced by yfinance >= 0.2
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        df = raw.rename(columns=_COLUMN_MAP)
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"

        return self._validate_dataframe(df, asset.ticker)
