"""
Xây dựng bộ dữ liệu thị trường hợp nhất theo ``data/SCHEMA.md`` từ CoinGecko + DefiLlama (Khanh phụ trách).

Chạy:
    python -m src.preprocessing.build_dataset                       # BTC, ETH, SOL, 365 ngày
    python -m src.preprocessing.build_dataset --tokens UNI AAVE --days 180

Kết quả: ``data/processed/market_dataset.csv`` (đã làm sạch) và
``data/processed/market_dataset_raw.csv`` (trước khi làm sạch, để đối chiếu).
Các trường on-chain (tx_count, active_addresses, ...) do collectors của Kha cung cấp; nếu
chưa có sẽ để trống (NaN) đúng tên cột.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.collectors.coingecko import CoinGeckoCollector
from src.collectors.defillama import DefiLlamaCollector
from src.preprocessing.clean import DataCleaner

SCHEMA_COLUMNS = [
    "date", "token", "price_usd", "volume_24h", "market_cap", "circulating_supply", "tvl",
    "tx_count", "active_addresses", "onchain_volume_usd", "pool_reserve0", "pool_reserve1",
]
EXTRA_COLUMNS = ["fees_usd", "revenue_usd"]
DEFAULT_TOKENS = ["BTC", "ETH", "SOL"]


def build_dataset(
    tokens: Iterable[str] = DEFAULT_TOKENS,
    days: int = 365,
    force_refresh: bool = False,
    include_fees: bool = True,
) -> pd.DataFrame:
    """Thu thập và ghép dữ liệu theo (date, token). Trả về bảng **chưa** làm sạch."""
    cg = CoinGeckoCollector()
    llama = DefiLlamaCollector()
    frames = []
    for sym in [t.upper() for t in tokens]:
        print(f"[build] {sym}: CoinGecko ...")
        market = cg.fetch_market_chart(sym, days=days, force_refresh=force_refresh)
        if market.empty:
            print(f"[build] {sym}: không có dữ liệu giá, bỏ qua")
            continue
        market["date"] = pd.to_datetime(market["date"])

        print(f"[build] {sym}: DefiLlama TVL ...")
        tvl = llama.fetch_tvl(sym, force_refresh=force_refresh)
        merged = market.merge(_by_date(tvl, "tvl"), on="date", how="left")

        if include_fees:
            for kind, col in (("dailyFees", "fees_usd"), ("dailyRevenue", "revenue_usd")):
                fees = llama.fetch_fees(sym, data_type=kind, force_refresh=force_refresh)
                merged = merged.merge(_by_date(fees, col), on="date", how="left")
        frames.append(merged)

    if not frames:
        return pd.DataFrame(columns=SCHEMA_COLUMNS + EXTRA_COLUMNS)
    df = pd.concat(frames, ignore_index=True)
    for col in SCHEMA_COLUMNS + EXTRA_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[SCHEMA_COLUMNS + EXTRA_COLUMNS].sort_values(["token", "date"]).reset_index(drop=True)


def _by_date(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if df is None or df.empty or col not in df.columns:
        return pd.DataFrame(columns=["date", col])
    out = df[["date", col]].copy()
    out["date"] = pd.to_datetime(out["date"])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Xây dựng bộ dữ liệu thị trường hợp nhất")
    parser.add_argument("--tokens", nargs="+", default=DEFAULT_TOKENS)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--out", default="data/processed/market_dataset.csv")
    parser.add_argument("--refresh", action="store_true", help="bỏ qua cache, gọi lại API")
    args = parser.parse_args()

    raw = build_dataset(args.tokens, args.days, args.refresh)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    raw.to_csv(out_path.with_name(out_path.stem + "_raw.csv"), index=False)

    clean = DataCleaner.clean_token_dataset(raw)
    clean.to_csv(out_path, index=False)
    print(DataCleaner.quality_report(clean).to_string(index=False))
    print(f"[build] Đã ghi {len(clean)} dòng vào {out_path}")


if __name__ == "__main__":
    main()
