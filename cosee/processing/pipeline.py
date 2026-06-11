"""End-to-end data processing pipeline.

Combines :class:`~cosee.processing.cleaner.DataCleaner`,
:class:`~cosee.processing.normalizer.DataNormalizer`, and
:class:`~cosee.processing.aligner.DataAligner` into a single composable
pipeline that takes raw OHLCV DataFrames and produces an aligned returns
matrix ready for the correlation engine.

Usage::

    from cosee.processing.pipeline import ProcessingPipeline

    pipeline = ProcessingPipeline()
    aligned_df = pipeline.run(raw_data)  # raw_data: dict[ticker, DataFrame]
"""

from __future__ import annotations

import logging
from typing import Dict, Optional

import pandas as pd

from cosee.processing.aligner import DataAligner
from cosee.processing.cleaner import DataCleaner
from cosee.processing.normalizer import DataNormalizer

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Orchestrates cleaning → normalisation → alignment.

    Args:
        cleaner: :class:`DataCleaner` instance (created with defaults if None).
        normalizer: :class:`DataNormalizer` instance (defaults if None).
        aligner: :class:`DataAligner` instance (defaults if None).
    """

    def __init__(
        self,
        cleaner: Optional[DataCleaner] = None,
        normalizer: Optional[DataNormalizer] = None,
        aligner: Optional[DataAligner] = None,
    ) -> None:
        self.cleaner = cleaner or DataCleaner()
        self.normalizer = normalizer or DataNormalizer()
        self.aligner = aligner or DataAligner()

    def run(
        self,
        raw_data: Dict[str, pd.DataFrame],
        start: Optional[pd.Timestamp] = None,
        end: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        """Process *raw_data* and return an aligned returns matrix.

        Args:
            raw_data: Mapping of ``ticker -> OHLCV DataFrame``.
            start: Optional start date filter applied after alignment.
            end: Optional end date filter applied after alignment.

        Returns:
            DataFrame of shape ``(dates, tickers)`` containing normalised
            return series aligned to a common date index.
        """
        if not raw_data:
            logger.warning("ProcessingPipeline.run() called with empty data.")
            return pd.DataFrame()

        return_series: Dict[str, pd.Series] = {}

        for ticker, df in raw_data.items():
            try:
                clean_df = self.cleaner.clean(df)
                returns = self.normalizer.normalize(clean_df)
                return_series[ticker] = returns
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to process %s: %s", ticker, exc)

        if not return_series:
            logger.error("All assets failed processing. Returning empty DataFrame.")
            return pd.DataFrame()

        aligned = self.aligner.align(return_series, start=start, end=end)
        logger.info(
            "Pipeline produced aligned matrix: %d dates × %d assets.",
            aligned.shape[0],
            aligned.shape[1],
        )
        return aligned
