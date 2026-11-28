"""
Unit test cho các module của Khanh: DataCleaner, FeatureEngineer, MVPQValuationModel,
và phần phân tích JSON của CoinGecko / DefiLlama (không gọi mạng).
"""

import numpy as np
import pandas as pd
import pytest

from src.collectors.coingecko import CoinGeckoCollector
from src.collectors.defillama import DefiLlamaCollector
from src.models.mv_pq import MVPQValuationModel
from src.preprocessing.clean import DataCleaner
from src.preprocessing.features import FeatureEngineer


def make_token(symbol, price, n=60, start="2026-01-01", volume=1e8, supply=1e6, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=n, freq="D")
    p = price * np.exp(np.cumsum(rng.normal(0, 0.02, n)))
    vol = volume * np.exp(rng.normal(0, 0.2, n))
    return pd.DataFrame({
        "date": dates, "token": symbol, "price_usd": p, "volume_24h": vol,
        "market_cap": p * supply, "circulating_supply": supply, "tvl": 5e8,
    })


# ---------------------------------------------------------------- DataCleaner
def test_cleaning_is_per_token_and_keeps_high_prices():
    df = pd.concat([make_token("UNI", 8), make_token("BTC", 68_000, seed=1)])
    out = DataCleaner.clean_token_dataset(df)
    btc_in = df[df.token == "BTC"].price_usd.to_numpy()
    btc_out = out[out.token == "BTC"].price_usd.to_numpy()
    np.testing.assert_allclose(btc_out, btc_in)


def test_ffill_limited_to_three_days_and_no_backfill():
    df = make_token("UNI", 8, n=10)
    df = df.drop(index=[3, 4, 5, 6, 7])  # khoảng trống 5 ngày
    out = DataCleaner.clean_timeseries(df)
    assert len(out) == 10
    assert out.loc[3:5, "price_usd"].notna().all()   # 3 ngày đầu được điền
    assert out.loc[6:7, "price_usd"].isna().all()    # phần còn lại để trống
    assert out.loc[3:7, "is_filled"].all()
    assert out["token"].eq("UNI").all()


def test_duplicate_dates_and_intraday_timestamps_are_normalized():
    df = pd.DataFrame({
        "date": ["2026-01-01T00:00:00Z", "2026-01-01T13:00:00Z", "2026-01-02T00:00:00Z"],
        "price_usd": [1.0, 2.0, 3.0],
    })
    out = DataCleaner.clean_timeseries(df)
    assert list(out["date"].dt.strftime("%Y-%m-%d")) == ["2026-01-01", "2026-01-02"]
    assert out["price_usd"].tolist() == [2.0, 3.0]  # giữ bản ghi mới nhất trong ngày


def test_invalid_values_become_missing():
    df = make_token("UNI", 8, n=5)
    df.loc[2, "price_usd"] = -1
    df.loc[3, "volume_24h"] = -5
    out = DataCleaner.validate_values(df)
    assert pd.isna(out.loc[2, "price_usd"]) and pd.isna(out.loc[3, "volume_24h"])


def test_volume_anomaly_flag_and_winsorization():
    df = make_token("UNI", 8, n=60)
    df.loc[45, "volume_24h"] *= 50
    flagged = DataCleaner.flag_volume_anomalies(df)
    assert flagged.loc[45, "is_anomaly"] and flagged["is_anomaly"].sum() == 1

    clipped = DataCleaner.remove_outliers_iqr(df, "volume_24h")
    assert clipped.loc[45, "volume_24h"] < df.loc[45, "volume_24h"] / 5
    others = df.index != 45
    # các ngày bình thường gần như không bị đụng tới
    assert (clipped.loc[others, "volume_24h"] == df.loc[others, "volume_24h"]).mean() > 0.95


