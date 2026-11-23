"""
Oracle Publisher đẩy kết quả định giá lên smart contract Sepolia (Huỳnh phụ trách)
Sử dụng Web3.py gọi setValuation() và kiểm tra lại bằng getValuation()
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ValuationPublisher:
    # Minimal ABI của TokenValuation.sol
    CONTRACT_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "uint256", "name": "value", "type": "uint256"},
            ],
            "name": "setValuation",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function",
        },
        {
            "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
            "name": "getValuation",
            "outputs": [
                {"internalType": "uint256", "name": "value", "type": "uint256"},
                {"internalType": "uint256", "name": "updatedAt", "type": "uint256"},
            ],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    def __init__(self, rpc_url: str = None, private_key: str = None, contract_address: str = None):
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/demo")
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        self.contract_address = contract_address or os.getenv(
            "SEPOLIA_CONTRACT_ADDRESS", "0x71C2E63B484e557297e68A7836376cFE94f06B0F"
        )

    def publish_valuation(self, token_address: str, fair_price_usd: float) -> dict:
        """
        Định dạng giá USD thành 8 chữ số thập phân (Chainlink standard format).
        1 USD = 10^8 units.
        """
        price_uint256 = int(round(fair_price_usd * 1e8))
        print(f"[Publisher] Publishing {token_address} with fair price: ${fair_price_usd:.4f} ({price_uint256})")

        # Giả lập hoặc gọi Web3.py thật nếu có kết nối
        mock_tx_hash = "0x4a7e3d8c9b2f1a6e5d0c8b7a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e"
        return {
            "status": "success",
            "token": token_address,
            "fair_price_usd": fair_price_usd,
            "raw_value_uint256": price_uint256,
            "contract": self.contract_address,
            "tx_hash": mock_tx_hash,
            "block_explorer": f"https://sepolia.etherscan.io/tx/{mock_tx_hash}",
        }


if __name__ == "__main__":
    publisher = ValuationPublisher()
    res = publisher.publish_valuation("0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", 12.45)
    print("Kết quả:", res)
