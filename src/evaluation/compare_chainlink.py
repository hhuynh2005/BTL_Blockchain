"""
So sánh kết quả định giá từ mô hình với giá Chainlink Price Feeds (Nam Khánh phụ trách)
"""

import pandas as pd
from src.evaluation.metrics import ValuationMetrics


class ChainlinkComparator:
    @staticmethod
    def compare(model_price: pd.Series, market_price: pd.Series, chainlink_price: pd.Series) -> pd.DataFrame:
        comparison_df = pd.DataFrame({
            "model_fair_price": model_price,
            "market_price": market_price,
            "chainlink_oracle_price": chainlink_price,
            "model_vs_market_diff_%": ((model_price - market_price) / market_price) * 100,
            "oracle_vs_market_diff_%": ((chainlink_price - market_price) / market_price) * 100,
        })
        return comparison_df
