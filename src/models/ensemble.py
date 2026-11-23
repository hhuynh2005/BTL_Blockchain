"""
Mô hình kết hợp Ensemble Valuation (Huỳnh phụ trách)
Kết hợp có trọng số từ các mô hình thành phần:
P_ensemble = w_nvt * P_nvt + w_mvpq * P_mvpq + w_twap * P_twap + w_comp * P_comp
với sum(w_i) = 1.0, w_i >= 0.
Tối ưu hóa trọng số dựa trên việc tối thiểu hóa MAE trên tập dữ liệu lịch sử.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from scipy.optimize import minimize
from src.models.base import ValuationModel


class EnsembleValuationModel(ValuationModel):
    def __init__(self, models: List[ValuationModel], initial_weights: Optional[Dict[str, float]] = None):
        super().__init__(name="Ensemble_Combined")
        self.models = models
        if initial_weights:
            self.weights = initial_weights
        else:
            n = len(models)
            self.weights = {m.name: 1.0 / n for m in models}

    def fit(self, df: pd.DataFrame, target_col: str = "price_usd") -> "EnsembleValuationModel":
        # Fit từng mô hình con
        preds = {}
        for m in self.models:
            m.fit(df)
            preds[m.name] = m.predict(df).values

        # Nếu có giá thực tế, tối ưu hóa trọng số bằng scipy minimize (L-BFGS-B hoặc SLSQP)
        if target_col in df.columns:
            y_true = df[target_col].values
            model_names = [m.name for m in self.models]
            pred_matrix = np.column_stack([preds[name] for name in model_names])

            def loss_func(w):
                y_pred = pred_matrix @ w
                return np.mean(np.abs(y_pred - y_true))

            n = len(model_names)
            init_w = np.array([self.weights.get(name, 1.0 / n) for name in model_names])
            bounds = [(0.0, 1.0) for _ in range(n)]
            constraints = ({"type": "eq", "fun": lambda w: np.sum(w) - 1.0})

            res = minimize(loss_func, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
            if res.success:
                optimized_weights = {name: float(w) for name, w in zip(model_names, res.x)}
                self.weights = optimized_weights

        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        total_pred = pd.Series(0.0, index=df.index)
        for m in self.models:
            w = self.weights.get(m.name, 0.0)
            total_pred += w * m.predict(df)
        return total_pred
