"""
Thu thập các chỉ số on-chain (totalSupply, tx_count, active_addresses) qua RPC/Etherscan (Kha phụ trách)
"""

import requests
import pandas as pd


class OnchainCollector:
    def __init__(self, etherscan_api_key: str = None, rpc_url: str = None):
        self.api_key = etherscan_api_key
        self.rpc_url = rpc_url

    def get_token_supply(self, token_address: str, decimals: int = 18) -> float:
        """
        Lấy totalSupply của ERC-20 token và quy đổi theo số chữ số thập phân.
        """
        return 1_000_000_000.0  # Placeholder khởi tạo

    def get_daily_tx_and_active_addresses(self, token_address: str) -> dict:
        """
        Thống kê số lượng giao dịch và số ví hoạt động hàng ngày.
        """
        return {
            "tx_count": 12500,
            "active_addresses": 4800,
            "onchain_volume_usd": 150_000_000.0,
        }
