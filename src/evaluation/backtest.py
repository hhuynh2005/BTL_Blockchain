"""
Khung thử nghiệm Backtesting (Nam Khánh phụ trách)

Hai chế độ:
1. `run_backtest`     – chia train/test theo thời gian (mặc định 70/30), fit trên train,
                        đánh giá out-of-sample trên test.
2. `run_walk_forward` – walk-forward (expanding hoặc rolling window): định kỳ fit lại mô hình
                        trên dữ liệu quá khứ và dự báo cho đoạn kế tiếp. Phù hợp với chuỗi
                        giá crypto không dừng.

Ngoài ra `compare_models` chạy nhiều mô hình (kèm baseline SMA-30) và trả về bảng xếp hạng.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.evaluation.metrics import ValuationMetrics
from src.models.base import ValuationModel


class SMABaselineModel(ValuationModel):
    """Mô hình đối chuẩn: trung bình trượt giá thị trường (Simple Moving Average)."""

    def __init__(self, window: int = 30):
        super().__init__(name=f"Baseline_SMA{window}")
        self.window = window
        self._history: Optional[pd.Series] = None

    def fit(self, df: pd.DataFrame) -> "SMABaselineModel":
        self._history = df["price_usd"].astype(float).tail(self.window) if "price_usd" in df.columns else None
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        price = df["price_usd"].astype(float)
        # Ghép phần đuôi của tập train để SMA ở đầu tập test có đủ cửa sổ.
        # shift(1): chỉ dùng thông tin tới phiên trước -> không nhìn trước tương lai.
        if self._history is not None:
            hist = self._history[~self._history.index.isin(price.index)]
            full = pd.concat([hist, price])
        else:
            full = price
        sma = full.rolling(self.window, min_periods=1).mean().shift(1)
        out = sma.loc[price.index]
        return out.fillna(price).rename(self.name)


@dataclass
class BacktestResult:
    model_name: str
    metrics: Dict[str, float]
    predictions: pd.Series
    actual: pd.Series
    train_size: int
    test_size: int
    extra: Dict = field(default_factory=dict)

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame({"actual": self.actual, "predicted": self.predictions})


class BacktestEngine:
    def __init__(self, train_ratio: float = 0.7, extended_metrics: bool = False):
        if not 0 < train_ratio < 1:
            raise ValueError("train_ratio phải nằm trong (0, 1)")
        self.train_ratio = train_ratio
        self.extended_metrics = extended_metrics

    # ------------------------------------------------------------------ #
    def split(self, df: pd.DataFrame):
        df = self._sort(df)
        split_idx = max(1, min(len(df) - 1, int(len(df) * self.train_ratio)))
        return df.iloc[:split_idx], df.iloc[split_idx:]

    @staticmethod
    def _sort(df: pd.DataFrame) -> pd.DataFrame:
        if "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
        return df

    # ------------------------------------------------------------------ #
    def run_backtest(self, model: ValuationModel, df: pd.DataFrame, target_col: str = "price_usd") -> Dict[str, float]:
        """Giữ nguyên API cũ: trả về dict chỉ số sai số trên tập test."""
        return self.run_detailed(model, df, target_col).metrics

    def run_detailed(self, model: ValuationModel, df: pd.DataFrame, target_col: str = "price_usd") -> BacktestResult:
        train_df, test_df = self.split(df)
        model.fit(train_df)
        preds = pd.Series(np.asarray(model.predict(test_df), dtype=float), index=test_df.index)
        y_true = test_df[target_col].astype(float)
        metrics = ValuationMetrics.evaluate_all(y_true, preds, extended=self.extended_metrics)
        return BacktestResult(model.name, metrics, preds, y_true, len(train_df), len(test_df))

    def run_walk_forward(
        self,
        model: ValuationModel,
        df: pd.DataFrame,
        target_col: str = "price_usd",
        initial_train: Optional[int] = None,
        step: int = 7,
        window: Optional[int] = None,
    ) -> BacktestResult:
        """
        Walk-forward validation.
        - initial_train: số phiên tối thiểu cho lần fit đầu (mặc định = train_ratio * N)
        - step: số phiên dự báo trước khi fit lại
        - window: None -> expanding window; số nguyên -> rolling window kích thước cố định
        """
        df = self._sort(df)
        n = len(df)
        start = initial_train or max(1, int(n * self.train_ratio))
        if start >= n:
            raise ValueError("Không đủ dữ liệu cho walk-forward")

        preds: List[pd.Series] = []
        n_refits = 0
        for t in range(start, n, step):
            lo = 0 if window is None else max(0, t - window)
            train = df.iloc[lo:t]
            test = df.iloc[t : t + step]
            model.fit(train)
            n_refits += 1
            preds.append(pd.Series(np.asarray(model.predict(test), dtype=float), index=test.index))

        pred_series = pd.concat(preds)
        y_true = df.loc[pred_series.index, target_col].astype(float)
        metrics = ValuationMetrics.evaluate_all(y_true, pred_series, extended=self.extended_metrics)
        return BacktestResult(
            model.name, metrics, pred_series, y_true, start, len(pred_series), extra={"n_refits": n_refits}
        )

    # ------------------------------------------------------------------ #
    def compare_models(
        self,
        models: List[ValuationModel],
        df: pd.DataFrame,
        target_col: str = "price_usd",
        include_baseline: bool = True,
        walk_forward: bool = False,
        sort_by: str = "MAPE",
        **wf_kwargs,
    ) -> pd.DataFrame:
        """Chạy backtest cho danh sách mô hình, trả về bảng chỉ số đã sắp xếp."""
        all_models = list(models)
        if include_baseline:
            all_models.append(SMABaselineModel(30))

        rows = []
        for m in all_models:
            res = (
                self.run_walk_forward(m, df, target_col, **wf_kwargs)
                if walk_forward
                else self.run_detailed(m, df, target_col)
            )
            rows.append({"model": res.model_name, **res.metrics})

        table = pd.DataFrame(rows).set_index("model")
        if sort_by in table.columns:
            table = table.sort_values(sort_by)
        return table

    def backtest_per_token(
        self,
        model_factory,
        df: pd.DataFrame,
        token_col: str = "token",
        target_col: str = "price_usd",
    ) -> pd.DataFrame:
        """
        Backtest riêng cho từng token. `model_factory` là hàm không tham số trả về mô hình mới
        (tránh rò rỉ tham số đã fit giữa các token).
        """
        rows = []
        for token, g in df.groupby(token_col):
            if len(g) < 3:
                continue
            res = self.run_detailed(model_factory(), g, target_col)
            rows.append({"token": token, "model": res.model_name, **res.metrics})
        return pd.DataFrame(rows)
