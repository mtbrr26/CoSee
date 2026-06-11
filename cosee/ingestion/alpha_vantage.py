"""Alpha Vantage connector (placeholder implementation).

This connector demonstrates how to integrate a paid/key-based API.  The
actual HTTP calls are stubbed out so the project runs without a live key;
replace ``_fetch_raw`` with real requests when a key is available.

Set the API key via the environment variable ``ALPHA_VANTAGE_API_KEY`` or in
the ``.env`` file.

Example::

    from cosee.ingestion.alpha_vantage import AlphaVantageConnector
    from cosee.models.asset import Asset
    from datetime import date

    conn = AlphaVantageConnector(api_key="YOUR_KEY")
    df = conn.fetch(Asset("MSFT"), start=date(2023, 1, 1))
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import pandas as pd

from cosee.ingestion.base import BaseConnector, ConnectorError
from cosee.models.asset import Asset

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.alphavantage.co/query"
_FUNCTION_MAP = {
    "1d": "TIME_SERIES_DAILY_ADJUSTED",
    "1wk": "TIME_SERIES_WEEKLY_ADJUSTED",
    "1mo": "TIME_SERIES_MONTHLY_ADJUSTED",
}


class AlphaVantageConnector(BaseConnector):
    """Fetches market data from the Alpha Vantage REST API.

    Args:
        api_key: Alpha Vantage API key.  If omitted, falls back to the
                 ``ALPHA_VANTAGE_API_KEY`` environment variable.
        timeout: HTTP timeout in seconds.
        retries: Number of retry attempts on transient HTTP failures.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        retries: int = 3,
    ) -> None:
        super().__init__(timeout=timeout, retries=retries)
        from cosee.config import settings  # avoid circular import at top level

        self._api_key: Optional[str] = api_key or settings.alpha_vantage_api_key

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        asset: Asset,
        start: date,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch OHLCV data from Alpha Vantage.

        Args:
            asset: Asset to fetch.
            start: Inclusive start date.
            end: Inclusive end date (defaults to today).
            interval: Data frequency (``"1d"``, ``"1wk"``, ``"1mo"``).

        Returns:
            Normalised OHLCV DataFrame.

        Raises:
            ConnectorError: On missing API key or failed requests.
        """
        if not self._api_key:
            raise ConnectorError(
                "Alpha Vantage API key is required. "
                "Set ALPHA_VANTAGE_API_KEY in your environment or .env file."
            )

        function = _FUNCTION_MAP.get(interval)
        if not function:
            raise ConnectorError(
                f"Unsupported interval '{interval}' for Alpha Vantage. "
                f"Supported: {list(_FUNCTION_MAP)}"
            )

        end_date = end or date.today()
        logger.debug(
            "Fetching %s from Alpha Vantage (%s to %s, interval=%s)",
            asset.ticker,
            start,
            end_date,
            interval,
        )

        raw = self._fetch_raw(asset.ticker, function)
        df = self._parse_response(raw, start, end_date)
        return self._validate_dataframe(df, asset.ticker)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_raw(self, ticker: str, function: str) -> dict:
        """Execute the HTTP request against the Alpha Vantage API.

        **Placeholder**: returns an empty dict.  Replace with a real
        ``requests.get`` call when you have a live API key.
        """
        logger.warning(
            "_fetch_raw is a placeholder. No HTTP request was made for %s.",
            ticker,
        )
        # TODO: Replace with real implementation, e.g.:
        # import requests
        # params = {
        #     "function": function,
        #     "symbol": ticker,
        #     "outputsize": "full",
        #     "apikey": self._api_key,
        # }
        # resp = requests.get(_BASE_URL, params=params, timeout=self.timeout)
        # resp.raise_for_status()
        # return resp.json()
        return {}

    @staticmethod
    def _parse_response(
        raw: dict, start: date, end: date
    ) -> pd.DataFrame:
        """Convert an Alpha Vantage JSON response into a normalised DataFrame.

        Expected keys (daily adjusted example):
            ``"Time Series (Daily)"`` → ``{date_str: {ohlcv fields}}``
        """
        # Locate the time-series key (varies by function).
        ts_key = next(
            (k for k in raw if k.startswith("Time Series")), None
        )
        if ts_key is None:
            return pd.DataFrame()

        records = raw[ts_key]
        rows = []
        for date_str, fields in records.items():
            dt = pd.to_datetime(date_str)
            if not (start <= dt.date() <= end):
                continue
            rows.append(
                {
                    "date": dt,
                    "open": float(fields.get("1. open", float("nan"))),
                    "high": float(fields.get("2. high", float("nan"))),
                    "low": float(fields.get("3. low", float("nan"))),
                    "close": float(
                        fields.get("5. adjusted close", fields.get("4. close", float("nan")))
                    ),
                    "volume": float(fields.get("6. volume", float("nan"))),
                    "adj_close": float(
                        fields.get("5. adjusted close", float("nan"))
                    ),
                }
            )

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).set_index("date").sort_index()
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        return df
