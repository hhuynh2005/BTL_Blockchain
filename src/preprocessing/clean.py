"""
Làm sạch dữ liệu thị trường / on-chain theo các quy tắc trong ``data/SCHEMA.md`` (Khanh phụ trách).

Pipeline ``DataCleaner.clean_token_dataset`` thực hiện, **riêng cho từng token**:
  1. Chuẩn hóa mốc thời gian về ngày UTC 00:00 và loại bản ghi trùng ngày.
  2. Kiểm tra tính hợp lệ: giá trị âm / giá bằng 0 -> coi là thiếu (NaN).
  3. Đồng bộ lịch ngày liên tục; điền khuyết bằng forward-fill **tối đa 3 ngày**
     (quy tắc 1 SCHEMA.md). Không dùng backward-fill để tránh rò rỉ dữ liệu tương lai.
  4. Gắn cờ ``is_anomaly`` khi volume > 10 lần trung bình 30 ngày trước đó (quy tắc 4).
  5. Giới hạn (winsorize) ngoại lai theo IQR trên **chuỗi tỷ suất biến động** của từng
     token, không cắt trực tiếp mức giá (tránh làm méo xu hướng dài hạn).

Lưu ý quan trọng: mọi phép thống kê đều tính trong phạm vi một token. Gộp nhiều token
rồi mới tính IQR sẽ cắt sai giá của token giá cao (vd BTC bị kéo về mức giá của UNI).
"""

from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# Cột phải dương (>0) và cột chỉ cần không âm (>=0) theo SCHEMA.md
STRICTLY_POSITIVE = ["price_usd", "circulating_supply", "pool_reserve0", "pool_reserve1"]
NON_NEGATIVE = ["volume_24h", "market_cap", "tvl", "tx_count", "active_addresses", "onchain_volume_usd"]

# Cột áp dụng làm mịn ngoại lai mặc định (đều là đại lượng dòng chảy dễ có đột biến)
DEFAULT_OUTLIER_COLS = ["volume_24h", "onchain_volume_usd", "tvl"]


