"""
Mô hình định giá theo Phương trình trao đổi MV = PQ (Fisher, 1911; Burniske, 2017).
Tác giả phụ trách: Khanh (nhánh feature/preprocess)

    M · V = P · Q
    M  : giá trị (vốn hóa) cần thiết của token lưu hành   M = P_fair · S
    V  : vận tốc luân chuyển một năm
    PQ : tổng giá trị giao dịch kinh tế trong năm          PQ ≈ Volume_24h · 365

    =>  P_fair = PQ / (V̂ · S)

Ước lượng V̂ — vấn đề vòng lặp và cách xử lý
--------------------------------------------
Thực nghiệm chỉ quan sát được V_t = PQ_t / MarketCap_t. Nếu dùng chính V_t của ngày t
thì P_fair,t = P_t (mô hình chỉ lặp lại giá thị trường). Vì vậy V̂ phải là một **chuẩn
dài hạn ước lượng từ quá khứ**:

* ``fit(train)`` + ``predict(test)``: V̂ = trung vị V trên ``velocity_window`` ngày cuối
  của tập huấn luyện, giữ cố định khi dự báo tập kiểm thử (out-of-sample).
* ``predict_walk_forward(df)``: V̂_t = trung vị V trong ``velocity_window`` ngày **trước** t
  (dịch 1 ngày, không dùng dữ liệu tương lai) — phù hợp cho backtest theo ngày.

Khi đó  P_fair,t / P_t = V_t / V̂ : mô hình báo *undervalued* khi mức sử dụng (giao dịch
so với vốn hóa) cao hơn chuẩn lịch sử, và *overvalued* khi ngược lại. Đây là cách diễn giải
cần nêu rõ trong báo cáo (Mục 2.3 và Chương 5).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from src.models.base import ValuationModel

ANNUALIZATION = 365.0


class MVPQValuationModel(ValuationModel):
    DEFAULT_VELOCITY = 8.5          # chỉ dùng khi hoàn toàn không có dữ liệu để ước lượng
    VELOCITY_BOUNDS = (0.5, 200.0)  # chặn giá trị phi kinh tế do dữ liệu lỗi

    def __init__(
        self,
        velocity_window: int = 90,
        use_onchain_volume: bool = True,
        pq_smoothing: int = 7,
        velocity: Optional[float] = None,
        signal_threshold_pct: float = 10.0,
    ):
        """
        velocity_window      : số ngày dùng để tính trung vị V̂.
        use_onchain_volume   : ưu tiên ``onchain_volume_usd`` (giảm ảnh hưởng wash trading trên sàn).
        pq_smoothing         : số ngày trung bình trượt (quá khứ) cho PQ để giảm nhiễu volume ngày.
        velocity             : nếu truyền vào, dùng V cố định ngoại sinh (vd chuẩn ngành) thay vì ước lượng.
        signal_threshold_pct : ngưỡng % lệch giá để kết luận Over/Undervalued.
        """
        super().__init__(name="MV_PQ")
        self.velocity_window = velocity_window
        self.use_onchain_volume = use_onchain_volume
        self.pq_smoothing = max(1, int(pq_smoothing))
        self.fixed_velocity = velocity
        self.signal_threshold_pct = signal_threshold_pct
        self.estimated_velocity: float = velocity or self.DEFAULT_VELOCITY
        self.volume_col: str = "volume_24h"
        self.params: Dict[str, Any] = {}

    # ------------------------------------------------------------------ building blocks
    def _choose_volume_col(self, df: pd.DataFrame) -> str:
        if (
            self.use_onchain_volume
            and "onchain_volume_usd" in df.columns
            and (pd.to_numeric(df["onchain_volume_usd"], errors="coerce") > 0).any()
        ):
            return "onchain_volume_usd"
        return "volume_24h"

    def _annual_pq(self, df: pd.DataFrame, col: str) -> pd.Series:
        vol = pd.to_numeric(df[col], errors="coerce").astype(float)
        vol = vol.rolling(self.pq_smoothing, min_periods=1).mean()
        return vol * ANNUALIZATION

    @staticmethod
    def _supply(df: pd.DataFrame) -> pd.Series:
        supply = pd.Series(np.nan, index=df.index, dtype=float)
        if "circulating_supply" in df.columns:
            supply = pd.to_numeric(df["circulating_supply"], errors="coerce").astype(float)
        if {"market_cap", "price_usd"}.issubset(df.columns):
            implied = df["market_cap"].astype(float) / df["price_usd"].astype(float).where(df["price_usd"] > 0)
            supply = supply.fillna(implied)
        return supply.where(supply > 0)

    def _daily_velocity(self, df: pd.DataFrame, col: str) -> pd.Series:
        """V_t quan sát được = PQ_t (đã làm mịn) / MarketCap_t."""
        mc = df["market_cap"].astype(float)
        return self._annual_pq(df, col) / mc.where(mc > 0)

    # ------------------------------------------------------------------ ValuationModel API
    def fit(self, df: pd.DataFrame) -> "MVPQValuationModel":
        """Ước lượng V̂ = trung vị V trên ``velocity_window`` ngày cuối của tập huấn luyện."""
        self.volume_col = self._choose_volume_col(df) if not df.empty else "volume_24h"

        if self.fixed_velocity is not None:
            v_hat, source = float(self.fixed_velocity), "exogenous"
        elif df.empty or "market_cap" not in df.columns or self.volume_col not in df.columns:
            v_hat, source = self.DEFAULT_VELOCITY, "default"
        else:
            data = df.sort_values("date") if "date" in df.columns else df
            v = self._daily_velocity(data, self.volume_col).dropna()
            v = v.iloc[-self.velocity_window:]
            v_hat, source = (float(v.median()), "median") if not v.empty else (self.DEFAULT_VELOCITY, "default")

        self.estimated_velocity = float(np.clip(v_hat, *self.VELOCITY_BOUNDS))
        self.params = {
            "estimated_velocity": self.estimated_velocity,
            "velocity_source": source,
            "velocity_window": self.velocity_window,
            "volume_column_used": self.volume_col,
            "pq_smoothing": self.pq_smoothing,
        }
        self.is_fitted = True
        return self

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """P_fair,t = PQ_t / (V̂ · S_t) với V̂ cố định từ ``fit``. Trả NaN nếu thiếu dữ liệu đầu vào."""
        if df.empty:
            return pd.Series(dtype=float, name="fair_price_mvpq")
        if not self.is_fitted:
            raise RuntimeError("Gọi fit() trước khi predict()")
        col = self.volume_col if self.volume_col in df.columns else self._choose_volume_col(df)
        fair = self._annual_pq(df, col) / (self.estimated_velocity * self._supply(df))
        fair.name = "fair_price_mvpq"
        return fair

    def predict_walk_forward(self, df: pd.DataFrame, min_history: int = 14) -> pd.Series:
        """
        Dự báo không nhìn trước cho backtest: V̂_t = trung vị V trong ``velocity_window``
        ngày trước t. ``min_history`` ngày đầu chưa đủ lịch sử sẽ là NaN.
        Dữ liệu phải là một token, đã sắp xếp theo ngày.
        """
        if df.empty:
            return pd.Series(dtype=float, name="fair_price_mvpq")
        col = self._choose_volume_col(df)
        if self.fixed_velocity is not None:
            v_hat = pd.Series(float(self.fixed_velocity), index=df.index)
        else:
            v_obs = self._daily_velocity(df, col)
            v_hat = v_obs.shift(1).rolling(self.velocity_window, min_periods=min_history).median()
        v_hat = v_hat.clip(*self.VELOCITY_BOUNDS)
        fair = self._annual_pq(df, col) / (v_hat * self._supply(df))
        fair.name = "fair_price_mvpq"
        return fair

    # ------------------------------------------------------------------ diagnostics
    def classify(self, mispricing_pct: float) -> str:
        if pd.isna(mispricing_pct):
            return "N/A"
        if mispricing_pct > self.signal_threshold_pct:
            return "Overvalued"
        if mispricing_pct < -self.signal_threshold_pct:
            return "Undervalued"
        return "Fair Value"

    def analyze_valuation(self, df: pd.DataFrame, walk_forward: bool = True) -> pd.DataFrame:
        """
        So sánh giá thị trường với giá hợp lý MV=PQ.

        mispricing_pct = (P_market - P_fair) / P_fair · 100
          > +ngưỡng : Overvalued  — giá thị trường cao hơn giá trị hợp lý
          < -ngưỡng : Undervalued — giá thị trường thấp hơn giá trị hợp lý
          còn lại   : Fair Value

        ``walk_forward=True`` (mặc định) dùng ``predict_walk_forward`` để kết quả không
        bị rò rỉ dữ liệu tương lai; ``False`` dùng V̂ cố định từ ``fit``.
        """
        res = df.copy()
        if "date" in res.columns:
            res = res.sort_values("date").reset_index(drop=True)
        if walk_forward:
            res["fair_price"] = self.predict_walk_forward(res)
        else:
            if not self.is_fitted:
                self.fit(res)
            res["fair_price"] = self.predict(res)

        if "price_usd" in res.columns:
            fair = res["fair_price"]
            res["mispricing_pct"] = ((res["price_usd"].astype(float) - fair) / fair.where(fair > 0) * 100.0).round(2)
            res["signal"] = res["mispricing_pct"].apply(self.classify)
        return res
