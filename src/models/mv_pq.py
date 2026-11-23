"""
Mô hình định giá theo Phương trình trao đổi MV = PQ (Khanh phụ trách)
M = Cung tiền (Vốn hóa thị trường = P * Supply)
V = Vận tốc luân chuyển = (Annualized Volume) / Market_Cap
P * Q = Tổng giá trị giao dịch kinh tế
P_fair = (P * Q) / (V * Supply)
"""

import pandas as pd
import numpy as np
from src.models.base import ValuationModel


class MVPQValuationModel(ValuationModel):
    def __init__(self, velocity_window: int = 30):
        super().__init__(name="MV_PQ")
        self.velocity_window = velocity_window
        self.estimated_velocity = None

    def fit(self, df: pd.DataFrame) -> "MVPQValuationModel":
        if "volume_24h" in df.columns and "market_cap" in df.columns:
            daily_v = (df["volume_24h"] * 365) / df["market_cap"].replace(0, np.nan)
            self.estimated_velocity = float(daily_v.rolling(self.velocity_window, min_periods=7).median().iloc[-1])
        else:
            self.estimated_velocity = 8.5
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        v = self.estimated_velocity if self.estimated_velocity and self.estimated_velocity > 0 else 8.5
        annual_pq = df.get("volume_24h", pd.Series(1.0, index=df.index)) * 365
        supply = df.get("circulating_supply", pd.Series(1.0, index=df.index)).replace(0, np.nan)
        
        target_m = annual_pq / v
        fair_price = target_m / supply
        return fair_price.fillna(df.get("price_usd", 1.0))
