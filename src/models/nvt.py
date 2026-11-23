"""
================================================================================
MODULE: src/models/nvt.py
TÁC GIẢ: Huỳnh (Trưởng nhóm - Nhánh feature/models)
MỤC ĐÍCH:
  Triển khai mô hình định giá dựa trên:
    1. Tỷ lệ Network Value to Transactions (NVT Ratio) cổ điển (Willy Woo, 2017).
       NVT = Vốn hóa / Giá trị giao dịch On-Chain 24h.
       Mức chuẩn (Benchmark) = Trung vị trượt 90 ngày (90-day Rolling Median).
       Giá hợp lý: P_fair = (NVT_benchmark * Daily_Onchain_Volume) / Circulating_Supply.
    2. Biến thể Luật Metcalfe:
       Giá trị mạng tỷ lệ thuận với bình phương số người dùng / địa chỉ hoạt động:
       Network_Value = alpha * (Active_Addresses)^2
       P_fair_Metcalfe = alpha * (Active_Addresses)^2 / Circulating_Supply.
    3. Chế độ kết hợp (Hybrid/Blended NVT-Metcalfe).
================================================================================
"""

from typing import Optional
import numpy as np
import pandas as pd
from src.models.base import ValuationModel


class NVTValuationModel(ValuationModel):
    """
    Mô hình định giá NVT Ratio kết hợp Luật Metcalfe cho tài sản số.
    """

    def __init__(
        self,
        rolling_window: int = 90,
        metcalfe_weight: float = 0.35,
        default_nvt_benchmark: float = 45.0,
    ):
        """
        Khởi tạo mô hình NVT.

        Args:
            rolling_window (int): Khung thời gian tính trung vị trượt benchmark (mặc định 90 ngày).
            metcalfe_weight (float): Trọng số của thành phần Metcalfe trong chế độ Blended (0.0 đến 1.0).
            default_nvt_benchmark (float): Giá trị benchmark dự phòng nếu chuỗi dữ liệu quá ngắn.
        """
        super().__init__(
            name="NVT_Metcalfe",
            description="Mô hình định giá theo NVT Ratio trượt 90 ngày và Luật Metcalfe",
        )
        self.rolling_window = rolling_window
        self.metcalfe_weight = metcalfe_weight
        self.default_nvt_benchmark = default_nvt_benchmark

        # Các tham số ước lượng sau khi fit
        self.nvt_benchmark: Optional[float] = None
        self.metcalfe_alpha: Optional[float] = None

    def fit(self, df: pd.DataFrame) -> "NVTValuationModel":
        """
        Ước lượng tham số NVT benchmark và hệ số Metcalfe alpha từ dữ liệu lịch sử.

        Args:
            df (pd.DataFrame): DataFrame chứa các cột:
                - 'market_cap' (USD)
                - 'onchain_volume_usd' hoặc 'volume_24h' (USD)
                - 'active_addresses' (Số lượng địa chỉ)
                - 'circulating_supply' (Lượng token lưu hành)
        """
        # 1. Xác định cột khối lượng on-chain
        vol_col = "onchain_volume_usd" if "onchain_volume_usd" in df.columns else "volume_24h"
        required_cols = ["market_cap", vol_col, "circulating_supply"]
        self.validate_input(df, required_cols)

        # 2. Tính toán chuỗi NVT Ratio lịch sử
        safe_volume = df[vol_col].replace(0, np.nan)
        nvt_series = df["market_cap"] / safe_volume

        # Khử ngoại lai bằng rolling median 90 ngày
        rolling_median = nvt_series.rolling(self.rolling_window, min_periods=max(5, self.rolling_window // 4)).median()
        valid_medians = rolling_median.dropna()

        if not valid_medians.empty:
            self.nvt_benchmark = float(valid_medians.iloc[-1])
        else:
            overall_median = nvt_series.median()
            self.nvt_benchmark = float(overall_median) if not np.isnan(overall_median) else self.default_nvt_benchmark

        # 3. Ước lượng hệ số Metcalfe alpha: Market_Cap = alpha * (Active_Addresses)^2
        if "active_addresses" in df.columns:
            valid_rows = df[(df["active_addresses"] > 0) & (df["market_cap"] > 0)]
            if len(valid_rows) >= 5:
                # alpha = median(Market_Cap / Active_Addresses^2)
                alpha_series = valid_rows["market_cap"] / (valid_rows["active_addresses"] ** 2)
                self.metcalfe_alpha = float(alpha_series.median())
            else:
                self.metcalfe_alpha = 1.0
        else:
            self.metcalfe_alpha = None

        # Lưu thông số vào params
        self.params = {
            "nvt_benchmark": round(self.nvt_benchmark, 4),
            "metcalfe_alpha": round(self.metcalfe_alpha, 6) if self.metcalfe_alpha else None,
            "rolling_window": self.rolling_window,
            "metcalfe_weight": self.metcalfe_weight,
        }
        self.is_fitted = True
        return self

    def predict_nvt_only(self, df: pd.DataFrame) -> pd.Series:
        """Dự báo giá chỉ dựa trên tỷ lệ NVT Ratio cổ điển."""
        benchmark = self.nvt_benchmark if self.nvt_benchmark is not None else self.default_nvt_benchmark
        vol_col = "onchain_volume_usd" if "onchain_volume_usd" in df.columns else "volume_24h"
        volume = df[vol_col].replace(0, np.nan)
        supply = df["circulating_supply"].replace(0, np.nan)

        fair_market_cap = volume * benchmark
        fair_price = fair_market_cap / supply
        return fair_price

    def predict_metcalfe_only(self, df: pd.DataFrame) -> pd.Series:
        """Dự báo giá chỉ dựa trên Luật Metcalfe (bình phương active addresses)."""
        if "active_addresses" not in df.columns or self.metcalfe_alpha is None:
            return self.predict_nvt_only(df)

        addresses = df["active_addresses"].replace(0, np.nan)
        supply = df["circulating_supply"].replace(0, np.nan)

        fair_market_cap = self.metcalfe_alpha * (addresses ** 2)
        fair_price = fair_market_cap / supply
        return fair_price

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Dự báo giá trị hợp lý kết hợp Blended giữa NVT Ratio và Luật Metcalfe:
        P_fair = (1 - w_m) * P_NVT + w_m * P_Metcalfe
        """
        p_nvt = self.predict_nvt_only(df)

        if "active_addresses" in df.columns and self.metcalfe_alpha is not None:
            p_metcalfe = self.predict_metcalfe_only(df)
            w = self.metcalfe_weight
            blended = (1.0 - w) * p_nvt + w * p_metcalfe
        else:
            blended = p_nvt

        # Fallback về giá spot nếu có giá trị NaN do thiếu dữ liệu
        if "price_usd" in df.columns:
            return blended.fillna(df["price_usd"])
        return blended.fillna(1.0)
