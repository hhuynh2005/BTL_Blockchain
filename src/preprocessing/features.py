"""
Kỹ nghệ đặc trưng (Feature Engineering) cho mô hình định giá (Khanh phụ trách).

Các đặc trưng sinh ra (tính riêng cho từng token, chỉ dùng dữ liệu quá khứ):
  1. ``returns``                  : lợi suất log ngày  ln(P_t / P_{t-1})
  2. ``volatility_7d / _30d``     : độ biến động lịch sử quy năm  std(returns)·√365
  3. ``ma_7 / ma_14 / ma_30``     : trung bình động giá
  4. ``velocity``                 : vận tốc luân chuyển quy năm  V = Volume_24h·365 / MarketCap
                                    (dùng trực tiếp cho phương trình MV = PQ, Mục 2.3)
  5. ``turnover_24h``             : tỷ lệ quay vòng ngày  Volume_24h / MarketCap
  6. ``nvt_ratio``                : MarketCap / On-chain Volume (fallback Volume_24h nếu thiếu on-chain)
  7. ``mc_tvl_ratio``             : MarketCap / TVL
  8. ``liquidity_score``          : mức độ tin cậy theo thanh khoản ∈ [0, 1] (Mục 2.7)

Ghi chú: SCHEMA.md đang định nghĩa ``velocity`` = On-chain Volume / Market Cap (không quy năm)
trong khi ``sample_tokens.csv`` dùng Volume_24h·365 / Market Cap. Module này theo cách của dữ liệu
mẫu (quy năm) vì MV = PQ cần V theo năm; đề nghị cập nhật lại SCHEMA.md cho thống nhất.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ANNUALIZATION = 365.0  # thị trường crypto giao dịch 365 ngày/năm


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    return a.astype(float) / b.astype(float).where(b.astype(float) > 0)


class FeatureEngineer:
    @staticmethod
    def _features_single(df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        if "date" in out.columns:
            out = out.sort_values("date").reset_index(drop=True)

        if "price_usd" in out.columns:
            prices = out["price_usd"].astype(float)
            out["returns"] = np.log(prices / prices.shift(1))
            out["volatility_7d"] = out["returns"].rolling(7, min_periods=3).std() * np.sqrt(ANNUALIZATION)
            out["volatility_30d"] = out["returns"].rolling(30, min_periods=7).std() * np.sqrt(ANNUALIZATION)
            for w in (7, 14, 30):
                out[f"ma_{w}"] = prices.rolling(w, min_periods=1).mean()

        if {"volume_24h", "market_cap"}.issubset(out.columns):
            out["turnover_24h"] = _safe_div(out["volume_24h"], out["market_cap"])
            out["velocity"] = out["turnover_24h"] * ANNUALIZATION

        if "market_cap" in out.columns:
            tx_vol = None
            if "onchain_volume_usd" in out.columns and out["onchain_volume_usd"].notna().any():
                tx_vol = out["onchain_volume_usd"]
            elif "volume_24h" in out.columns:
                tx_vol = out["volume_24h"]
            if tx_vol is not None:
                out["nvt_ratio"] = _safe_div(out["market_cap"], tx_vol)

        if {"market_cap", "tvl"}.issubset(out.columns):
            out["mc_tvl_ratio"] = _safe_div(out["market_cap"], out["tvl"])

        if "volume_24h" in out.columns:
            out["liquidity_score"] = FeatureEngineer.liquidity_score(out["volume_24h"])

        return out

    @staticmethod
    def liquidity_score(volume_usd: pd.Series, low: float = 1e6, high: float = 1e9) -> pd.Series:
        """
        Điểm tin cậy theo thanh khoản: nội suy log tuyến tính khối lượng 24h trong
        [``low``, ``high``] USD về [0, 1]. Token có volume < 1 triệu USD/ngày -> 0
        (dễ bị thao túng), > 1 tỷ USD/ngày -> 1.
        """
        v = volume_usd.astype(float).where(volume_usd > 0)
        score = (np.log10(v) - np.log10(low)) / (np.log10(high) - np.log10(low))
        return score.clip(0.0, 1.0)

    @staticmethod
    def generate_features(df: pd.DataFrame, token_col: str = "token") -> pd.DataFrame:
        """
        Sinh đặc trưng cho bảng một hoặc nhiều token. Khi có cột ``token``, mọi phép
        tính trượt (rolling/shift) được thực hiện riêng trong từng token để không
        lẫn dữ liệu giữa các token.
        """
        if df.empty:
            return df.copy()
        if token_col not in df.columns or df[token_col].nunique() <= 1:
            return FeatureEngineer._features_single(df)
        parts = [FeatureEngineer._features_single(g) for _, g in df.groupby(token_col, sort=True)]
        return pd.concat(parts, ignore_index=True)
