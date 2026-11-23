"""
Mô hình định giá so sánh tương đối theo ngành (Comparable Analysis) (Nam Khánh phụ trách)
Sử dụng bội số Market Cap / TVL (MC/TVL Multiple) so với trung vị ngành.
P_fair = (Median_Sector_MC_TVL * TVL_target) / Supply_target
"""

import pandas as pd
from src.models.base import ValuationModel


class ComparableValuationModel(ValuationModel):
    def __init__(self, sector_benchmark_mc_tvl: float = 1.25):
        super().__init__(name="Comparable_MCTVL")
        self.sector_benchmark_mc_tvl = sector_benchmark_mc_tvl

    def fit(self, df: pd.DataFrame) -> "ComparableValuationModel":
        if "market_cap" in df.columns and "tvl" in df.columns:
            ratios = df["market_cap"] / df["tvl"].replace(0, pd.NA)
            valid = ratios.dropna()
            if not valid.empty:
                self.sector_benchmark_mc_tvl = float(valid.median())
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        benchmark = self.sector_benchmark_mc_tvl
        tvl = df.get("tvl", pd.Series(1.0, index=df.index))
        supply = df.get("circulating_supply", pd.Series(1.0, index=df.index)).replace(0, pd.NA)
        
        target_mc = tvl * benchmark
        fair_price = target_mc / supply
        return fair_price.fillna(df.get("price_usd", 1.0))
