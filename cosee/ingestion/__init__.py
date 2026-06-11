"""Data ingestion subpackage."""

from cosee.ingestion.base import BaseConnector, ConnectorError
from cosee.ingestion.yahoo_finance import YahooFinanceConnector
from cosee.ingestion.alpha_vantage import AlphaVantageConnector
from cosee.ingestion.factory import get_connector

__all__ = [
    "BaseConnector",
    "ConnectorError",
    "YahooFinanceConnector",
    "AlphaVantageConnector",
    "get_connector",
]
