"""
Thu thập số dư dự trữ (reserves) và giá AMM từ Uniswap V2/V3 Pool (Kha phụ trách)
"""

import pandas as pd


class UniswapCollector:
    def __init__(self, rpc_url: str = None):
        self.rpc_url = rpc_url

    def get_pool_reserves(self, pool_address: str) -> dict:
        """
        Truy vấn hàm getReserves() của UniswapV2Pair.
        Trả về dict gồm: reserve0, reserve1, block_timestamp_last.
        """
        # Skeleton / fallback nếu chưa kết nối RPC on-chain
        return {
            "pool_address": pool_address,
            "reserve0": 1000000.0,
            "reserve1": 1000.0,
            "implied_price": 1000.0 / 1000000.0,
        }
