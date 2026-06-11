"""Abstract base class for all market data connectors.

Every concrete connector must implement :meth:`fetch` which returns a
``pandas.DataFrame`` with a ``DatetimeIndex`` and at least a ``close`` column.

Columns (all optional except ``close``):
    - ``open``
    - ``high``
    - ``low``
    - ``close``   ← **required**
    - ``volume``
    - ``adj_close``
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

import pandas as pd

from cosee.models.asset import Asset

logger = logging.getLogger(__name__)


class ConnectorError(Exception):
    """Raised when a data connector encounters an unrecoverable error."""


class BaseConnector(ABC):
    """Interface that all market data source connectors must satisfy.

    Args:
        timeout: HTTP request timeout in seconds.
        retries: Number of retry attempts on transient failures.
    """

    def __init__(self, timeout: int = 30, retries: int = 3) -> None:
        self.timeout = timeout
        self.retries = retries

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch(
        self,
        asset: Asset,
        start: date,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch OHLCV data for a single asset.

        Args:
            asset: The asset to fetch data for.
            start: Inclusive start date.
            end: Inclusive end date (defaults to today).
            interval: Data frequency, e.g. ``"1d"``, ``"1wk"``, ``"1mo"``.

        Returns:
            DataFrame indexed by ``datetime`` with at least a ``close`` column.

        Raises:
            ConnectorError: On irrecoverable fetch failures.
        """

    def fetch_many(
        self,
        assets: List[Asset],
        start: date,
        end: Optional[date] = None,
        interval: str = "1d",
    ) -> dict[str, pd.DataFrame]:
        """Fetch data for multiple assets.

        Default implementation calls :meth:`fetch` sequentially.  Subclasses
        may override this with concurrent/batch requests.

        Returns:
            Mapping of ``ticker -> DataFrame``.
        """
        results: dict[str, pd.DataFrame] = {}
        for asset in assets:
            try:
                df = self.fetch(asset, start, end, interval)
                results[asset.ticker] = df
            except ConnectorError as exc:
                logger.warning("Failed to fetch %s: %s", asset.ticker, exc)
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_dataframe(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
        """Ensure the returned DataFrame meets minimum requirements."""
        if df is None or df.empty:
            raise ConnectorError(f"No data returned for {ticker}.")
        if "close" not in df.columns:
            raise ConnectorError(
                f"DataFrame for {ticker} is missing required 'close' column."
            )
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ConnectorError(
                f"DataFrame for {ticker} must have a DatetimeIndex."
            )
        return df

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(timeout={self.timeout})"
