"""Connector factory.

Instantiates the appropriate :class:`~cosee.ingestion.base.BaseConnector`
based on the configured ``data_source`` setting.

Usage::

    from cosee.ingestion.factory import get_connector
    connector = get_connector()  # uses settings.data_source
"""

from __future__ import annotations

from cosee.ingestion.base import BaseConnector


def get_connector(source: str | None = None) -> BaseConnector:
    """Return a connector instance for the given *source* name.

    Args:
        source: Connector identifier.  If ``None``, falls back to
                ``settings.data_source``.  Supported values:
                ``"yahoo_finance"``, ``"alpha_vantage"``.

    Returns:
        A concrete :class:`BaseConnector` instance.

    Raises:
        ValueError: For unknown source names.
    """
    from cosee.config import settings  # lazy – avoid circular imports

    name = (source or settings.data_source).lower().strip()

    if name == "yahoo_finance":
        from cosee.ingestion.yahoo_finance import YahooFinanceConnector

        return YahooFinanceConnector()

    if name == "alpha_vantage":
        from cosee.ingestion.alpha_vantage import AlphaVantageConnector

        return AlphaVantageConnector()

    raise ValueError(
        f"Unknown data source '{name}'. "
        "Supported sources: 'yahoo_finance', 'alpha_vantage'."
    )