# ---------------------------------------------------------------- FeatureEngineer
def test_features_do_not_leak_across_tokens():
    df = pd.concat([make_token("AAA", 10, n=20), make_token("BBB", 1000, n=20, seed=2)])
    out = FeatureEngineer.generate_features(df)
    first_bbb = out[out.token == "BBB"].iloc[0]
    assert pd.isna(first_bbb["returns"])            # không lấy giá AAA làm ngày trước
    assert first_bbb["ma_7"] == pytest.approx(first_bbb["price_usd"])
    v = out["velocity"].to_numpy()
    np.testing.assert_allclose(v, out["volume_24h"] * 365 / out["market_cap"])


def test_liquidity_score_bounds():
    s = FeatureEngineer.liquidity_score(pd.Series([1e3, 1e6, 3.16e7, 1e9, 1e12]))
    assert s.iloc[0] == 0 and s.iloc[-1] == 1 and s.iloc[2] == pytest.approx(0.5, abs=0.01)


# ---------------------------------------------------------------- MV = PQ
def test_mvpq_fixed_velocity_matches_formula():
    df = make_token("UNI", 10, n=30, volume=5e7, supply=1e8)
    model = MVPQValuationModel(velocity=10.0, pq_smoothing=1).fit(df)
    expected = df["volume_24h"] * 365 / (10.0 * df["circulating_supply"])
    np.testing.assert_allclose(model.predict(df), expected)


def test_mvpq_walk_forward_has_no_lookahead():
    df = make_token("UNI", 10, n=60)
    model = MVPQValuationModel(velocity_window=30)
    base = model.predict_walk_forward(df)
    shocked = df.copy()
    shocked.loc[50:, "volume_24h"] *= 10  # thay đổi tương lai
    after = model.predict_walk_forward(shocked)
    np.testing.assert_allclose(base.iloc[:50].dropna(), after.iloc[:50].dropna())
    assert base.iloc[:14].isna().all() and base.iloc[14:].notna().all()


def test_mvpq_is_not_a_copy_of_market_price():
    df = make_token("UNI", 10, n=60)
    res = MVPQValuationModel().analyze_valuation(df)
    valid = res.dropna(subset=["fair_price"])
    assert not np.allclose(valid["fair_price"], valid["price_usd"])
    assert set(valid["signal"]) <= {"Overvalued", "Undervalued", "Fair Value"}


def test_mvpq_signal_direction():
    model = MVPQValuationModel(signal_threshold_pct=10)
    assert model.classify(25) == "Overvalued"
    assert model.classify(-25) == "Undervalued"
    assert model.classify(5) == "Fair Value"


# ---------------------------------------------------------------- Collectors (offline)
def test_coingecko_parse_dedupes_today_point(tmp_path):
    day = 86_400_000
    t0 = 1_767_225_600_000  # 2026-01-01 00:00 UTC
    data = {
        "prices": [[t0, 100.0], [t0 + day, 110.0], [t0 + day + 3_600_000, 999.0]],
        "market_caps": [[t0, 1e9], [t0 + day, 1.1e9], [t0 + day + 3_600_000, 9e9]],
        "total_volumes": [[t0, 5e7], [t0 + day, 6e7], [t0 + day + 3_600_000, 9e7]],
    }
    df = CoinGeckoCollector.parse_market_chart(data, "SOL")
    assert len(df) == 2 and df["price_usd"].tolist() == [100.0, 110.0]
    assert df["circulating_supply"].iloc[0] == pytest.approx(1e7)
    assert CoinGeckoCollector(cache_dir=str(tmp_path)).get_coin_id("sol") == "solana"


def test_defillama_routes_chain_tokens(tmp_path):
    c = DefiLlamaCollector(cache_dir=str(tmp_path))
    assert c.is_chain_token("SOL") and not c.is_chain_token("UNI")
    df = c._to_daily([{"date": 1_767_225_600, "tvl": 1.0}, {"date": 1_767_250_000, "tvl": 2.0}],
                     "date", "tvl", "SOL", "tvl")
    assert len(df) == 1 and df["tvl"].iloc[0] == 2.0
