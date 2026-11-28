"""
So sánh kết quả định giá từ mô hình với giá Chainlink Price Feeds (Nam Khánh phụ trách)

- `compare`      : bảng chi tiết theo từng phiên (giữ nguyên API cũ).
- `summarize`    : bảng tóm tắt độ lệch trung bình, tương quan, sai số so với market/oracle.
- `fetch_latest` : đọc giá mới nhất từ Chainlink AggregatorV3 qua Web3 (tùy chọn, cần RPC_URL).
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd

from src.evaluation.metrics import ValuationMetrics

# ABI tối thiểu của AggregatorV3Interface
AGGREGATOR_V3_ABI = [
    {
        "inputs": [],
        "name": "latestRoundData",
        "outputs": [
            {"name": "roundId", "type": "uint80"},
            {"name": "answer", "type": "int256"},
            {"name": "startedAt", "type": "uint256"},
            {"name": "updatedAt", "type": "uint256"},
            {"name": "answeredInRound", "type": "uint80"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function",
    },
]


class ChainlinkComparator:
    @staticmethod
    def compare(model_price: pd.Series, market_price: pd.Series, chainlink_price: pd.Series) -> pd.DataFrame:
        market = market_price.replace(0, np.nan)
        comparison_df = pd.DataFrame(
            {
                "model_fair_price": model_price,
                "market_price": market_price,
                "chainlink_oracle_price": chainlink_price,
                "model_vs_market_diff_%": ((model_price - market) / market) * 100,
                "oracle_vs_market_diff_%": ((chainlink_price - market) / market) * 100,
                "model_vs_oracle_diff_%": ((model_price - chainlink_price) / chainlink_price.replace(0, np.nan))
                * 100,
            }
        )
        return comparison_df

    @staticmethod
    def summarize(model_price: pd.Series, market_price: pd.Series, chainlink_price: pd.Series) -> Dict[str, float]:
        """Các chỉ số tổng hợp phục vụ bảng 5.2 trong báo cáo."""
        cmp = ChainlinkComparator.compare(model_price, market_price, chainlink_price)

        def _corr(a: pd.Series, b: pd.Series) -> float:
            pair = pd.concat([a, b], axis=1).dropna()
            if len(pair) < 2 or pair.iloc[:, 0].std() == 0 or pair.iloc[:, 1].std() == 0:
                return float("nan")
            return float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))

        return {
            "n_obs": int(cmp.dropna(subset=["model_fair_price", "market_price"]).shape[0]),
            "mean_model_vs_market_%": round(float(cmp["model_vs_market_diff_%"].mean()), 3),
            "mean_abs_model_vs_market_%": round(float(cmp["model_vs_market_diff_%"].abs().mean()), 3),
            "mean_oracle_vs_market_%": round(float(cmp["oracle_vs_market_diff_%"].mean()), 3),
            "mean_abs_model_vs_oracle_%": round(float(cmp["model_vs_oracle_diff_%"].abs().mean()), 3),
            "corr_model_market": round(_corr(model_price, market_price), 4),
            "corr_model_oracle": round(_corr(model_price, chainlink_price), 4),
            "corr_oracle_market": round(_corr(chainlink_price, market_price), 4),
            "MAPE_model_vs_market": round(ValuationMetrics.calculate_mape(market_price, model_price), 3),
            "MAPE_model_vs_oracle": round(ValuationMetrics.calculate_mape(chainlink_price, model_price), 3),
        }

    @staticmethod
    def fetch_latest(feed_address: str, rpc_url: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Đọc giá mới nhất từ Chainlink feed (mainnet/Sepolia). Trả về None nếu không kết nối được.
        """
        import os

        rpc_url = rpc_url or os.getenv("RPC_URL") or os.getenv("MAINNET_RPC_URL")
        if not rpc_url:
            return None
        try:
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
            feed = w3.eth.contract(address=Web3.to_checksum_address(feed_address), abi=AGGREGATOR_V3_ABI)
            decimals = feed.functions.decimals().call()
            _, answer, _, updated_at, _ = feed.functions.latestRoundData().call()
            return {"price": answer / 10**decimals, "updated_at": int(updated_at)}
        except Exception as e:  # pragma: no cover - phụ thuộc mạng
            print(f"[Chainlink] Không đọc được feed {feed_address}: {e}")
            return None

    @staticmethod
    def simulate_oracle(market_price: pd.Series, deviation_threshold: float = 0.01, heartbeat: int = 3) -> pd.Series:
        """
        Mô phỏng chuỗi giá Chainlink khi không có dữ liệu lịch sử: oracle chỉ cập nhật khi giá lệch
        quá `deviation_threshold` (mặc định 1%) hoặc sau `heartbeat` phiên không cập nhật.
        """
        values = market_price.astype(float).to_numpy()
        out = np.empty_like(values)
        last, since = values[0], 0
        for i, v in enumerate(values):
            since += 1
            if np.isnan(last) or abs(v - last) / last > deviation_threshold or since >= heartbeat:
                last, since = v, 0
            out[i] = last
        return pd.Series(out, index=market_price.index, name="chainlink_oracle_price")
