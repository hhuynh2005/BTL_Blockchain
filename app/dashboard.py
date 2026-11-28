"""
Dashboard giao diện trực quan hóa định giá token (Nam Khánh phụ trách)
Sử dụng Streamlit: hiển thị biểu đồ giá, giá trị hợp lý theo từng mô hình,
trọng số ensemble, kết quả backtest, so sánh Chainlink và trạng thái smart contract Sepolia.

Chạy:  streamlit run app/dashboard.py
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation import BacktestEngine, ChainlinkComparator, ValuationMetrics, load_market_data  # noqa: E402
from src.models import (  # noqa: E402
    ComparableValuationModel,
    EnsembleValuationModel,
    MVPQValuationModel,
    NVTValuationModel,
    TWAPValuationModel,
)

# Khóa trong weights.yaml -> (tên mô hình, nhãn hiển thị)
MODEL_KEYS = {
    "nvt": ("NVT_Metcalfe", "NVT Ratio & Metcalfe"),
    "mv_pq": ("MV_PQ", "MV = PQ"),
    "twap": ("Uniswap_TWAP", "Uniswap TWAP"),
    "comparable": ("Comparable_MCTVL", "Comparable MC/TVL"),
}
SIGNAL_THRESHOLD_PCT = 5.0
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "0x71C2E63B484e557297e68A7836376cFE94f06B0F")


# --------------------------------------------------------------------------- #
# Tải dữ liệu & cấu hình
# --------------------------------------------------------------------------- #
@st.cache_data
def load_yaml(rel_path: str) -> dict:
    p = ROOT / rel_path
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@st.cache_data
def get_market_data() -> pd.DataFrame:
    df = load_market_data(str(ROOT / "data/processed/market_data.csv"))
    df["date"] = pd.to_datetime(df["date"])
    return df


def build_models():
    return [NVTValuationModel(), MVPQValuationModel(), TWAPValuationModel(), ComparableValuationModel()]


def default_weights(symbol: str, sector: str, cfg: dict) -> dict:
    w = cfg.get("token_weights", {}).get(symbol) or cfg.get("sector_weights", {}).get(sector) or cfg.get(
        "default_weights", {}
    )
    return {k: float(w.get(k, 0.25)) for k in MODEL_KEYS}


@st.cache_data(show_spinner="Đang chạy các mô hình định giá...")
def run_models(token_df: pd.DataFrame, sector_df: pd.DataFrame, train_ratio: float):
    """Fit trên tập train, dự báo toàn bộ chuỗi; trả về bảng giá theo mô hình + trọng số tối ưu."""
    engine = BacktestEngine(train_ratio=train_ratio, extended_metrics=True)
    train_df, _ = engine.split(token_df)

    preds = {}
    for m in build_models():
        if isinstance(m, ComparableValuationModel):
            # Benchmark MC/TVL ước lượng trên toàn ngành trong giai đoạn train
            m.fit(sector_df[sector_df["date"] <= train_df["date"].max()])
        else:
            m.fit(train_df)
        preds[m.name] = m.predict(token_df).astype(float).values
    pred_df = pd.DataFrame(preds, index=token_df["date"])

    ens = EnsembleValuationModel(build_models()).fit(train_df)
    backtest = engine.compare_models(build_models() + [EnsembleValuationModel(build_models())], token_df)
    return pred_df, ens.weights, backtest


# --------------------------------------------------------------------------- #
# Giao diện
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="Công cụ Định giá Token - Đề tài R",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🪙 Công cụ Định giá Token Dựa trên Dữ liệu Thị trường & On-chain")
st.caption("Môn: Chuỗi khối và công nghệ sổ cái phân tán | Nhóm: Huỳnh, Khanh, Kha, Nam Khánh")

tokens_cfg = load_yaml("config/tokens.yaml").get("tokens", [])
weights_cfg = load_yaml("config/weights.yaml")
market = get_market_data()

available = set(market["token"].unique())
tokens_cfg = [t for t in tokens_cfg if t["symbol"] in available] or [
    {"symbol": s, "name": s, "sector": market.loc[market.token == s, "sector"].iloc[0]} for s in sorted(available)
]

if market.attrs.get("source") == "synthetic":
    st.warning(
        "Chưa có `data/processed/market_data.csv` đủ lịch sử – dashboard đang dùng **dữ liệu mô phỏng** "
        "theo SCHEMA.md. Kết quả chỉ mang tính minh họa."
    )

# Sidebar --------------------------------------------------------------------
st.sidebar.header("⚙️ Cấu hình định giá")
selected_symbol = st.sidebar.selectbox("Chọn Token mục tiêu:", [t["symbol"] for t in tokens_cfg], index=0)
selected_token = next(t for t in tokens_cfg if t["symbol"] == selected_symbol)
sector = selected_token.get("sector", "")

st.sidebar.markdown(f"**Tên:** {selected_token.get('name', '')}")
st.sidebar.markdown(f"**Lĩnh vực:** `{sector}`")

token_df = market[market["token"] == selected_symbol].sort_values("date").reset_index(drop=True)
sector_df = market[market["sector"] == sector] if "sector" in market.columns else market

max_days = len(token_df)
lookback = st.sidebar.slider("Khung thời gian hiển thị (ngày):", 30, max_days, min(180, max_days), 10)
train_ratio = st.sidebar.slider("Tỷ lệ tập huấn luyện (backtest):", 0.5, 0.9, 0.7, 0.05)

pred_df, optimized_w, backtest_table = run_models(token_df, sector_df, train_ratio)

st.sidebar.subheader("⚖️ Trọng số Mô hình (Ensemble)")
weight_mode = st.sidebar.radio(
    "Nguồn trọng số:",
    ["Cấu hình (weights.yaml)", "Tối ưu MAE (SLSQP)", "Tùy chỉnh"],
    index=0,
)
cfg_w = default_weights(selected_symbol, sector, weights_cfg)
if weight_mode == "Tối ưu MAE (SLSQP)":
    raw_w = {k: optimized_w.get(name, 0.0) for k, (name, _) in MODEL_KEYS.items()}
    for k, (_, label) in MODEL_KEYS.items():
        st.sidebar.text(f"{label}: {raw_w[k]:.2f}")
elif weight_mode == "Tùy chỉnh":
    raw_w = {
        k: st.sidebar.slider(label, 0.0, 1.0, float(round(cfg_w[k] / 0.05) * 0.05), 0.05, key=f"w_{k}")
        for k, (_, label) in MODEL_KEYS.items()
    }
else:
    raw_w = cfg_w
    for k, (_, label) in MODEL_KEYS.items():
        st.sidebar.text(f"{label}: {raw_w[k]:.2f}")

total_w = sum(raw_w.values())
weights = {k: (v / total_w if total_w > 0 else 0.25) for k, v in raw_w.items()}

# Tính toán ---------------------------------------------------------------------
market_price = token_df.set_index("date")["price_usd"].astype(float)
ensemble_price = sum(weights[k] * pred_df[name] for k, (name, _) in MODEL_KEYS.items())
oracle_price = ChainlinkComparator.simulate_oracle(market_price)

chart_data = pd.DataFrame(
    {
        "Giá thị trường (Spot)": market_price,
        "Định giá Ensemble": ensemble_price,
        **{label: pred_df[name] for _, (name, label) in MODEL_KEYS.items()},
    }
)
view = chart_data.tail(lookback)

split_date = BacktestEngine(train_ratio).split(token_df)[1]["date"].min()
test_mask = chart_data.index >= split_date
oos_metrics = ValuationMetrics.evaluate_all(
    market_price[test_mask], ensemble_price[test_mask], extended=True
)

# Metrics tóm tắt ----------------------------------------------------------------
current_market = float(market_price.iloc[-1])
current_fair = float(ensemble_price.iloc[-1])
diff_pct = (current_fair - current_market) / current_market * 100

if diff_pct > SIGNAL_THRESHOLD_PCT:
    valuation_status = "🟢 Rẻ (Under)"
elif diff_pct < -SIGNAL_THRESHOLD_PCT:
    valuation_status = "🔴 Đắt (Over)"
else:
    valuation_status = "⚪ Hợp lý (Fair)"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Giá thị trường hiện tại", f"${current_market:,.4f}")
col2.metric("Giá trị hợp lý (Ensemble)", f"${current_fair:,.4f}", f"{diff_pct:+.2f}%")
col3.metric("Tín hiệu định giá", valuation_status, help=f"Ngưỡng ±{SIGNAL_THRESHOLD_PCT:.0f}% so với giá thị trường")
col4.metric(
    "MAPE out-of-sample (Ensemble)",
    f"{oos_metrics['MAPE']:.2f}%",
    f"MAE ${oos_metrics['MAE']:,.4f}",
    delta_color="off",
)

st.subheader("📈 Diễn biến Giá thị trường và Kết quả Định giá")
st.line_chart(view[["Giá thị trường (Spot)", "Định giá Ensemble"]])
st.caption(f"Tập kiểm tra (out-of-sample) bắt đầu từ {split_date:%d/%m/%Y}.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "📊 Chi tiết các mô hình",
        "🧪 Backtest & Sai số",
        "🔗 So sánh Chainlink",
        "🏷️ So sánh ngành (MC/TVL)",
        "⛓️ Smart Contract Sepolia",
        "📋 Bảng dữ liệu",
    ]
)

with tab1:
    st.line_chart(view)
    w_df = pd.DataFrame(
        {"Mô hình": [label for _, (_, label) in MODEL_KEYS.items()], "Trọng số": [weights[k] for k in MODEL_KEYS]}
    ).set_index("Mô hình")
    c1, c2 = st.columns([1, 2])
    c1.markdown("**Trọng số ensemble đang áp dụng**")
    c1.dataframe(w_df.style.format("{:.2%}"), width="stretch")
    c2.markdown("**Đóng góp của từng mô hình vào giá hợp lý hiện tại (USD)**")
    contrib = pd.Series(
        {label: weights[k] * float(pred_df[name].iloc[-1]) for k, (name, label) in MODEL_KEYS.items()}
    )
    c2.bar_chart(contrib)

with tab2:
    st.markdown(
        f"Fit trên **{train_ratio:.0%}** dữ liệu đầu, đánh giá trên phần còn lại. "
        "Baseline = trung bình trượt 30 ngày (SMA-30)."
    )
    st.dataframe(backtest_table.style.highlight_min(subset=["MAE", "RMSE", "MAPE"], color="#2e7d3240"),
                 width="stretch")
    st.markdown("**Ensemble với trọng số đang chọn (out-of-sample)**")
    st.json(oos_metrics)
    err = (ensemble_price - market_price)[test_mask] / market_price[test_mask] * 100
    st.markdown("**Sai số % theo thời gian (Ensemble vs thị trường, tập test)**")
    st.area_chart(err.rename("Sai số %"))

with tab3:
    st.info(
        "Chuỗi Chainlink được **mô phỏng** theo cơ chế deviation threshold 1% / heartbeat. "
        "Khi cấu hình `RPC_URL`, giá mới nhất được đọc trực tiếp từ feed on-chain bên dưới."
    )
    cmp_view = pd.DataFrame(
        {"Giá thị trường": market_price, "Chainlink (mô phỏng)": oracle_price, "Định giá Ensemble": ensemble_price}
    ).tail(lookback)
    st.line_chart(cmp_view)
    summary = ChainlinkComparator.summarize(ensemble_price, market_price, oracle_price)
    st.dataframe(pd.Series(summary, name="Giá trị").to_frame(), width="stretch")

    feed = selected_token.get("chainlink_feed")
    if feed:
        st.markdown(f"Feed Chainlink (mainnet): `{feed}`")
        if st.button("Đọc giá Chainlink mới nhất"):
            live = ChainlinkComparator.fetch_latest(feed)
            if live:
                st.success(f"Giá Chainlink: ${live['price']:,.4f} (cập nhật {pd.to_datetime(live['updated_at'], unit='s')})")
            else:
                st.error("Không kết nối được RPC. Kiểm tra biến môi trường `RPC_URL`.")

with tab4:
    comp = ComparableValuationModel().fit(market[market["date"] == market["date"].max()])
    latest = market[market["date"] == market["date"].max()].reset_index(drop=True)
    rel = comp.relative_valuation(latest)
    st.markdown("**Bội số MC/TVL trung vị theo ngành (phiên gần nhất)**")
    st.bar_chart(pd.Series(comp.sector_benchmarks, name="MC/TVL trung vị"))
    st.markdown("**Định giá tương đối của các token**")
    st.dataframe(
        rel.set_index("token").style.format(
            {"mc_tvl": "{:.3f}", "benchmark_mc_tvl": "{:.3f}", "fair_price": "${:,.4f}",
             "price_usd": "${:,.4f}", "upside_%": "{:+.2f}%"}
        ),
        width="stretch",
    )

with tab5:
    st.markdown("### Thông tin Smart Contract Oracle")
    st.info(
        "Kết quả định giá được làm tròn theo 8 chữ số thập phân (uint256) và ghi lên "
        "**Ethereum Sepolia Testnet** thông qua module `src/chain/publisher.py`."
    )
    token_addr = selected_token.get("sepolia_address", "")
    st.code(
        "\n".join(
            [
                f"Contract Address : {CONTRACT_ADDRESS}",
                "Network          : Ethereum Sepolia (chainId 11155111)",
                f"Token Address    : {token_addr}",
                f"Fair Value (USD) : {current_fair:.8f}",
                f"On-chain value   : {int(round(current_fair * 1e8))}  (x 1e8)",
                "Function         : setValuation(address token, uint256 value)",
            ]
        ),
        language="text",
    )
    st.markdown(f"[Xem contract trên Etherscan](https://sepolia.etherscan.io/address/{CONTRACT_ADDRESS})")

with tab6:
    st.dataframe(chart_data.tail(30).style.format("${:,.4f}"), width="stretch")
    st.download_button(
        "⬇️ Tải CSV kết quả định giá",
        chart_data.to_csv().encode("utf-8"),
        file_name=f"valuation_{selected_symbol}.csv",
        mime="text/csv",
    )
