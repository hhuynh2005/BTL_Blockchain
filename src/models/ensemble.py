"""
================================================================================
MODULE: src/models/ensemble.py
TÁC GIẢ: Huỳnh (Trưởng nhóm - Nhánh feature/models)
MỤC ĐÍCH:
  Triển khai mô hình kết hợp Ensemble Valuation:
    P_ensemble = w_1 * P_1 + w_2 * P_2 + ... + w_k * P_k
  với các ràng buộc:
    sum(w_i) = 1.0,  w_i >= 0  (i = 1 .. k).

  Thuật toán tối ưu hóa trọng số:
    Tối thiểu hóa sai số tuyệt đối trung bình (MAE) hoặc sai số toàn phương (RMSE)
    trên tập dữ liệu huấn luyện lịch sử bằng giải thuật Sequential Least Squares
    Programming (SLSQP) từ thư viện scipy.optimize.
================================================================================
"""

from typing import Dict, List, Optional, Union
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from src.models.base import ValuationModel


class EnsembleValuationModel(ValuationModel):
    """
    Mô hình Ensemble tích hợp nhiều mô hình thành phần với trọng số tối ưu.
    """

    def __init__(
        self,
        models: List[ValuationModel],
        initial_weights: Optional[Dict[str, float]] = None,
        loss_metric: str = "MAE",
    ):
        """
        Khởi tạo mô hình Ensemble.

        Args:
            models (List[ValuationModel]): Danh sách các mô hình con kế thừa ValuationModel.
            initial_weights (Dict[str, float], optional): Trọng số khởi tạo ban đầu.
            loss_metric (str): Hàm mất mát cần tối thiểu hóa ('MAE' hoặc 'RMSE').
        """
        super().__init__(
            name="Ensemble_Combined",
            description="Mô hình kết hợp Ensemble có trọng số tối ưu hóa MAE",
        )
        if not models:
            raise ValueError("Danh sách mô hình con không được rỗng.")

        self.models: List[ValuationModel] = models
        self.loss_metric: str = loss_metric.upper()

        # Khởi tạo trọng số
        n = len(models)
        if initial_weights:
            self.weights = self._normalize_weights(initial_weights)
        else:
            self.weights = {m.name: 1.0 / n for m in models}

        self.params = {"weights": self.weights, "loss_metric": self.loss_metric}

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Chuẩn hóa trọng số sao cho tổng bằng 1.0 và không âm."""
        model_names = [m.name for m in self.models]
        filtered = {name: max(0.0, float(weights.get(name, 0.0))) for name in model_names}
        total = sum(filtered.values())
        if total > 0:
            return {name: val / total for name, val in filtered.items()}
        n = len(model_names)
        return {name: 1.0 / n for name in model_names}

    def fit(
        self,
        df: pd.DataFrame,
        target_col: str = "price_usd",
        optimize_weights: bool = True,
    ) -> "EnsembleValuationModel":
        """
        Huấn luyện từng mô hình con và tối ưu hóa trọng số Ensemble.

        Args:
            df (pd.DataFrame): Dữ liệu chuỗi thời gian huấn luyện.
            target_col (str): Cột giá thị trường thực tế dùng để tính hàm mất mát.
            optimize_weights (bool): Nếu True, chạy giải thuật tối ưu hóa trọng số.
        """
        # 1. Fit từng mô hình con và thu thập dự báo
        predictions_dict: Dict[str, np.ndarray] = {}
        for model in self.models:
            model.fit(df)
            pred_series = model.predict(df)
            predictions_dict[model.name] = pred_series.to_numpy()

        # 2. Tối ưu hóa trọng số nếu có cột giá thực tế
        if optimize_weights and target_col in df.columns:
            y_true = df[target_col].to_numpy()
            model_names = [m.name for m in self.models]
            # Ma trận dự báo kích thước (N, K)
            pred_matrix = np.column_stack([predictions_dict[name] for name in model_names])

            # Lọc bỏ các dòng có NaN
            valid_mask = ~np.isnan(y_true) & ~np.isnan(pred_matrix).any(axis=1)
            y_t = y_true[valid_mask]
            X_p = pred_matrix[valid_mask]

            if len(y_t) >= 10:
                def objective_function(w: np.ndarray) -> float:
                    y_pred = X_p @ w
                    if self.loss_metric == "RMSE":
                        return float(np.sqrt(np.mean((y_pred - y_t) ** 2)))
                    # Mặc định MAE
                    return float(np.mean(np.abs(y_pred - y_t)))

                n = len(model_names)
                init_w = np.array([self.weights.get(name, 1.0 / n) for name in model_names])
                bounds = [(0.0, 1.0) for _ in range(n)]
                constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0})

                res = minimize(
                    objective_function,
                    init_w,
                    method="SLSQP",
                    bounds=bounds,
                    constraints=constraints,
                    options={"maxiter": 200, "ftol": 1e-6},
                )

                if res.success:
                    opt_w = np.clip(res.x, 0.0, 1.0)
                    opt_w = opt_w / np.sum(opt_w)
                    self.weights = {name: round(float(w), 4) for name, w in zip(model_names, opt_w)}
                else:
                    # Fallback lưới đơn giản nếu tối ưu hóa không hội tụ
                    self._fallback_grid_search(X_p, y_t, model_names)

        self.params = {
            "weights": self.weights,
            "loss_metric": self.loss_metric,
            "sub_models": [m.name for m in self.models],
        }
        self.is_fitted = True
        return self

    def _fallback_grid_search(self, X_p: np.ndarray, y_t: np.ndarray, model_names: List[str]) -> None:
        """Thuật toán tìm kiếm theo lưới đơn giản dự phòng khi SLSQP gặp vấn đề số học."""
        n = len(model_names)
        best_loss = float("inf")
        best_weights = self.weights

        # Sinh 500 mẫu trọng số Dirichlet ngẫu nhiên
        np.random.seed(42)
        sample_weights = np.random.dirichlet(np.ones(n), size=500)
        for w in sample_weights:
            y_pred = X_p @ w
            loss = np.mean(np.abs(y_pred - y_t))
            if loss < best_loss:
                best_loss = loss
                best_weights = {name: round(float(val), 4) for name, val in zip(model_names, w)}

        self.weights = best_weights

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """
        Dự báo giá trị hợp lý kết hợp bằng tổng có trọng số:
        P_ensemble = sum(w_i * P_i)
        """
        if not self.models:
            return pd.Series(1.0, index=df.index)

        total_series = pd.Series(0.0, index=df.index)
        for model in self.models:
            w = self.weights.get(model.name, 0.0)
            if w > 0:
                pred = model.predict(df)
                total_series += w * pred

        # Điền fallback nếu phát sinh NaN
        if "price_usd" in df.columns:
            return total_series.fillna(df["price_usd"])
        return total_series.fillna(1.0)

    def load_weights_from_yaml(
        self,
        config_path: Union[str, Path] = "config/weights.yaml",
        sector: Optional[str] = None,
        token: Optional[str] = None,
    ) -> "EnsembleValuationModel":
        """
        Tải trọng số đã hiệu chỉnh từ tệp config/weights.yaml theo Token hoặc Sector.
        """
        path = Path(config_path)
        if not path.exists():
            return self

        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        target_weights = None
        # Ưu tiên 1: Trọng số riêng của Token
        if token and "token_weights" in cfg and token in cfg["token_weights"]:
            target_weights = cfg["token_weights"][token]
        # Ưu tiên 2: Trọng số theo ngành
        elif sector and "sector_weights" in cfg and sector in cfg["sector_weights"]:
            target_weights = cfg["sector_weights"][sector]
        # Ưu tiên 3: Trọng số mặc định
        elif "default_weights" in cfg:
            target_weights = cfg["default_weights"]

        if target_weights:
            # Map tên trong yaml sang model name
            name_mapping = {
                "nvt": "NVT_Metcalfe",
                "mv_pq": "MV_PQ",
                "twap": "Uniswap_TWAP",
                "comparable": "Comparable_MCTVL",
            }
            mapped = {}
            for k, v in target_weights.items():
                mapped_name = name_mapping.get(k, k)
                mapped[mapped_name] = v
            self.weights = self._normalize_weights(mapped)
            self.params["weights"] = self.weights

        return self
