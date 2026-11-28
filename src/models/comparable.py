"""
Mô hình định giá so sánh tương đối theo ngành (Comparable Analysis) (Nam Khánh phụ trách)
Sử dụng bội số Market Cap / TVL (MC/TVL Multiple) so với trung vị ngành.

    P_fair = (Median_Sector_MC_TVL * TVL_target) / Supply_target

- Nếu dữ liệu có cột `sector`, bội số trung vị được ước lượng riêng cho từng ngành
  (DEX, Lending, Liquid Staking, ...). Ngành chưa thấy khi fit sẽ dùng trung vị toàn cục.
- Các bội số ngoại lai (ngoài khoảng phân vị [q_low, q_high]) bị loại trước khi lấy trung vị
  để tránh token có TVL gần 0 làm méo benchmark.
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.models.base import ValuationModel


class ComparableValuationModel(ValuationModel):
    def __init__(
        self,
        sector_benchmark_mc_tvl: float = 1.25,
        sector_col: str = "sector",
        quantile_clip: tuple = (0.05, 0.95),
        min_tvl: float = 0.0,
    ):
        super().__init__(name="Comparable_MCTVL")
        self.sector_benchmark_mc_tvl = float(sector_benchmark_mc_tvl)
        self.sector_col = sector_col
        self.quantile_clip = quantile_clip
        self.min_tvl = min_tvl
        self.sector_benchmarks: Dict[str, float] = {}

    # ------------------------------------------------------------------ #
    @staticmethod
    def compute_mc_tvl(df: pd.DataFrame) -> pd.Series:
        """Bội số MC/TVL cho từng dòng (NaN nếu TVL <= 0 hoặc thiếu dữ liệu)."""
        if "market_cap" not in df.columns or "tvl" not in df.columns:
            return pd.Series(np.nan, index=df.index, dtype=float)
        mc = pd.to_numeric(df["market_cap"], errors="coerce")
        tvl = pd.to_numeric(df["tvl"], errors="coerce").where(lambda s: s > 0)
        return (mc / tvl).replace([np.inf, -np.inf], np.nan)

    def _robust_median(self, ratios: pd.Series) -> Optional[float]:
        valid = ratios.dropna()
        valid = valid[valid > 0]
        if valid.empty:
            return None
        lo, hi = self.quantile_clip
        if len(valid) >= 5:
            valid = valid[(valid >= valid.quantile(lo)) & (valid <= valid.quantile(hi))]
        return float(valid.median())

    # ------------------------------------------------------------------ #
    def fit(self, df: pd.DataFrame) -> "ComparableValuationModel":
        ratios = self.compute_mc_tvl(df)
        if "tvl" in df.columns and self.min_tvl > 0:
            ratios = ratios.where(pd.to_numeric(df["tvl"], errors="coerce") >= self.min_tvl)

        global_median = self._robust_median(ratios)
        if global_median is not None:
            self.sector_benchmark_mc_tvl = global_median

        self.sector_benchmarks = {}
        if self.sector_col in df.columns:
            for sector, idx in df.groupby(self.sector_col).groups.items():
                med = self._robust_median(ratios.loc[idx])
                if med is not None:
                    self.sector_benchmarks[str(sector)] = med

        self.is_fitted = True
        return self

    def benchmark_for(self, df: pd.DataFrame) -> pd.Series:
        """Bội số benchmark áp dụng cho từng dòng (theo ngành nếu có)."""
        base = pd.Series(self.sector_benchmark_mc_tvl, index=df.index, dtype=float)
        if self.sector_benchmarks and self.sector_col in df.columns:
            mapped = df[self.sector_col].astype(str).map(self.sector_benchmarks)
            base = mapped.fillna(base).astype(float)
        return base

    def predict(self, df: pd.DataFrame) -> pd.Series:
        tvl = pd.to_numeric(df["tvl"], errors="coerce") if "tvl" in df.columns else pd.Series(np.nan, index=df.index)
        if "circulating_supply" in df.columns:
            supply = pd.to_numeric(df["circulating_supply"], errors="coerce").where(lambda s: s > 0)
        else:
            supply = pd.Series(np.nan, index=df.index)

        fair_price = (tvl * self.benchmark_for(df)) / supply
        fallback = df["price_usd"] if "price_usd" in df.columns else 1.0
        return fair_price.astype(float).fillna(fallback).rename(self.name)

    def relative_valuation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Bảng so sánh tương đối: bội số hiện tại vs benchmark ngành và % chênh lệch
        (dương = token đang rẻ hơn ngành / undervalued).
        """
        out = pd.DataFrame(index=df.index)
        for col in ("token", self.sector_col):
            if col in df.columns:
                out[col] = df[col]
        out["mc_tvl"] = self.compute_mc_tvl(df)
        out["benchmark_mc_tvl"] = self.benchmark_for(df)
        out["fair_price"] = self.predict(df)
        if "price_usd" in df.columns:
            out["price_usd"] = df["price_usd"]
            out["upside_%"] = (out["fair_price"] / df["price_usd"] - 1.0) * 100
        return out
