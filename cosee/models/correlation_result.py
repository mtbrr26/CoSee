"""CorrelationResult domain model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from cosee.models.asset import Asset


@dataclass
class CorrelationResult:
    """Stores the correlation between two assets over a given window.

    Attributes:
        asset_a: First asset in the pair.
        asset_b: Second asset in the pair.
        correlation: Pearson correlation coefficient in [-1, 1].
        window: Rolling window size in trading days (None = full period).
        series: Optional time-series of rolling correlation values.
        p_value: Optional p-value for statistical significance.
    """

    asset_a: Asset
    asset_b: Asset
    correlation: float
    window: Optional[int] = None
    series: Optional[pd.Series] = None
    p_value: Optional[float] = None

    def __post_init__(self) -> None:
        if not -1.0 <= self.correlation <= 1.0:
            raise ValueError(
                f"Correlation must be in [-1, 1], got {self.correlation}."
            )

    @property
    def pair_key(self) -> str:
        """Deterministic pair identifier (alphabetically sorted)."""
        tickers = sorted([self.asset_a.ticker, self.asset_b.ticker])
        return f"{tickers[0]}/{tickers[1]}"

    def __repr__(self) -> str:
        return (
            f"CorrelationResult(pair={self.pair_key}, "
            f"correlation={self.correlation:.4f}, window={self.window})"
        )
