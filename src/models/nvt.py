"""
Mô hình định giá NVT Ratio & Luật Metcalfe (Huỳnh phụ trách)
NVT = Vốn hóa / Giá trị giao dịch on-chain
Fair Price = (NVT_benchmark * Daily_Onchain_Volume) / Circulating_Supply
"""

import pandas as pd
import numpy as np
from src.models.base import ValuationModel


class NVTValuationModel(ValuationModel):
    def __init__(self, rolling_window: int = 90):
        super().__init__(name="NVT_Metcalfe")
        self.rolling_window = rolling_window
        self.median_nvt = None

    def fit(self, df: pd.DataFrame) -> "NVTValuationModel":
        # Tính toán NVT ratio benchmark từ dữ liệu lịch sử
        if "market_cap" in df.columns and "onchain_volume_usd" in df.columns:
            nvt_series = df["market_cap"] / df["onchain_volume_usd"].replace(0, np.nan)
            self.median_nvt = float(nvt_series.rolling(self.rolling_window, min_periods=7).median().iloc[-1])
        else:
            self.median_nvt = 45.0  # Giá trị benchmark mặc định
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        benchmark = self.median_nvt if self.median_nvt is not None else 45.0
        onchain_vol = df.get("onchain_volume_usd", df.get("volume_24h", pd.Series(1.0, index=df.index)))
        supply = df.get("circulating_supply", pd.Series(1.0, index=df.index)).replace(0, np.nan)
        
        fair_mc = onchain_vol * benchmark
        fair_price = fair_mc / supply
        return fair_price.fillna(df.get("price_usd", 1.0))
