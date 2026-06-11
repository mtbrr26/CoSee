"""Time-series alignment utilities.

Aligns multiple return series onto a common date index so that the
correlation engine can work on consistently shaped data.

Strategies
----------
``"inner"``  – only dates present in **all** series  (default).
``"outer"``  – union of all dates; missing values filled with NaN.
``"left"``   – use the first series as the reference index.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Literal, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataAligner:
    """Aligns a collection of return series to a shared date grid.

    Args:
        join: Pandas merge/join strategy applied when concatenating series.
        fill_method: How to fill NaNs introduced by the outer/left join.
            ``"ffill"`` – forward fill, ``"drop"`` – drop incomplete rows,
            ``"none"`` – leave untouched.
    """

    def __init__(
        self,
        join: Literal["inner", "outer", "left"] = "inner",
        fill_method: Literal["ffill", "drop", "none"] = "none",
    ) -> None:
        self.join = join
        self.fill_method = fill_method

    def align(
        self,
        series: Dict[str, pd.Series],
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        """Align all *series* onto a common DatetimeIndex.

        Args:
            series: Mapping of ``ticker -> return Series`` (DatetimeIndex).
            start: Optional start date filter.
            end: Optional end date filter.

        Returns:
            A :class:`pd.DataFrame` where each column is a ticker and each
            row is a date.  Shape: ``(dates, tickers)``.
        """
        if not series:
            return pd.DataFrame()

        combined = pd.concat(series.values(), axis=1, join=self.join)
        combined.columns = list(series.keys())
        combined.index = pd.to_datetime(combined.index)
        combined = combined.sort_index()

        if start is not None:
            combined = combined.loc[combined.index >= pd.Timestamp(start)]
        if end is not None:
            combined = combined.loc[combined.index <= pd.Timestamp(end)]

        if self.fill_method == "ffill":
            combined = combined.ffill()
        elif self.fill_method == "drop":
            combined = combined.dropna()

        logger.debug(
            "Aligned %d series into DataFrame of shape %s (join='%s').",
            len(series),
            combined.shape,
            self.join,
        )
        return combined

    def align_list(
        self,
        tickers: List[str],
        series_map: Dict[str, pd.Series],
        **kwargs,
    ) -> pd.DataFrame:
        """Convenience wrapper – filters *series_map* to *tickers* before aligning."""
        filtered = {t: series_map[t] for t in tickers if t in series_map}
        return self.align(filtered, **kwargs)
