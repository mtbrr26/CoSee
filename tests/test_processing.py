"""Tests for the data processing pipeline."""

import pytest
import numpy as np
import pandas as pd

from cosee.processing.cleaner import DataCleaner
from cosee.processing.normalizer import DataNormalizer
from cosee.processing.aligner import DataAligner
from cosee.processing.pipeline import ProcessingPipeline


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prices(n: int = 50, start: str = "2023-01-01", seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq="B")
    prices = 100 + np.cumsum(rng.normal(0, 1, n))
    df = pd.DataFrame(
        {
            "open": prices * 0.99,
            "high": prices * 1.01,
            "low": prices * 0.98,
            "close": prices,
            "volume": rng.integers(500_000, 2_000_000, n).astype(float),
        },
        index=idx,
    )
    df.index.name = "date"
    return df


# ---------------------------------------------------------------------------
# DataCleaner
# ---------------------------------------------------------------------------

class TestDataCleaner:
    def test_removes_duplicates(self):
        df = _make_prices(10)
        df = pd.concat([df, df.iloc[:2]])  # add duplicate rows
        cleaner = DataCleaner(fill_method="none")
        cleaned = cleaner.clean(df)
        assert not cleaned.index.duplicated().any()

    def test_zero_prices_become_nan(self):
        df = _make_prices(5)
        df.iloc[2, df.columns.get_loc("close")] = 0
        cleaner = DataCleaner(fill_method="none")
        cleaned = cleaner.clean(df)
        assert np.isnan(cleaned.iloc[2]["close"])

    def test_negative_prices_become_nan(self):
        df = _make_prices(5)
        df.iloc[1, df.columns.get_loc("close")] = -5.0
        cleaner = DataCleaner(fill_method="none")
        cleaned = cleaner.clean(df)
        assert np.isnan(cleaned.iloc[1]["close"])

    def test_ffill_fills_nans(self):
        df = _make_prices(5)
        df.iloc[2, df.columns.get_loc("close")] = np.nan
        cleaner = DataCleaner(fill_method="ffill")
        cleaned = cleaner.clean(df)
        assert not cleaned["close"].isna().any()

    def test_drop_fill_removes_rows(self):
        df = _make_prices(5)
        df.iloc[2, df.columns.get_loc("close")] = np.nan
        cleaner = DataCleaner(fill_method="drop")
        cleaned = cleaner.clean(df)
        assert len(cleaned) < len(df)

    def test_outlier_removal(self):
        df = _make_prices(50)
        df.iloc[10, df.columns.get_loc("close")] = 1_000_000.0  # extreme outlier
        cleaner = DataCleaner(drop_outliers=True, outlier_std=3.0, fill_method="none")
        cleaned = cleaner.clean(df)
        assert np.isnan(cleaned.iloc[10]["close"])


# ---------------------------------------------------------------------------
# DataNormalizer
# ---------------------------------------------------------------------------

class TestDataNormalizer:
    def test_log_return_no_nan(self):
        df = _make_prices(30)
        norm = DataNormalizer(method="log_return")
        result = norm.normalize(df)
        assert not result.isna().any()
        assert len(result) == len(df) - 1  # first row is dropped

    def test_pct_return_no_nan(self):
        df = _make_prices(30)
        norm = DataNormalizer(method="pct_return")
        result = norm.normalize(df)
        assert not result.isna().any()

    def test_min_max_bounded(self):
        df = _make_prices(30)
        norm = DataNormalizer(method="min_max")
        result = norm.normalize(df)
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_none_method_passthrough(self):
        df = _make_prices(10)
        norm = DataNormalizer(method="none")
        result = norm.normalize(df)
        assert list(result) == list(df["close"])

    def test_missing_column_raises(self):
        df = pd.DataFrame({"open": [1, 2, 3]}, index=pd.date_range("2023-01-01", periods=3))
        norm = DataNormalizer(price_col="close")
        with pytest.raises(KeyError):
            norm.normalize(df)

    def test_unknown_method_raises(self):
        df = _make_prices(10)
        norm = DataNormalizer(method="unknown_method")  # type: ignore[arg-type]
        with pytest.raises(ValueError):
            norm.normalize(df)


# ---------------------------------------------------------------------------
# DataAligner
# ---------------------------------------------------------------------------

class TestDataAligner:
    def _make_series(self, n: int, start: str = "2023-01-01", seed: int = 1) -> pd.Series:
        rng = np.random.default_rng(seed)
        idx = pd.date_range(start, periods=n, freq="B")
        return pd.Series(rng.normal(0, 1, n), index=idx)

    def test_inner_join_common_dates(self):
        s1 = self._make_series(20)
        s2 = self._make_series(15)  # shorter – fewer common dates
        aligner = DataAligner(join="inner")
        result = aligner.align({"A": s1, "B": s2})
        assert len(result) == 15

    def test_outer_join_full_union(self):
        s1 = self._make_series(20)
        s2 = self._make_series(15)
        aligner = DataAligner(join="outer")
        result = aligner.align({"A": s1, "B": s2})
        assert len(result) == 20

    def test_empty_input_returns_empty(self):
        aligner = DataAligner()
        result = aligner.align({})
        assert result.empty

    def test_columns_match_tickers(self):
        s1 = self._make_series(10)
        s2 = self._make_series(10, seed=2)
        aligner = DataAligner()
        result = aligner.align({"AAPL": s1, "MSFT": s2})
        assert set(result.columns) == {"AAPL", "MSFT"}


# ---------------------------------------------------------------------------
# ProcessingPipeline
# ---------------------------------------------------------------------------

class TestProcessingPipeline:
    def test_pipeline_produces_aligned_matrix(self):
        raw = {
            "AAPL": _make_prices(50, seed=1),
            "MSFT": _make_prices(50, seed=2),
            "TSLA": _make_prices(50, seed=3),
        }
        pipeline = ProcessingPipeline()
        result = pipeline.run(raw)
        assert not result.empty
        assert set(result.columns) == {"AAPL", "MSFT", "TSLA"}

    def test_empty_input_returns_empty(self):
        pipeline = ProcessingPipeline()
        result = pipeline.run({})
        assert result.empty

    def test_shape_is_dates_by_assets(self):
        raw = {
            "X": _make_prices(30, seed=10),
            "Y": _make_prices(30, seed=11),
        }
        pipeline = ProcessingPipeline()
        result = pipeline.run(raw)
        assert result.shape[1] == 2
