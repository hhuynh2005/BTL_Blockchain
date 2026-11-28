"""
Unit test cho module đánh giá (metrics, backtest, chainlink) và mô hình Comparable (Nam Khánh)
"""

import numpy as np
import pandas as pd
import pytest

from src.evaluation import (
    BacktestEngine,
    ChainlinkComparator,
    SMABaselineModel,
    ValuationMetrics,
    generate_market_data,
    generate_token_series,
)
from src.models import ComparableValuationModel, TWAPValuationModel


# ----------------------------------------------------------------- metrics
def test_metrics_known_values():
    y = pd.Series([100.0, 200.0, 300.0])
    p = pd.Series([110.0, 190.0, 330.0])
    assert ValuationMetrics.calculate_mae(y, p) == pytest.approx(50 / 3)
    assert ValuationMetrics.calculate_rmse(y, p) == pytest.approx(np.sqrt((100 + 100 + 900) / 3))
    assert ValuationMetrics.calculate_mape(y, p) == pytest.approx((10 + 5 + 10) / 3)
    assert ValuationMetrics.calculate_bias(y, p) == pytest.approx(10.0)


def test_metrics_perfect_prediction():
    y = pd.Series([1.0, 2.0, 3.0, 2.5])
    m = ValuationMetrics.evaluate_all(y, y.copy(), extended=True)
    assert m["MAE"] == 0 and m["RMSE"] == 0 and m["MAPE"] == 0
    assert m["R2"] == 1.0
    assert m["DirAcc"] == 100.0


def test_metrics_ignore_nan_and_zero():
    y = pd.Series([0.0, 10.0, np.nan, 20.0])
    p = pd.Series([1.0, 11.0, 5.0, 18.0])
    assert ValuationMetrics.calculate_mape(y, p) == pytest.approx((10 + 10) / 2)
    assert np.isfinite(ValuationMetrics.calculate_mae(y, p))


def test_metrics_align_on_index():
    y = pd.Series([1.0, 2.0, 3.0], index=[0, 1, 2])
    p = pd.Series([2.0, 3.0], index=[1, 2])
    assert ValuationMetrics.calculate_mae(y, p) == 0.0


# ----------------------------------------------------------------- comparable
def test_comparable_sector_benchmarks():
    df = pd.DataFrame(
        {
            "sector": ["DEX", "DEX", "Lending", "Lending"],
            "market_cap": [100.0, 300.0, 50.0, 50.0],
            "tvl": [100.0, 100.0, 100.0, 100.0],
            "circulating_supply": [10.0] * 4,
            "price_usd": [10.0, 30.0, 5.0, 5.0],
        }
    )
    m = ComparableValuationModel().fit(df)
    assert m.sector_benchmarks["DEX"] == pytest.approx(2.0)
    assert m.sector_benchmarks["Lending"] == pytest.approx(0.5)
    preds = m.predict(df)
    assert preds.tolist() == pytest.approx([20.0, 20.0, 5.0, 5.0])

    unseen = df.assign(sector="Other")
    assert m.sector_benchmark_mc_tvl == pytest.approx(0.75)  # trung vị toàn cục
    assert m.predict(unseen).tolist() == pytest.approx([7.5] * 4)


def test_comparable_handles_zero_tvl_and_supply():
    df = pd.DataFrame(
        {"market_cap": [100.0, 100.0], "tvl": [0.0, 50.0], "circulating_supply": [0.0, 10.0], "price_usd": [7.0, 8.0]}
    )
    m = ComparableValuationModel().fit(df)
    preds = m.predict(df)
    assert preds.dtype == float
    assert preds.iloc[0] == 7.0  # fallback về giá thị trường
    assert preds.iloc[1] == pytest.approx(2.0 * 50 / 10)


