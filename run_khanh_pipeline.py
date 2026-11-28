"""
Demo pipeline phần việc của Khanh (nhánh feature/preprocess):
  1. Nạp dữ liệu thật (data/processed/market_dataset.csv — tạo bằng
     ``python -m src.preprocessing.build_dataset``); nếu chưa có thì dùng sample_tokens.csv.
  2. Làm sạch (DataCleaner)  3. Sinh đặc trưng (FeatureEngineer)
  4. Định giá MV = PQ walk-forward (không nhìn trước)  5. Đánh giá MAE / RMSE / MAPE.

Chạy:  python run_khanh_pipeline.py
"""

import sys
from pathlib import Path

import pandas as pd

from src.evaluation.metrics import ValuationMetrics
from src.models.mv_pq import MVPQValuationModel
from src.preprocessing.clean import DataCleaner
from src.preprocessing.features import FeatureEngineer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # in tiếng Việt trên terminal Windows

REAL_DATA = Path("data/processed/market_dataset_raw.csv")
SAMPLE_DATA = Path("data/processed/sample_tokens.csv")


def run_pipeline() -> pd.DataFrame:
    src = REAL_DATA if REAL_DATA.exists() else SAMPLE_DATA
    df_raw = pd.read_csv(src)
    print("=" * 78)
    print(f"[1] Nạp {src}: {len(df_raw)} dòng, token = {sorted(df_raw['token'].unique())}")

    df_clean = DataCleaner.clean_token_dataset(df_raw)
    print("[2] Làm sạch xong. Báo cáo chất lượng:")
    print(DataCleaner.quality_report(df_clean).to_string(index=False))

    df_feat = FeatureEngineer.generate_features(df_clean)
    print("\n[3] Đặc trưng ngày gần nhất:")
    cols = ["token", "price_usd", "velocity", "nvt_ratio", "mc_tvl_ratio", "volatility_30d", "liquidity_score"]
    print(df_feat.groupby("token").tail(1)[[c for c in cols if c in df_feat]].round(3).to_string(index=False))

    print("\n[4] Định giá MV = PQ (V̂ = trung vị V của 90 ngày trước, walk-forward)")
    rows = []
    for sym, g in df_feat.groupby("token"):
        model = MVPQValuationModel(velocity_window=90)
        res = model.analyze_valuation(g, walk_forward=True)
        valid = res.dropna(subset=["fair_price"])
        metrics = ValuationMetrics.evaluate_all(valid["price_usd"], valid["fair_price"])
        last = res.iloc[-1]
        rows.append({
            "Token": sym,
            "Ngày": pd.to_datetime(last["date"]).date(),
            "Giá thị trường": round(last["price_usd"], 2),
            "Giá MV=PQ": round(last["fair_price"], 2),
            "Độ lệch %": f"{last['mispricing_pct']:+.1f}",
            "Tín hiệu": last["signal"],
            "MAE": metrics["MAE"],
            "RMSE": metrics["RMSE"],
            "MAPE %": metrics["MAPE"],
            "Số ngày đánh giá": len(valid),
        })
    summary = pd.DataFrame(rows)
    print(summary.to_string(index=False))
    print("=" * 78)
    return summary


if __name__ == "__main__":
    run_pipeline()
