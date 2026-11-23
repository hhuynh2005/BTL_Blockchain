"""
Giao diện cơ sở cho mọi mô hình định giá token (Huỳnh phụ trách)
Mọi mô hình định giá cần kế thừa lớp ValuationModel và triển khai:
  - fit(df: pd.DataFrame)
  - predict(df: pd.DataFrame) -> pd.Series
"""

from abc import ABC, abstractmethod
import pandas as pd


class ValuationModel(ABC):
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False

    @abstractmethod
    def fit(self, df: pd.DataFrame) -> "ValuationModel":
        """
        Huấn luyện hoặc ước lượng tham số mô hình trên tập dữ liệu lịch sử.
        """
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Dự báo giá trị hợp lý (Fair Value theo USD) cho từng dòng trong dữ liệu.
        Trả về: pd.Series chứa giá định giá (USD).
        """
        pass

    def __repr__(self) -> str:
        return f"<ValuationModel: {self.name}>"
