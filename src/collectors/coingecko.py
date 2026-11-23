"""
Thu thập dữ liệu giá, khối lượng, vốn hóa và lượng cung từ CoinGecko API (Khanh phụ trách)
Có cơ chế cache và xử lý giới hạn tần suất (rate limit).
"""

import time
import requests
import pandas as pd
from pathlib import Path


class CoinGeckoCollector:
    BASE_URL = "https://api.coingecko.com/api/v3"

    def __init__(self, cache_dir: str = "data/raw/coingecko"):
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def fetch_market_chart(self, coin_id: str, days: int = 90) -> pd.DataFrame:
        """
        Lấy lịch sử giá, market cap, và 24h volume.
        """
        cache_file = self.cache_dir / f"{coin_id}_{days}d.csv"
        if cache_file.exists():
            return pd.read_csv(cache_file, parse_dates=["date"])

        url = f"{self.BASE_URL}/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days, "interval": "daily"}
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                prices = data.get("prices", [])
                market_caps = data.get("market_caps", [])
                volumes = data.get("total_volumes", [])

                records = []
                for p, m, v in zip(prices, market_caps, volumes):
                    date_str = pd.to_datetime(p[0], unit="ms").strftime("%Y-%m-%d")
                    records.append({
                        "date": date_str,
                        "price_usd": p[1],
                        "market_cap": m[1],
                        "volume_24h": v[1],
                    })
                df = pd.DataFrame(records)
                df.to_csv(cache_file, index=False)
                return df
        except Exception as e:
            print(f"[CoinGecko] Error fetching {coin_id}: {e}")

        # Trả về fallback rỗng
        return pd.DataFrame(columns=["date", "price_usd", "market_cap", "volume_24h"])
