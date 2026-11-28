"""
Sinh dữ liệu mô phỏng theo đúng SCHEMA.md phục vụ thử nghiệm, dashboard và unit test
khi chưa có dữ liệu thu thập thật trong data/processed/ (Nam Khánh phụ trách).

Giá được sinh xoay quanh "giá trị nền tảng" (hàm của on-chain volume và TVL) cộng nhiễu
đầu cơ có tính tự tương quan, nên các mô hình định giá có tín hiệu để đánh giá.
"""

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Tham số khởi tạo gần đúng cho một số token (giá, supply, TVL)
DEFAULT_PROFILES: Dict[str, Dict] = {
    "UNI": {"sector": "DEX", "price": 8.5, "supply": 600e6, "tvl": 4.5e9},
    "CRV": {"sector": "DEX", "price": 0.55, "supply": 1.2e9, "tvl": 2.0e9},
    "SUSHI": {"sector": "DEX", "price": 1.1, "supply": 260e6, "tvl": 0.35e9},
    "BAL": {"sector": "DEX", "price": 3.8, "supply": 60e6, "tvl": 0.9e9},
    "AAVE": {"sector": "Lending", "price": 95.0, "supply": 14.8e6, "tvl": 11e9},
    "COMP": {"sector": "Lending", "price": 55.0, "supply": 8.5e6, "tvl": 2.5e9},
    "MKR": {"sector": "Lending", "price": 1500.0, "supply": 0.92e6, "tvl": 6.5e9},
    "LINK": {"sector": "Infrastructure", "price": 14.0, "supply": 587e6, "tvl": 1.0e9},
    "GRT": {"sector": "Infrastructure", "price": 0.18, "supply": 9.5e9, "tvl": 0.6e9},
    "LDO": {"sector": "Liquid Staking", "price": 2.0, "supply": 890e6, "tvl": 28e9},
    "SNX": {"sector": "Derivatives", "price": 2.5, "supply": 330e6, "tvl": 0.6e9},
    "ARB": {"sector": "Infrastructure", "price": 1.0, "supply": 3.0e9, "tvl": 2.5e9},
}


def generate_token_series(
    symbol: str,
    days: int = 365,
    start: str = "2025-11-28",
    seed: Optional[int] = None,
    profile: Optional[Dict] = None,
) -> pd.DataFrame:
    prof = profile or DEFAULT_PROFILES.get(symbol, {"sector": "Other", "price": 10.0, "supply": 100e6, "tvl": 1e9})
    rng = np.random.default_rng(seed if seed is not None else sum(map(ord, symbol)))

    dates = pd.date_range(start=start, periods=days, freq="D")
    supply = np.full(days, prof["supply"]) * (1 + np.linspace(0, 0.03, days))  # lạm phát nhẹ

    # Yếu tố nền tảng: random walk log cho TVL và on-chain activity
    fundamental = np.cumsum(rng.normal(0.0005, 0.02, days))
    tvl = prof["tvl"] * np.exp(fundamental + rng.normal(0, 0.01, days))

    # Nhiễu đầu cơ AR(1) quanh giá trị nền tảng
    spec = np.zeros(days)
    for i in range(1, days):
        spec[i] = 0.93 * spec[i - 1] + rng.normal(0, 0.03)
    price = prof["price"] * np.exp(fundamental + spec)

    market_cap = price * supply
    velocity_true = rng.uniform(0.04, 0.12)
    onchain_vol = market_cap * velocity_true * np.exp(rng.normal(0, 0.15, days))
    volume_24h = onchain_vol * rng.uniform(1.1, 1.6) * np.exp(rng.normal(0, 0.2, days))

    tx_count = (onchain_vol / price / rng.uniform(800, 3000)).astype(int) + 1000
    active = (tx_count * rng.uniform(0.25, 0.45)).astype(int)

    # Pool Uniswap: reserve0 = token, reserve1 = USD (giá AMM bám sát spot ± 1%)
    reserve0 = np.full(days, prof["tvl"] * 0.01 / prof["price"])
    reserve1 = reserve0 * price * (1 + rng.normal(0, 0.01, days))

    df = pd.DataFrame(
        {
            "date": dates,
            "token": symbol,
            "sector": prof["sector"],
            "price_usd": price,
            "volume_24h": volume_24h,
            "market_cap": market_cap,
            "circulating_supply": supply,
            "tvl": tvl,
            "tx_count": tx_count,
            "active_addresses": active,
            "onchain_volume_usd": onchain_vol,
            "pool_reserve0": reserve0,
            "pool_reserve1": reserve1,
        }
    )
    df["velocity"] = df["onchain_volume_usd"] / df["market_cap"]
    df["nvt_ratio"] = df["market_cap"] / df["onchain_volume_usd"]
    return df


def generate_market_data(
    symbols: Optional[List[str]] = None, days: int = 365, seed: int = 42, start: str = "2025-11-28"
) -> pd.DataFrame:
    symbols = symbols or list(DEFAULT_PROFILES)
    frames = [generate_token_series(s, days=days, start=start, seed=seed + i) for i, s in enumerate(symbols)]
    return pd.concat(frames, ignore_index=True)


def load_market_data(
    path: str = "data/processed/market_data.csv", fallback_days: int = 365, min_rows_per_token: int = 60
) -> pd.DataFrame:
    """
    Đọc dữ liệu đã tiền xử lý nếu có đủ lịch sử, ngược lại sinh dữ liệu mô phỏng.
    Cột `sector` được bổ sung từ DEFAULT_PROFILES nếu thiếu.
    """
    p = Path(path)
    if p.exists():
        df = pd.read_csv(p, parse_dates=["date"])
        if not df.empty and df.groupby("token").size().min() >= min_rows_per_token:
            if "sector" not in df.columns:
                df["sector"] = df["token"].map(lambda t: DEFAULT_PROFILES.get(t, {}).get("sector", "Other"))
            df.attrs["source"] = str(p)
            return df
    df = generate_market_data(days=fallback_days)
    df.attrs["source"] = "synthetic"
    return df