class DataCleaner:
    MAX_FFILL_DAYS = 3
    ANOMALY_MULTIPLIER = 10.0
    ANOMALY_WINDOW = 30

    # ------------------------------------------------------------------ bước 1-3
    @staticmethod
    def normalize_dates(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        """Chuyển cột ngày về ngày UTC (không kèm múi giờ), làm tròn xuống 00:00."""
        out = df.copy()
        dt = pd.to_datetime(out[date_col], utc=True)
        out[date_col] = dt.dt.floor("D").dt.tz_localize(None)
        return out

    @staticmethod
    def validate_values(df: pd.DataFrame) -> pd.DataFrame:
        """Thay giá trị vi phạm ràng buộc dấu (SCHEMA.md quy tắc 2) bằng NaN để xử lý như dữ liệu thiếu."""
        out = df.copy()
        for col in STRICTLY_POSITIVE:
            if col in out.columns:
                s = pd.to_numeric(out[col], errors="coerce")
                out[col] = s.where(s > 0)
        for col in NON_NEGATIVE:
            if col in out.columns:
                s = pd.to_numeric(out[col], errors="coerce")
                out[col] = s.where(s >= 0)
        return out

    @staticmethod
    def clean_timeseries(
        df: pd.DataFrame,
        date_col: str = "date",
        max_ffill_days: int = MAX_FFILL_DAYS,
    ) -> pd.DataFrame:
        """
        Làm sạch chuỗi thời gian của **một** token: chuẩn hóa ngày UTC, bỏ trùng ngày
        (giữ bản ghi cuối cùng), lấp đầy lịch ngày liên tục và forward-fill tối đa
        ``max_ffill_days`` ngày. Khoảng trống dài hơn vẫn để NaN và được đánh dấu
        ở cột ``is_filled = False`` cho người dùng xử lý tiếp.
        """
        if df.empty or date_col not in df.columns:
            return df.copy()

        out = DataCleaner.normalize_dates(df, date_col)
        out = out.sort_values(date_col).drop_duplicates(subset=[date_col], keep="last")
        out = out.set_index(date_col)

        full_index = pd.date_range(out.index.min(), out.index.max(), freq="D", name=date_col)
        observed = out.index
        out = out.reindex(full_index)

        numeric_cols = out.select_dtypes(include="number").columns
        other_cols = out.columns.difference(numeric_cols)
        out[numeric_cols] = out[numeric_cols].ffill(limit=max_ffill_days)
        # Cột định danh (token, sector...) không đổi theo thời gian -> điền cả hai chiều
        out[other_cols] = out[other_cols].ffill().bfill()

        out["is_filled"] = ~out.index.isin(observed)
        return out.reset_index()

    # ------------------------------------------------------------------ bước 4
    @staticmethod
    def flag_volume_anomalies(
        df: pd.DataFrame,
        volume_col: str = "volume_24h",
        window: int = ANOMALY_WINDOW,
        multiplier: float = ANOMALY_MULTIPLIER,
    ) -> pd.DataFrame:
        """
        ``is_anomaly = True`` khi volume trong ngày vượt ``multiplier`` lần trung bình
        ``window`` ngày **trước đó** (shift 1 để không so sánh với chính nó).
        Dữ liệu phải là một token, đã sắp xếp theo ngày.
        """
        out = df.copy()
        if volume_col not in out.columns:
            out["is_anomaly"] = False
            return out
        vol = out[volume_col].astype(float)
        baseline = vol.shift(1).rolling(window, min_periods=min(7, window)).mean()
        out["is_anomaly"] = (vol > multiplier * baseline).fillna(False).astype(bool)
        return out

    # ------------------------------------------------------------------ bước 5
    @staticmethod
    def remove_outliers_iqr(
        df: pd.DataFrame,
        column: str,
        multiplier: float = 3.0,
        window: int = 30,
    ) -> pd.DataFrame:
        """
        Winsorize ngoại lai của ``column`` bằng quy tắc IQR áp lên **độ lệch cục bộ**:

            r_t = ln(x_t) - median(ln x_{t-window..t-1})      (trung vị trượt quá khứ)
            r_t bị giới hạn trong [Q1 - k·IQR, Q3 + k·IQR] của chuỗi r
            x_t' = exp(median_t + r_t')

        So với cắt IQR trực tiếp trên mức giá trị, cách này (i) không cắt nhầm xu
        hướng tăng/giảm dài hạn, (ii) chỉ sửa đúng ngày đột biến, không làm trôi
        các ngày sau, (iii) chỉ dùng dữ liệu quá khứ nên không rò rỉ tương lai.

        Hàm giả định ``df`` chỉ chứa **một** token và đã sắp xếp theo ngày.
        """
        out = df.copy()
        if column not in out.columns:
            return out
        series = pd.to_numeric(out[column], errors="coerce").astype(float)
        if series.dropna().size < 8:
            return out  # quá ít điểm để ước lượng tứ phân vị tin cậy

        positive = series.where(series > 0)
        log_s = np.log(positive)
        local_med = log_s.shift(1).rolling(window, min_periods=5).median()
        resid = log_s - local_med
        q1, q3 = resid.quantile([0.25, 0.75])
        iqr = q3 - q1
        if not np.isfinite(iqr) or iqr == 0:
            return out
        clipped = resid.clip(q1 - multiplier * iqr, q3 + multiplier * iqr)
        changed = (clipped != resid) & clipped.notna()
        if not changed.any():
            return out
        fixed = series.copy()
        fixed[changed] = np.exp(local_med[changed] + clipped[changed])
        out[column] = fixed
        return out

    # ------------------------------------------------------------------ pipeline
    @staticmethod
    def clean_single_token(
        df: pd.DataFrame,
        outlier_cols: Optional[List[str]] = None,
        iqr_multiplier: float = 3.0,
    ) -> pd.DataFrame:
        """Pipeline đầy đủ cho một token."""
        out = DataCleaner.validate_values(df)
        out = DataCleaner.clean_timeseries(out)
        out = DataCleaner.flag_volume_anomalies(out)
        cols = DEFAULT_OUTLIER_COLS if outlier_cols is None else outlier_cols
        for col in cols:
            out = DataCleaner.remove_outliers_iqr(out, col, multiplier=iqr_multiplier)

        # Giữ ràng buộc market_cap = price × supply sau khi điền khuyết
        if {"market_cap", "price_usd", "circulating_supply"}.issubset(out.columns):
            missing_mc = out["market_cap"].isna()
            out.loc[missing_mc, "market_cap"] = out.loc[missing_mc, "price_usd"] * out.loc[missing_mc, "circulating_supply"]
        return out

    @staticmethod
    def clean_token_dataset(
        df: pd.DataFrame,
        numeric_cols: Optional[List[str]] = None,
        token_col: str = "token",
        iqr_multiplier: float = 3.0,
    ) -> pd.DataFrame:
        """
        Pipeline làm sạch cho bảng nhiều token: chạy ``clean_single_token`` độc lập
        trên từng token rồi ghép lại (sắp xếp theo token, ngày).

        ``numeric_cols``: danh sách cột cần làm mịn ngoại lai (mặc định volume, on-chain volume, TVL).
        """
        if df.empty:
            return df.copy()
        if token_col not in df.columns:
            return DataCleaner.clean_single_token(df, numeric_cols, iqr_multiplier)

        parts = []
        for sym, group in df.groupby(token_col, sort=True):
            cleaned = DataCleaner.clean_single_token(group, numeric_cols, iqr_multiplier)
            cleaned[token_col] = sym
            parts.append(cleaned)
        return pd.concat(parts, ignore_index=True)

    @staticmethod
    def quality_report(df: pd.DataFrame, token_col: str = "token") -> pd.DataFrame:
        """Bảng tóm tắt chất lượng dữ liệu theo token (phục vụ Chương 3)."""
        rows: List[Dict] = []
        groups = df.groupby(token_col) if token_col in df.columns else [("ALL", df)]
        for sym, g in groups:
            rows.append({
                "token": sym,
                "so_ngay": len(g),
                "tu_ngay": pd.to_datetime(g["date"]).min().date() if "date" in g else None,
                "den_ngay": pd.to_datetime(g["date"]).max().date() if "date" in g else None,
                "ngay_noi_suy": int(g["is_filled"].sum()) if "is_filled" in g else 0,
                "ngay_bat_thuong": int(g["is_anomaly"].sum()) if "is_anomaly" in g else 0,
                **{
                    f"thieu_{c}": int(g[c].isna().sum())
                    for c in ("price_usd", "volume_24h", "market_cap", "circulating_supply", "tvl")
                    if c in g.columns
                },
            })
        return pd.DataFrame(rows)
