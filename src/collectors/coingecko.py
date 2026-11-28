"""
Thu thập giá, khối lượng giao dịch, vốn hóa và cung lưu hành từ CoinGecko API (Khanh phụ trách).

Đặc điểm:
- Cache CSV theo từng token tại ``data/raw/coingecko/`` (có thời hạn, mặc định 12 giờ).
- Xử lý giới hạn tần suất: chờ tối thiểu giữa hai lần gọi, tự thử lại với
  exponential backoff khi gặp HTTP 429 / 5xx (tôn trọng header ``Retry-After``).
- Hỗ trợ khóa Demo API miễn phí qua biến môi trường ``COINGECKO_API_KEY``.
- Chuẩn hóa mốc thời gian về ngày UTC, mỗi ngày một dòng (bỏ điểm "hiện tại"
  không tròn ngày mà CoinGecko luôn trả về ở cuối chuỗi).
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd
import requests

OUTPUT_COLUMNS = ["date", "token", "price_usd", "market_cap", "volume_24h", "circulating_supply"]


class CoinGeckoCollector:
    BASE_URL = "https://api.coingecko.com/api/v3"

    # Ánh xạ ký hiệu token -> coin_id của CoinGecko
    COIN_ID_MAP = {
        # Phạm vi thử nghiệm chính (bản nháp báo cáo): BTC, ETH, SOL
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        # 12 token ERC-20 trong config/tokens.yaml
        "UNI": "uniswap",
        "CRV": "curve-dao-token",
        "SUSHI": "sushi",
        "BAL": "balancer",
        "AAVE": "aave",
        "COMP": "compound-governance-token",
        "MKR": "maker",
        "LINK": "chainlink",
        "GRT": "the-graph",
        "LDO": "lido-dao",
        "SNX": "havven",
        "ARB": "arbitrum",
    }

    MIN_INTERVAL_SEC = 2.5   # Gói miễn phí ~30 lượt/phút -> giãn cách an toàn
    MAX_RETRIES = 4
    TIMEOUT_SEC = 15
    MAX_FREE_DAYS = 365      # Gói Public/Demo chỉ cho lịch sử tối đa 365 ngày

    def __init__(
        self,
        cache_dir: str = "data/raw/coingecko",
        api_key: Optional[str] = None,
        cache_ttl_hours: float = 12.0,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = api_key or os.getenv("COINGECKO_API_KEY") or None
        self.cache_ttl_sec = cache_ttl_hours * 3600
        self._last_call = 0.0
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "token-valuation-tool/1.0"})
        if self.api_key:
            self.session.headers["x-cg-demo-api-key"] = self.api_key

    # ------------------------------------------------------------------ helpers
    def get_coin_id(self, symbol: str) -> str:
        """Chuyển token symbol (vd ``SOL``) sang coin_id CoinGecko (``solana``)."""
        return self.COIN_ID_MAP.get(symbol.upper(), symbol.lower())

    def _symbol_of(self, symbol_or_id: str) -> str:
        """Trả về ký hiệu token chuẩn, kể cả khi người dùng truyền coin_id."""
        up = symbol_or_id.upper()
        if up in self.COIN_ID_MAP:
            return up
        for sym, cid in self.COIN_ID_MAP.items():
            if cid == symbol_or_id.lower():
                return sym
        return up

    def _cache_is_fresh(self, path: Path) -> bool:
        return path.exists() and (time.time() - path.stat().st_mtime) < self.cache_ttl_sec

    def _throttle(self) -> None:
        wait = self.MIN_INTERVAL_SEC - (time.time() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.time()

    def _get(self, path: str, params: dict) -> Optional[dict]:
        """GET có giãn cách và thử lại khi bị giới hạn tần suất hoặc lỗi máy chủ."""
        url = f"{self.BASE_URL}{path}"
        for attempt in range(self.MAX_RETRIES + 1):
            self._throttle()
            try:
                resp = self.session.get(url, params=params, timeout=self.TIMEOUT_SEC)
            except requests.RequestException as exc:
                print(f"[CoinGecko] Lỗi kết nối ({exc}); thử lại lần {attempt + 1}/{self.MAX_RETRIES}")
                time.sleep(2 ** attempt)
                continue

            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429 or resp.status_code >= 500:
                retry_after = resp.headers.get("Retry-After")
                wait = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** (attempt + 2)
                print(f"[CoinGecko] HTTP {resp.status_code}; chờ {wait:.0f}s rồi thử lại ({attempt + 1}/{self.MAX_RETRIES})")
                time.sleep(wait)
                continue
            print(f"[CoinGecko] HTTP {resp.status_code} tại {path}: {resp.text[:200]}")
            return None
        print(f"[CoinGecko] Hết số lần thử lại cho {path}")
        return None

    # ------------------------------------------------------------------ parsing
    @staticmethod
    def parse_market_chart(data: dict, symbol: str) -> pd.DataFrame:
        """Chuyển JSON ``/market_chart`` thành bảng theo ngày UTC (đúng tên cột SCHEMA.md)."""
        frames = []
        for key, col in (("prices", "price_usd"), ("market_caps", "market_cap"), ("total_volumes", "volume_24h")):
            arr = data.get(key) or []
            s = pd.DataFrame(arr, columns=["ts", col])
            s["ts"] = pd.to_datetime(s["ts"], unit="ms", utc=True)
            frames.append(s.set_index("ts"))
        if not frames or frames[0].empty:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)

        df = pd.concat(frames, axis=1).sort_index()
        # Chỉ giữ các điểm tròn ngày (00:00 UTC); điểm cuối là thời điểm hiện tại
        # nên trùng ngày với điểm 00:00 của hôm nay -> giữ điểm 00:00.
        df["date"] = df.index.floor("D").tz_localize(None)
        df = df.groupby("date", as_index=False).first()

        price = df["price_usd"].astype(float)
        df["circulating_supply"] = (df["market_cap"].astype(float) / price.where(price > 0)).round(2)
        df["token"] = symbol
        return df[OUTPUT_COLUMNS].reset_index(drop=True)

    # ------------------------------------------------------------------ public API
    def fetch_market_chart(self, symbol: str, days: int = 365, force_refresh: bool = False) -> pd.DataFrame:
        """
        Lấy lịch sử ``price_usd``, ``market_cap``, ``volume_24h`` và ``circulating_supply``
        (= market_cap / price) theo ngày của một token.

        Tham số ``symbol`` nhận ký hiệu (``SOL``) hoặc coin_id (``solana``).
        Trả về DataFrame rỗng đúng cột nếu không lấy được dữ liệu.
        """
        days = int(min(days, self.MAX_FREE_DAYS)) if not self.api_key else int(days)
        coin_id = self.get_coin_id(symbol)
        sym = self._symbol_of(symbol)
        cache_file = self.cache_dir / f"{coin_id}_{days}d.csv"

        if not force_refresh and self._cache_is_fresh(cache_file):
            return pd.read_csv(cache_file, parse_dates=["date"])

        data = self._get(f"/coins/{coin_id}/market_chart", {"vs_currency": "usd", "days": days, "interval": "daily"})
        if data is None:
            if cache_file.exists():  # API lỗi -> dùng bản cache cũ còn hơn không có gì
                print(f"[CoinGecko] Dùng cache cũ cho {coin_id}")
                return pd.read_csv(cache_file, parse_dates=["date"])
            return pd.DataFrame(columns=OUTPUT_COLUMNS)

        df = self.parse_market_chart(data, sym)
        if not df.empty:
            df.to_csv(cache_file, index=False)
        return df

    def fetch_many(self, symbols: Iterable[str], days: int = 365, force_refresh: bool = False) -> pd.DataFrame:
        """Lấy dữ liệu cho nhiều token (tuần tự, có giãn cách) và gộp thành một bảng."""
        frames = [self.fetch_market_chart(s, days=days, force_refresh=force_refresh) for s in symbols]
        frames = [f for f in frames if not f.empty]
        if not frames:
            return pd.DataFrame(columns=OUTPUT_COLUMNS)
        return pd.concat(frames, ignore_index=True)
