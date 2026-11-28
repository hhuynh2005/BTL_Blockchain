"""
Thu thập TVL và phí / doanh thu giao thức từ DefiLlama (Khanh phụ trách).

- Token của giao thức DeFi (UNI, AAVE, ...): TVL lấy từ ``/protocol/{slug}``.
- Token của blockchain lớp 1/lớp 2 (BTC, ETH, SOL, ARB): TVL của cả chuỗi lấy từ
  ``/v2/historicalChainTvl/{chain}``.
- Phí (fees) và doanh thu (revenue) theo ngày lấy từ ``/summary/fees/{slug}``,
  là đầu vào cho mô hình định giá theo dòng thu nhập (Mục 2.5).

Mọi kết quả được cache CSV tại ``data/raw/defillama/`` và có thử lại khi lỗi mạng.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import pandas as pd
import requests


class DefiLlamaCollector:
    BASE_URL = "https://api.llama.fi"

    # Token giao thức -> slug giao thức trên DefiLlama
    PROTOCOL_SLUG_MAP = {
        "UNI": "uniswap",
        "AAVE": "aave",
        "CRV": "curve-dex",
        "BAL": "balancer-v2",
        "COMP": "compound-finance",
        "MKR": "makerdao",
        "LDO": "lido",
        "SUSHI": "sushiswap",
        "SNX": "synthetix",
        "LINK": "chainlink",
        "GRT": "the-graph",
    }

    # Token gốc của blockchain -> tên chain trên DefiLlama (TVL & phí ở cấp chuỗi)
    CHAIN_MAP = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "SOL": "Solana",
        "ARB": "Arbitrum",
    }

    MAX_RETRIES = 3
    TIMEOUT_SEC = 20

    def __init__(self, cache_dir: str = "data/raw/defillama", cache_ttl_hours: float = 12.0):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl_sec = cache_ttl_hours * 3600
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "token-valuation-tool/1.0"})

    # ------------------------------------------------------------------ helpers
    def get_slug(self, symbol: str) -> str:
        """Token symbol -> slug giao thức (hoặc chuyển chữ thường nếu chưa có trong bảng)."""
        return self.PROTOCOL_SLUG_MAP.get(symbol.upper(), symbol.lower())

    def is_chain_token(self, symbol: str) -> bool:
        return symbol.upper() in self.CHAIN_MAP

    def _cache_is_fresh(self, path: Path) -> bool:
        return path.exists() and (time.time() - path.stat().st_mtime) < self.cache_ttl_sec

    def _get(self, path: str, params: Optional[dict] = None):
        url = f"{self.BASE_URL}{path}"
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.TIMEOUT_SEC)
            except requests.RequestException as exc:
                print(f"[DefiLlama] Lỗi kết nối ({exc}); thử lại {attempt + 1}/{self.MAX_RETRIES}")
                time.sleep(2 ** attempt)
                continue
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                time.sleep(2 ** (attempt + 1))
                continue
            print(f"[DefiLlama] HTTP {resp.status_code} tại {path}")
            return None
        return None

    @staticmethod
    def _to_daily(records: list, ts_key: str, val_key: str, symbol: str, col: str) -> pd.DataFrame:
        """Chuẩn hóa danh sách {timestamp, value} thành bảng theo ngày UTC, mỗi ngày một dòng."""
        if not records:
            return pd.DataFrame(columns=["date", "token", col])
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df[ts_key].astype("int64"), unit="s", utc=True).dt.floor("D").dt.tz_localize(None)
        df[col] = pd.to_numeric(df[val_key], errors="coerce")
        # Điểm cuối thường là thời điểm hiện tại -> trùng ngày, giữ giá trị mới nhất
        df = df.sort_values("date").groupby("date", as_index=False)[col].last()
        df["token"] = symbol.upper()
        return df[["date", "token", col]]

    def _cached(self, cache_file: Path, force_refresh: bool, loader) -> pd.DataFrame:
        if not force_refresh and self._cache_is_fresh(cache_file):
            return pd.read_csv(cache_file, parse_dates=["date"])
        df = loader()
        if df is None or df.empty:
            if cache_file.exists():
                print(f"[DefiLlama] Dùng cache cũ {cache_file.name}")
                return pd.read_csv(cache_file, parse_dates=["date"])
            return df
        df.to_csv(cache_file, index=False)
        return df

    # ------------------------------------------------------------------ TVL
    def fetch_protocol_tvl(self, symbol: str, force_refresh: bool = False) -> pd.DataFrame:
        """Chuỗi TVL theo ngày của giao thức DeFi (tổng mọi chain)."""
        slug = self.get_slug(symbol)

        def load():
            data = self._get(f"/protocol/{slug}")
            records = (data or {}).get("tvl") or []
            return self._to_daily(records, "date", "totalLiquidityUSD", symbol, "tvl")

        return self._cached(self.cache_dir / f"{slug}_tvl.csv", force_refresh, load)

    def fetch_chain_tvl(self, symbol: str, force_refresh: bool = False) -> pd.DataFrame:
        """Chuỗi TVL theo ngày của cả blockchain (BTC, ETH, SOL, ARB)."""
        chain = self.CHAIN_MAP.get(symbol.upper(), symbol)

        def load():
            data = self._get(f"/v2/historicalChainTvl/{chain}")
            return self._to_daily(data or [], "date", "tvl", symbol, "tvl")

        return self._cached(self.cache_dir / f"chain_{chain.lower()}_tvl.csv", force_refresh, load)

    def fetch_tvl(self, symbol: str, force_refresh: bool = False) -> pd.DataFrame:
        """Tự chọn TVL cấp chuỗi hay cấp giao thức theo loại token."""
        if self.is_chain_token(symbol):
            return self.fetch_chain_tvl(symbol, force_refresh)
        return self.fetch_protocol_tvl(symbol, force_refresh)

    # ------------------------------------------------------------------ Fees / Revenue
    def fetch_fees(self, symbol: str, data_type: str = "dailyFees", force_refresh: bool = False) -> pd.DataFrame:
        """
        Phí (``dailyFees``) hoặc doanh thu giao thức (``dailyRevenue``) theo ngày, tính bằng USD.
        Với token chuỗi (BTC/ETH/SOL) đây là tổng phí giao dịch người dùng trả cho mạng.
        """
        if data_type not in ("dailyFees", "dailyRevenue"):
            raise ValueError("data_type phải là 'dailyFees' hoặc 'dailyRevenue'")
        col = "fees_usd" if data_type == "dailyFees" else "revenue_usd"
        slug = self.CHAIN_MAP[symbol.upper()].lower() if self.is_chain_token(symbol) else self.get_slug(symbol)

        def load():
            data = self._get(
                f"/summary/fees/{slug}",
                {"dataType": data_type, "excludeTotalDataChartBreakdown": "true"},
            )
            chart = (data or {}).get("totalDataChart") or []
            records = [{"ts": p[0], "v": p[1]} for p in chart]
            return self._to_daily(records, "ts", "v", symbol, col)

        return self._cached(self.cache_dir / f"{slug}_{col}.csv", force_refresh, load)
