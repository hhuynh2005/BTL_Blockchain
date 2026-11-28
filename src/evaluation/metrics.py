"""
Các chỉ số đánh giá sai số định giá (Nam Khánh phụ trách)

- MAE   : Mean Absolute Error
- RMSE  : Root Mean Squared Error
- MAPE  : Mean Absolute Percentage Error (%)
- sMAPE : Symmetric MAPE (%) – ổn định hơn khi giá rất nhỏ
- Bias  : Sai lệch trung bình (dương = mô hình định giá cao hơn thị trường)
- R2    : Hệ số xác định
- DirAcc: Tỷ lệ dự đoán đúng hướng biến động (%)

Mọi hàm tự căn chỉnh index và bỏ các cặp có NaN/inf trước khi tính.
"""

from typing import Iterable, Tuple, Union

import numpy as np
import pandas as pd

ArrayLike = Union[pd.Series, np.ndarray, Iterable[float]]


def _align(y_true: ArrayLike, y_pred: ArrayLike) -> Tuple[np.ndarray, np.ndarray]:
    if isinstance(y_true, pd.Series) and isinstance(y_pred, pd.Series):
        df = pd.concat([y_true.rename("t"), y_pred.rename("p")], axis=1, join="inner")
        t, p = df["t"].to_numpy(dtype=float), df["p"].to_numpy(dtype=float)
    else:
        t = np.asarray(y_true, dtype=float).ravel()
        p = np.asarray(y_pred, dtype=float).ravel()
        if t.shape != p.shape:
            raise ValueError(f"Kích thước không khớp: {t.shape} vs {p.shape}")
    mask = np.isfinite(t) & np.isfinite(p)
    return t[mask], p[mask]


class ValuationMetrics:
    @staticmethod
    def calculate_mae(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """Mean Absolute Error"""
        t, p = _align(y_true, y_pred)
        return float(np.mean(np.abs(p - t))) if t.size else float("nan")

    @staticmethod
    def calculate_rmse(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """Root Mean Squared Error"""
        t, p = _align(y_true, y_pred)
        return float(np.sqrt(np.mean((p - t) ** 2))) if t.size else float("nan")

    @staticmethod
    def calculate_mape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """Mean Absolute Percentage Error (%) – bỏ qua các điểm y_true = 0"""
        t, p = _align(y_true, y_pred)
        mask = t != 0
        if not mask.any():
            return float("nan")
        return float(np.mean(np.abs((t[mask] - p[mask]) / t[mask])) * 100)

    @staticmethod
    def calculate_smape(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """Symmetric MAPE (%)"""
        t, p = _align(y_true, y_pred)
        denom = (np.abs(t) + np.abs(p)) / 2
        mask = denom != 0
        if not mask.any():
            return float("nan")
        return float(np.mean(np.abs(p[mask] - t[mask]) / denom[mask]) * 100)

    @staticmethod
    def calculate_bias(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """Sai lệch trung bình (Mean Error) = mean(y_pred - y_true)"""
        t, p = _align(y_true, y_pred)
        return float(np.mean(p - t)) if t.size else float("nan")

    @staticmethod
    def calculate_r2(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """Hệ số xác định R^2"""
        t, p = _align(y_true, y_pred)
        if t.size < 2:
            return float("nan")
        ss_tot = np.sum((t - t.mean()) ** 2)
        if ss_tot == 0:
            return float("nan")
        return float(1 - np.sum((t - p) ** 2) / ss_tot)

    @staticmethod
    def calculate_directional_accuracy(y_true: ArrayLike, y_pred: ArrayLike) -> float:
        """% số phiên mà hướng thay đổi của giá định giá trùng với hướng thay đổi giá thực"""
        t, p = _align(y_true, y_pred)
        if t.size < 2:
            return float("nan")
        dt, dp = np.sign(np.diff(t)), np.sign(np.diff(p))
        return float(np.mean(dt == dp) * 100)

    @staticmethod
    def evaluate_all(y_true: ArrayLike, y_pred: ArrayLike, extended: bool = False) -> dict:
        result = {
            "MAE": round(ValuationMetrics.calculate_mae(y_true, y_pred), 4),
            "RMSE": round(ValuationMetrics.calculate_rmse(y_true, y_pred), 4),
            "MAPE": round(ValuationMetrics.calculate_mape(y_true, y_pred), 2),
        }
        if extended:
            result.update(
                {
                    "sMAPE": round(ValuationMetrics.calculate_smape(y_true, y_pred), 2),
                    "Bias": round(ValuationMetrics.calculate_bias(y_true, y_pred), 4),
                    "R2": round(ValuationMetrics.calculate_r2(y_true, y_pred), 4),
                    "DirAcc": round(ValuationMetrics.calculate_directional_accuracy(y_true, y_pred), 2),
                }
            )
        return result
