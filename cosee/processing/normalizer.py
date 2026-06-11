"""Data normalisation utilities.

Transforms raw price data into stationary return series suitable for
correlation analysis.

Supported modes
---------------
``"log_return"``      – natural-log daily returns  (default, recommended).
``"pct_return"``      – simple percentage returns.
``"z_score"``         – rolling z-score normalisation.
``"min_max"``         – scale to [0, 1] over the whole series.
``"none"``            – pass through unchanged.
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalises a price series into a return / score series.

    Args:
        method: Normalisation strategy (see module docstring).
        price_col: Column to normalise (default ``"close"``).
        z_window: Rolling window for z-score normalisation.
    """

    def __init__(
        self,
        method: Literal["log_return", "pct_return", "z_score", "min_max", "none"] = "log_return",
        price_col: str = "close",
        z_window: int = 20,
    ) -> None:
        self.method = method
        self.price_col = price_col
        self.z_window = z_window

    def normalize(self, df: pd.DataFrame) -> pd.Series:
        """Compute the normalised return series for *df*.

        Args:
            df: Cleaned OHLCV DataFrame with a DatetimeIndex.

        Returns:
            A :class:`pandas.Series` indexed by date.

        Raises:
            KeyError: If *price_col* is not in *df*.
        """
        if self.price_col not in df.columns:
            raise KeyError(
                f"Column '{self.price_col}' not found in DataFrame. "
                f"Available: {list(df.columns)}"
            )

        prices = df[self.price_col].dropna()

        if self.method == "log_return":
            result = np.log(prices / prices.shift(1)).dropna()
        elif self.method == "pct_return":
            result = prices.pct_change().dropna()
        elif self.method == "z_score":
            roll_mean = prices.rolling(self.z_window).mean()
            roll_std = prices.rolling(self.z_window).std()
            result = ((prices - roll_mean) / roll_std).dropna()
        elif self.method == "min_max":
            mn, mx = prices.min(), prices.max()
            result = (prices - mn) / (mx - mn) if mx != mn else prices * 0
        elif self.method == "none":
            result = prices
        else:
            raise ValueError(f"Unknown normalisation method: {self.method!r}")

        logger.debug(
            "Normalised %d rows using method='%s'.", len(result), self.method
        )
        return result
