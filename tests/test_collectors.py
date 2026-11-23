"""
Unit test kiểm thử các module thu thập dữ liệu (Kha)
"""

import pytest
from src.collectors import (
    CoinGeckoCollector,
    DefiLlamaCollector,
    UniswapCollector,
    OnchainCollector,
)


def test_coingecko_collector_init():
    collector = CoinGeckoCollector()
    assert collector.cache_dir is not None


def test_defillama_collector_init():
    collector = DefiLlamaCollector()
    assert collector.cache_dir is not None


def test_uniswap_collector_reserves():
    collector = UniswapCollector()
    res = collector.get_pool_reserves("0x1d42064fc4beb5f8aaf85f4617ae8b3b5b8bd801")
    assert "reserve0" in res
    assert "reserve1" in res
    assert res["implied_price"] > 0


def test_onchain_collector():
    collector = OnchainCollector()
    stats = collector.get_daily_tx_and_active_addresses("0x1f9840a85d5af5bf1d1762f925bdaddc4201f984")
    assert stats["tx_count"] > 0
    assert stats["active_addresses"] > 0
