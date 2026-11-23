"""
Kỹ nghệ đặc trưng (Feature Engineering): biến động giá, moving average, velocity, nvt_ratio (Khanh phụ trách)
"""

import pandas as pd
import numpy as np


class FeatureEngineer:
    @staticmethod
    def generate_features(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        if "price_usd" in df.columns:
            # Lợi suất log và độ biến động 7 ngày, 30 ngày
            df["returns"] = np.log(df["price_usd"] / df["price_usd"].shift(1))
            df["volatility_7d"] = df["returns"].rolling(7).std() * np.sqrt(365)
            df["volatility_30d"] = df["returns"].rolling(30).std() * np.sqrt(365)

            # Đường trung bình động MA
            df["ma_7"] = df["price_usd"].rolling(7).mean()
            df["ma_30"] = df["price_usd"].rolling(30).mean()

        # Tốc độ vòng quay của token (velocity)
        if "volume_24h" in df.columns and "market_cap" in df.columns:
            df["velocity"] = (df["volume_24h"] * 365) / df["market_cap"].replace(0, np.nan)

        # NVT Ratio
        if "market_cap" in df.columns and "onchain_volume_usd" in df.columns:
            df["nvt_ratio"] = df["market_cap"] / df["onchain_volume_usd"].replace(0, np.nan)

        return df
