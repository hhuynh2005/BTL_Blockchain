"""
Mô hình định giá Time-Weighted Average Price (TWAP) từ sàn AMM Uniswap (Kha phụ trách)
TWAP làm mịn các biến động tức thời, chống thao túng oracle và tấn công Flash Loan.
"""

import pandas as pd
from src.models.base import ValuationModel


class TWAPValuationModel(ValuationModel):
    def __init__(self, window: int = 7):
        super().__init__(name="Uniswap_TWAP")
        self.window = window

    def fit(self, df: pd.DataFrame) -> "TWAPValuationModel":
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        # Nếu có reserve từ Uniswap pool: P = reserve1 / reserve0
        if "pool_reserve0" in df.columns and "pool_reserve1" in df.columns:
            spot_amm = df["pool_reserve1"] / df["pool_reserve0"].replace(0, pd.NA)
            twap_series = spot_amm.rolling(self.window, min_periods=1).mean()
            return twap_series.fillna(df.get("price_usd", 1.0))
        elif "price_usd" in df.columns:
            return df["price_usd"].rolling(self.window, min_periods=1).mean()
        else:
            return pd.Series(1.0, index=df.index)
