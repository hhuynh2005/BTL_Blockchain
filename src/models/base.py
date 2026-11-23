"""
================================================================================
MODULE: src/models/base.py
TÁC GIẢ: Huỳnh (Trưởng nhóm - Nhánh feature/models)
MỤC ĐÍCH:
  Định nghĩa Lớp cơ sở trừu tượng (Abstract Base Class - ABC) `ValuationModel`.
  Mọi mô hình định giá token trong hệ thống (NVT, MV=PQ, TWAP, Comparable, Ensemble)
  bắt buộc phải kế thừa lớp này và triển khai hai phương thức cốt lõi:
    1. fit(self, df: pd.DataFrame) -> "ValuationModel"
    2. predict(self, df: pd.DataFrame) -> pd.Series
================================================================================
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json
from pathlib import Path
import numpy as np
import pandas as pd


class ValuationModel(ABC):
    """
    Giao diện cơ sở cho tất cả các mô hình định giá tài sản số.
    
    Quy ước thiết kế:
      - fit(df): Khớp hoặc hiệu chỉnh các tham số kinh tế lượng trên dữ liệu lịch sử.
      - predict(df): Trả về một pd.Series chứa các giá trị định giá hợp lý (USD).
      - evaluate(df): Đánh giá sai số MAE, RMSE, MAPE so với giá thị trường thực tế.
    """

    def __init__(self, name: str, description: str = ""):
        self.name: str = name
        self.description: str = description
        self.is_fitted: bool = False
        self.params: Dict[str, float] = {}

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "ValuationModel":
        """
        Huấn luyện hoặc ước lượng tham số mô hình trên tập dữ liệu lịch sử.
        
        Args:
            df (pd.DataFrame): Bảng dữ liệu chuỗi thời gian tuân theo data/SCHEMA.md.
            
        Returns:
            ValuationModel: Trả về chính đối tượng (self) sau khi đã khớp tham số.
        """
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Dự báo giá trị hợp lý (Fair Value theo USD) cho từng dòng trong dữ liệu.
        
        Args:
            df (pd.DataFrame): Bảng dữ liệu đầu vào.
            
        Returns:
            pd.Series: Chuỗi giá định giá hợp lý tính bằng USD, cùng chỉ số index với df.
        """
        pass

    def validate_input(self, df: pd.DataFrame, required_columns: List[str]) -> None:
        """
        Kiểm tra tính đầy đủ của các trường dữ liệu theo Schema trước khi tính toán.
        
        Args:
            df (pd.DataFrame): DataFrame cần kiểm tra.
            required_columns (List[str]): Danh sách tên cột bắt buộc phải có.
            
        Raises:
            ValueError: Nếu thiếu một hoặc nhiều cột bắt buộc.
        """
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(
                f"[{self.name}] Dữ liệu đầu vào thiếu các cột bắt buộc: {missing}. "
                f"Vui lòng kiểm tra lại data/SCHEMA.md."
            )

    def evaluate(self, df: pd.DataFrame, target_col: str = "price_usd") -> Dict[str, float]:
        """
        Đánh giá độ chính xác của mô hình so với giá thị trường mục tiêu.
        
        Args:
            df (pd.DataFrame): DataFrame chứa dữ liệu kiểm thử.
            target_col (str): Tên cột chứa giá thị trường đối sánh (mặc định 'price_usd').
            
        Returns:
            Dict[str, float]: Từ điển chứa các chỉ số sai số MAE, RMSE, MAPE (%).
        """
        if target_col not in df.columns:
            raise ValueError(f"Không tìm thấy cột mục tiêu '{target_col}' trong DataFrame.")

        y_true = df[target_col].replace(0, np.nan).dropna()
        y_pred = self.predict(df).loc[y_true.index]

        # Khử các giá trị NaN phát sinh
        valid_mask = ~(y_true.isna() | y_pred.isna())
        y_t = y_true[valid_mask].to_numpy()
        y_p = y_pred[valid_mask].to_numpy()

        if len(y_t) == 0:
            return {"MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan}

        mae = float(np.mean(np.abs(y_p - y_t)))
        rmse = float(np.sqrt(np.mean((y_p - y_t) ** 2)))
        mape = float(np.mean(np.abs((y_t - y_p) / y_t)) * 100.0)

        return {
            "MAE": round(mae, 4),
            "RMSE": round(rmse, 4),
            "MAPE": round(mape, 2),
        }

    def save_params(self, filepath: str) -> None:
        """Lưu các tham số đã fit của mô hình ra tệp JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "model_name": self.name,
            "is_fitted": self.is_fitted,
            "params": self.params,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_params(self, filepath: str) -> "ValuationModel":
        """Tải các tham số mô hình từ tệp JSON đã lưu."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy tệp tham số tại: {filepath}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.name = data.get("model_name", self.name)
        self.is_fitted = data.get("is_fitted", False)
        self.params = data.get("params", {})
        return self

    def __repr__(self) -> str:
        status = "Fitted" if self.is_fitted else "Unfitted"
        return f"<ValuationModel: {self.name} [{status}] params={self.params}>"
