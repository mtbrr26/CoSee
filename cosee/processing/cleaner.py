"""Data cleaning utilities.

Handles:
  - Removal of duplicate index entries.
  - Filling / dropping missing values.
  - Outlier detection via z-score or IQR methods.
  - Removal of rows with zero or negative prices.
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataCleaner:
    """Cleans a raw OHLCV :class:`pandas.DataFrame`.

    Args:
        fill_method: Strategy for filling missing values.
            ``"ffill"``  – forward fill (default).
            ``"bfill"``  – backward fill.
            ``"drop"``   – drop rows with any NaN.
            ``"none"``   – leave NaNs untouched.
        drop_outliers: Whether to replace statistical outliers with NaN.
        outlier_std: Number of standard deviations to use as the outlier
            threshold (only used when *drop_outliers* is ``True``).
    """

    def __init__(
        self,
        fill_method: Literal["ffill", "bfill", "drop", "none"] = "ffill",
        drop_outliers: bool = False,
        outlier_std: float = 4.0,
    ) -> None:
        self.fill_method = fill_method
        self.drop_outliers = drop_outliers
        self.outlier_std = outlier_std

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply all cleaning steps to *df*.

        Args:
            df: Raw OHLCV DataFrame with a DatetimeIndex.

        Returns:
            Cleaned DataFrame.
        """
        df = df.copy()
        initial_len = len(df)

        # 1. Sort by date
        df = df.sort_index()

        # 2. Remove duplicate index entries (keep last)
        duplicates = df.index.duplicated(keep="last")
        if duplicates.any():
            logger.debug("Dropping %d duplicate rows.", duplicates.sum())
            df = df[~duplicates]

        # 3. Remove zero / negative prices
        price_cols = [c for c in ("open", "high", "low", "close", "adj_close") if c in df.columns]
        for col in price_cols:
            mask = df[col] <= 0
            if mask.any():
                logger.debug("Setting %d non-positive %s values to NaN.", mask.sum(), col)
                df.loc[mask, col] = np.nan

        # 4. Outlier detection on close price
        if self.drop_outliers and "close" in df.columns:
            df = self._remove_outliers(df, "close")

        # 5. Fill missing values
        if self.fill_method == "ffill":
            df = df.ffill()
        elif self.fill_method == "bfill":
            df = df.bfill()
        elif self.fill_method == "drop":
            before = len(df)
            df = df.dropna()
            logger.debug("Dropped %d rows with NaN.", before - len(df))
        # "none" → leave NaNs as-is

        logger.debug(
            "Cleaning: %d rows → %d rows (removed %d).",
            initial_len,
            len(df),
            initial_len - len(df),
        )
        return df

    def _remove_outliers(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        series = df[col]
        mean = series.mean()
        std = series.std()
        if std == 0:
            return df
        z_scores = (series - mean) / std
        mask = z_scores.abs() > self.outlier_std
        if mask.any():
            logger.debug(
                "Replacing %d outliers in '%s' (|z| > %.1f) with NaN.",
                mask.sum(),
                col,
                self.outlier_std,
            )
            df = df.copy()
            df.loc[mask, col] = np.nan
        return df