def test_relative_valuation_columns():
    df = generate_market_data(symbols=["UNI", "AAVE", "CRV"], days=30)
    latest = df[df["date"] == df["date"].max()]
    rel = ComparableValuationModel().fit(latest).relative_valuation(latest)
    assert {"mc_tvl", "benchmark_mc_tvl", "fair_price", "upside_%"} <= set(rel.columns)


# ----------------------------------------------------------------- backtest
@pytest.fixture
def token_df():
    return generate_token_series("UNI", days=120, seed=1)


def test_backtest_split_and_metrics(token_df):
    engine = BacktestEngine(train_ratio=0.7)
    train, test = engine.split(token_df)
    assert len(train) == 84 and len(test) == 36
    assert train["date"].max() < test["date"].min()
    metrics = engine.run_backtest(TWAPValuationModel(), token_df)
    assert set(metrics) == {"MAE", "RMSE", "MAPE"}
    assert metrics["MAPE"] >= 0


def test_walk_forward_covers_test_period(token_df):
    engine = BacktestEngine(train_ratio=0.5)
    res = engine.run_walk_forward(TWAPValuationModel(), token_df, step=10)
    assert res.test_size == 60
    assert res.extra["n_refits"] == 6
    assert res.predictions.index.equals(res.actual.index)


def test_sma_baseline_no_lookahead(token_df):
    engine = BacktestEngine(train_ratio=0.7)
    train, test = engine.split(token_df)
    model = SMABaselineModel(window=5).fit(train)
    preds = model.predict(test)
    expected_first = train["price_usd"].tail(5).mean()
    assert preds.iloc[0] == pytest.approx(expected_first)


def test_compare_models_includes_baseline(token_df):
    table = BacktestEngine().compare_models([TWAPValuationModel(), ComparableValuationModel()], token_df)
    assert "Baseline_SMA30" in table.index
    assert table["MAPE"].is_monotonic_increasing


def test_backtest_per_token():
    df = generate_market_data(symbols=["UNI", "LINK"], days=60)
    out = BacktestEngine().backtest_per_token(TWAPValuationModel, df)
    assert sorted(out["token"]) == ["LINK", "UNI"]


def test_invalid_train_ratio():
    with pytest.raises(ValueError):
        BacktestEngine(train_ratio=1.5)


# ----------------------------------------------------------------- chainlink
def test_chainlink_compare_and_summary():
    market = pd.Series([100.0, 102.0, 101.0, 105.0])
    oracle = ChainlinkComparator.simulate_oracle(market, deviation_threshold=0.015, heartbeat=10)
    assert oracle.tolist() == [100.0, 102.0, 102.0, 105.0]

    model = market * 1.1
    cmp = ChainlinkComparator.compare(model, market, oracle)
    assert cmp["model_vs_market_diff_%"].round(6).eq(10.0).all()

    summary = ChainlinkComparator.summarize(model, market, oracle)
    assert summary["n_obs"] == 4
    assert summary["corr_model_market"] == pytest.approx(1.0)
    assert summary["mean_model_vs_market_%"] == pytest.approx(10.0)


def test_fetch_latest_without_rpc(monkeypatch):
    monkeypatch.delenv("RPC_URL", raising=False)
    monkeypatch.delenv("MAINNET_RPC_URL", raising=False)
    assert ChainlinkComparator.fetch_latest("0x2c1d072e956affc0d435cb7ac38ef18d24d9127c") is None


# ----------------------------------------------------------------- sample data
def test_sample_data_schema():
    df = generate_market_data(symbols=["UNI"], days=10)
    required = {
        "date", "token", "price_usd", "volume_24h", "market_cap", "circulating_supply", "tvl", "tx_count",
        "active_addresses", "onchain_volume_usd", "pool_reserve0", "pool_reserve1", "velocity", "nvt_ratio",
    }
    assert required <= set(df.columns)
    assert (df["price_usd"] > 0).all()
    pd.testing.assert_frame_equal(df, generate_market_data(symbols=["UNI"], days=10))
