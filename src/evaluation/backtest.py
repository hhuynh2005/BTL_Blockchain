"""
Khung thử nghiệm Backtesting (Nam Khánh phụ trách)
Chia tập huấn luyện / kiểm tra theo thời gian và đánh giá sai số mô hình.
"""

import pandas as pd
from typing import Dict
from src.models.base import ValuationModel
from src.evaluation.metrics import ValuationMetrics


class BacktestEngine:
    def __init__(self, train_ratio: float = 0.7):
        self.train_ratio = train_ratio

    def run_backtest(self, model: ValuationModel, df: pd.DataFrame, target_col: str = "price_usd") -> Dict[str, float]:
        n = len(df)
        split_idx = int(n * self.train_ratio)
        train_df = df.iloc[:split_idx]
        test_df = df.iloc[split_idx:]

        model.fit(train_df)
        preds = model.predict(test_df)
        y_true = test_df[target_col]

        metrics = ValuationMetrics.evaluate_all(y_true, preds)
        return metrics
