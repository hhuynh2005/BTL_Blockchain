"""
Các chỉ số đánh giá sai số định giá: MAE, RMSE, MAPE (Nam Khánh phụ trách)
"""

import numpy as np
import pandas as pd


class ValuationMetrics:
    @staticmethod
    def calculate_mae(y_true: pd.Series, y_pred: pd.Series) -> float:
        """Mean Absolute Error"""
        return float(np.mean(np.abs(y_pred - y_true)))

    @staticmethod
    def calculate_rmse(y_true: pd.Series, y_pred: pd.Series) -> float:
        """Root Mean Squared Error"""
        return float(np.sqrt(np.mean((y_pred - y_true) ** 2)))

    @staticmethod
    def calculate_mape(y_true: pd.Series, y_pred: pd.Series) -> float:
        """Mean Absolute Percentage Error (%)"""
        mask = y_true != 0
        return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

    @staticmethod
    def evaluate_all(y_true: pd.Series, y_pred: pd.Series) -> dict:
        return {
            "MAE": round(ValuationMetrics.calculate_mae(y_true, y_pred), 4),
            "RMSE": round(ValuationMetrics.calculate_rmse(y_true, y_pred), 4),
            "MAPE": round(ValuationMetrics.calculate_mape(y_true, y_pred), 2),
        }
