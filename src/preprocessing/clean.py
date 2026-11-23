"""
Làm sạch dữ liệu, xử lý giá trị thiếu (missing values), lọc ngoại lai và đồng bộ mốc thời gian (Khanh phụ trách)
"""

import pandas as pd
import numpy as np


class DataCleaner:
    @staticmethod
    def clean_timeseries(df: pd.DataFrame) -> pd.DataFrame:
        """
        Đồng bộ chuỗi thời gian, điền giá trị thiếu bằng forward-fill, loại bỏ dòng trùng lặp.
        """
        df = df.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").drop_duplicates(subset=["date"])
            df = df.set_index("date").asfreq("D")
            df = df.ffill().bfill().reset_index()
        return df

    @staticmethod
    def remove_outliers_iqr(df: pd.DataFrame, column: str, multiplier: float = 3.0) -> pd.DataFrame:
        """
        Lọc bỏ hoặc làm mịn giá trị ngoại lai theo khoảng tứ phân vị (IQR).
        """
        if column not in df.columns:
            return df
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        df[column] = df[column].clip(lower=lower, upper=upper)
        return df
