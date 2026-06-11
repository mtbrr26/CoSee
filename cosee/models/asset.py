"""Asset domain model."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AssetType(str, Enum):
    """Supported asset categories."""

    STOCK = "stock"
    ETF = "etf"
    COMMODITY = "commodity"
    INDEX = "index"
    COMPANY = "company"   # Non-equity or private-company data feeds
    UNKNOWN = "unknown"


@dataclass
class Asset:
    """Represents a single tradeable or trackable market asset.

    Attributes:
        ticker: Exchange ticker symbol (e.g. "AAPL", "GC=F").
        name: Human-readable display name.
        asset_type: Category of the asset.
        exchange: Exchange or market the asset trades on.
        currency: Denomination currency (ISO 4217).
        metadata: Arbitrary extra fields for extensibility.
    """

    ticker: str
    name: str = ""
    asset_type: AssetType = AssetType.UNKNOWN
    exchange: str = ""
    currency: str = "USD"
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.ticker:
            raise ValueError("Asset ticker must not be empty.")
        self.ticker = self.ticker.upper().strip()
        if isinstance(self.asset_type, str):
            self.asset_type = AssetType(self.asset_type.lower())

    def __repr__(self) -> str:
        return f"Asset(ticker={self.ticker!r}, type={self.asset_type.value})"

    def __hash__(self) -> int:
        return hash(self.ticker)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Asset):
            return NotImplemented
        return self.ticker == other.ticker
