"""Tests for domain models."""

import pytest

from cosee.models.asset import Asset, AssetType
from cosee.models.correlation_result import CorrelationResult


class TestAsset:
    def test_basic_creation(self):
        asset = Asset(ticker="aapl", name="Apple Inc.", asset_type=AssetType.STOCK)
        assert asset.ticker == "AAPL"  # uppercased
        assert asset.asset_type == AssetType.STOCK

    def test_ticker_normalised_to_uppercase(self):
        assert Asset(ticker="tsla").ticker == "TSLA"

    def test_empty_ticker_raises(self):
        with pytest.raises(ValueError):
            Asset(ticker="")

    def test_asset_type_from_string(self):
        asset = Asset(ticker="SPY", asset_type="etf")
        assert asset.asset_type == AssetType.ETF

    def test_equality(self):
        a1 = Asset(ticker="MSFT")
        a2 = Asset(ticker="msft")
        assert a1 == a2

    def test_hashable(self):
        s = {Asset(ticker="AAPL"), Asset(ticker="AAPL")}
        assert len(s) == 1

    def test_repr(self):
        r = repr(Asset(ticker="GLD", asset_type=AssetType.ETF))
        assert "GLD" in r
        assert "etf" in r


class TestCorrelationResult:
    def _make_result(self, corr: float) -> CorrelationResult:
        return CorrelationResult(
            asset_a=Asset(ticker="AAPL"),
            asset_b=Asset(ticker="MSFT"),
            correlation=corr,
        )

    def test_valid_correlation(self):
        r = self._make_result(0.85)
        assert r.correlation == 0.85

    def test_boundary_values(self):
        assert self._make_result(1.0).correlation == 1.0
        assert self._make_result(-1.0).correlation == -1.0

    def test_invalid_correlation_raises(self):
        with pytest.raises(ValueError):
            self._make_result(1.5)
        with pytest.raises(ValueError):
            self._make_result(-1.1)

    def test_pair_key_sorted(self):
        r = CorrelationResult(
            asset_a=Asset(ticker="MSFT"),
            asset_b=Asset(ticker="AAPL"),
            correlation=0.9,
        )
        assert r.pair_key == "AAPL/MSFT"

    def test_repr(self):
        r = self._make_result(0.75)
        assert "AAPL/MSFT" in repr(r)
