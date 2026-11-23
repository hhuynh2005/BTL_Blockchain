"""
Thu thập dữ liệu Total Value Locked (TVL) và doanh thu giao thức từ DefiLlama (Khanh phụ trách)
"""

import requests
import pandas as pd
from pathlib import Path


class DefiLlamaCollector:
    BASE_URL = "https://api.llama.fi"

    def __init__(self, cache_dir: str = "data/raw/defillama"):
        self.cache_dir = Path(cache_dir)
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    def fetch_protocol_tvl(self, protocol_slug: str) -> pd.DataFrame:
        """
        Lấy chuỗi lịch sử TVL của giao thức theo ngày.
        """
        cache_file = self.cache_dir / f"{protocol_slug}_tvl.csv"
        if cache_file.exists():
            return pd.read_csv(cache_file, parse_dates=["date"])

        url = f"{self.BASE_URL}/protocol/{protocol_slug}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                tvl_list = data.get("tvl", [])
                records = []
                for item in tvl_list:
                    date_str = pd.to_datetime(item["date"], unit="s").strftime("%Y-%m-%d")
                    records.append({"date": date_str, "tvl": item["totalLiquidityUSD"]})
                df = pd.DataFrame(records)
                df.to_csv(cache_file, index=False)
                return df
        except Exception as e:
            print(f"[DefiLlama] Error fetching {protocol_slug}: {e}")

        return pd.DataFrame(columns=["date", "tvl"])
