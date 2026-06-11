"""Correlation engine.

Computes pairwise Pearson correlations (both static and rolling) over an
aligned returns matrix, then surfaces the top correlated pairs.

Usage::

    from cosee.correlation.engine import CorrelationEngine
    import pandas as pd

    engine = CorrelationEngine(window=30, top_n=10)
    results = engine.run(aligned_df)
    for r in results:
        print(r)
"""

from __future__ import annotations

import itertools
import logging
from typing import List, Optional

import numpy as np
import pandas as pd
from scipy import stats  # optional; gracefully degrades if unavailable

from cosee.models.asset import Asset
from cosee.models.correlation_result import CorrelationResult

logger = logging.getLogger(__name__)


class CorrelationEngine:
    """Computes pairwise correlations between asset return series.

    Args:
        window: Rolling window in trading days.  Use ``None`` for a single
                full-period (static) correlation.
        top_n: Number of top pairs to return (ranked by |correlation|).
        method: Correlation method: ``"pearson"`` (default) or ``"spearman"``.
        min_periods: Minimum number of overlapping observations required.
        compute_pvalue: Whether to compute p-values (requires ``scipy``).
    """

    def __init__(
        self,
        window: Optional[int] = 30,
        top_n: int = 20,
        method: str = "pearson",
        min_periods: Optional[int] = None,
        compute_pvalue: bool = False,
    ) -> None:
        self.window = window
        self.top_n = top_n
        self.method = method
        self.min_periods = min_periods
        self.compute_pvalue = compute_pvalue

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, returns: pd.DataFrame) -> List[CorrelationResult]:
        """Compute correlations and return the top-N pairs.

        Args:
            returns: Aligned returns matrix from
                     :class:`~cosee.processing.pipeline.ProcessingPipeline`.
                     Shape: ``(dates, tickers)``.

        Returns:
            List of :class:`~cosee.models.correlation_result.CorrelationResult`
            sorted by descending absolute correlation.
        """
        if returns.empty or returns.shape[1] < 2:
            logger.warning("Correlation engine requires at least 2 assets.")
            return []

        tickers = list(returns.columns)
        results: List[CorrelationResult] = []

        for ticker_a, ticker_b in itertools.combinations(tickers, 2):
            series_a = returns[ticker_a].dropna()
            series_b = returns[ticker_b].dropna()

            corr_value, rolling_series, p_val = self._compute_correlation(
                series_a, series_b
            )

            if corr_value is None or np.isnan(corr_value):
                logger.debug("Skipping %s/%s – not enough data.", ticker_a, ticker_b)
                continue

            result = CorrelationResult(
                asset_a=Asset(ticker=ticker_a),
                asset_b=Asset(ticker=ticker_b),
                correlation=corr_value,
                window=self.window,
                series=rolling_series,
                p_value=p_val,
            )
            results.append(result)

        # Sort by absolute correlation (descending)
        results.sort(key=lambda r: abs(r.correlation), reverse=True)
        top = results[: self.top_n]

        logger.info(
            "Found %d pairs; returning top %d (window=%s).",
            len(results),
            len(top),
            self.window,
        )
        return top

    def correlation_matrix(self, returns: pd.DataFrame) -> pd.DataFrame:
        """Return the full pairwise correlation matrix.

        Args:
            returns: Aligned returns DataFrame.

        Returns:
            Square :class:`pd.DataFrame` of Pearson/Spearman correlations.
        """
        return returns.corr(method=self.method)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_correlation(
        self,
        series_a: pd.Series,
        series_b: pd.Series,
    ):
        """Compute correlation between two series.

        Returns:
            Tuple of ``(scalar_correlation, rolling_series_or_None, p_value_or_None)``.
        """
        # Align the two series on their common dates.
        aligned = pd.concat([series_a, series_b], axis=1, join="inner").dropna()
        if len(aligned) < 2:
            return None, None, None

        col_a, col_b = aligned.columns[0], aligned.columns[1]

        # -- Rolling correlation ------------------------------------------
        rolling_series: Optional[pd.Series] = None
        if self.window is not None:
            min_p = self.min_periods or max(2, self.window // 2)
            rolling_series = (
                aligned[col_a]
                .rolling(self.window, min_periods=min_p)
                .corr(aligned[col_b])
            )
            # Use the last valid value as the scalar summary.
            last_valid = rolling_series.dropna()
            corr_value = float(last_valid.iloc[-1]) if not last_valid.empty else None
        else:
            # Static full-period correlation.
            if self.method == "pearson":
                corr_value = float(aligned[col_a].corr(aligned[col_b]))
            else:
                corr_value = float(
                    aligned[col_a].corr(aligned[col_b], method="spearman")
                )

        # -- P-value (optional) -------------------------------------------
        p_val: Optional[float] = None
        if self.compute_pvalue and corr_value is not None:
            try:
                _, p_val = stats.pearsonr(aligned[col_a], aligned[col_b])
            except Exception:  # noqa: BLE001
                pass

        return corr_value, rolling_series, p_val
