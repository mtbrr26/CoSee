"""Tests for the correlation engine."""

import pytest
import numpy as np
import pandas as pd

from cosee.correlation.engine import CorrelationEngine
from cosee.models.asset import Asset
from cosee.models.correlation_result import CorrelationResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_aligned(n: int = 100, tickers=("AAPL", "MSFT", "TSLA"), seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    data = {t: rng.normal(0, 1, n) for t in tickers}
    return pd.DataFrame(data, index=idx)


def _make_correlated(n: int = 100, noise: float = 0.1) -> pd.DataFrame:
    """Return a two-column DataFrame where the columns are highly correlated."""
    rng = np.random.default_rng(42)
    idx = pd.date_range("2022-01-01", periods=n, freq="B")
    base = rng.normal(0, 1, n)
    a = base + rng.normal(0, noise, n)
    b = base + rng.normal(0, noise, n)
    return pd.DataFrame({"A": a, "B": b}, index=idx)


# ---------------------------------------------------------------------------
# CorrelationEngine
# ---------------------------------------------------------------------------

class TestCorrelationEngine:
    def test_returns_list_of_results(self):
        df = _make_aligned()
        engine = CorrelationEngine(window=20, top_n=10)
        results = engine.run(df)
        assert isinstance(results, list)
        assert all(isinstance(r, CorrelationResult) for r in results)

    def test_top_n_respected(self):
        df = _make_aligned(tickers=("A", "B", "C", "D", "E"))
        engine = CorrelationEngine(window=20, top_n=3)
        results = engine.run(df)
        assert len(results) <= 3

    def test_sorted_by_abs_correlation(self):
        df = _make_aligned(tickers=("A", "B", "C", "D"))
        engine = CorrelationEngine(window=20, top_n=10)
        results = engine.run(df)
        abs_corrs = [abs(r.correlation) for r in results]
        assert abs_corrs == sorted(abs_corrs, reverse=True)

    def test_high_correlation_detected(self):
        df = _make_correlated(n=200, noise=0.05)
        engine = CorrelationEngine(window=None, top_n=1)
        results = engine.run(df)
        assert len(results) == 1
        assert abs(results[0].correlation) > 0.95

    def test_full_period_static_correlation(self):
        df = _make_aligned()
        engine = CorrelationEngine(window=None, top_n=5)
        results = engine.run(df)
        assert results
        for r in results:
            assert r.window is None
            assert r.series is None

    def test_rolling_series_present_when_window_set(self):
        df = _make_aligned(n=100)
        engine = CorrelationEngine(window=20, top_n=3)
        results = engine.run(df)
        for r in results:
            assert r.series is not None
            assert isinstance(r.series, pd.Series)

    def test_empty_dataframe_returns_empty_list(self):
        engine = CorrelationEngine()
        assert engine.run(pd.DataFrame()) == []

    def test_single_column_returns_empty_list(self):
        idx = pd.date_range("2022-01-01", periods=50, freq="B")
        df = pd.DataFrame({"AAPL": np.random.randn(50)}, index=idx)
        engine = CorrelationEngine()
        assert engine.run(df) == []

    def test_correlation_matrix_shape(self):
        tickers = ("A", "B", "C")
        df = _make_aligned(tickers=tickers)
        engine = CorrelationEngine()
        matrix = engine.correlation_matrix(df)
        assert matrix.shape == (3, 3)
        # Diagonal must be 1.0
        for t in tickers:
            assert matrix.loc[t, t] == pytest.approx(1.0)

    def test_correlation_values_in_range(self):
        df = _make_aligned(n=100, tickers=("X", "Y", "Z"))
        engine = CorrelationEngine(window=30, top_n=10)
        results = engine.run(df)
        for r in results:
            assert -1.0 <= r.correlation <= 1.0
