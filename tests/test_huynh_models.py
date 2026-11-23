"""
================================================================================
UNIT TESTS: tests/test_huynh_models.py
TÁC GIẢ: Huỳnh (Trưởng nhóm - Nhánh feature/models)
MỤC ĐÍCH:
  Kiểm thử toàn diện các module do Huỳnh phụ trách:
    - Base Class ValuationModel & validation, parameter checkpointing
    - NVT Ratio & Luật Metcalfe (NVTValuationModel)
    - Mô hình Ensemble kết hợp và tối ưu hóa trọng số (EnsembleValuationModel)
    - Oracle Publisher tương tác Smart Contract Sepolia (ValuationPublisher)
================================================================================
"""

import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from src.models.base import ValuationModel
from src.models.nvt import NVTValuationModel
from src.models.mv_pq import MVPQValuationModel
from src.models.twap import TWAPValuationModel
from src.models.comparable import ComparableValuationModel
from src.models.ensemble import EnsembleValuationModel
from src.chain.publisher import ValuationPublisher


@pytest.fixture
def sample_dataset():
    """Tạo bộ dữ liệu chuỗi thời gian 60 ngày cho token UNI phục vụ kiểm thử."""
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    np.random.seed(42)
    base_price = 10.0
    trend = np.linspace(0, 2.0, 60) + np.random.normal(0, 0.2, 60)
    prices = base_price + trend
    volume = 50_000_000.0 + np.random.normal(0, 5_000_000.0, 60)
    supply = 100_000_000.0
    mc = prices * supply

    df = pd.DataFrame(
        {
            "date": dates,
            "token": ["UNI"] * 60,
            "price_usd": prices,
            "volume_24h": volume,
            "onchain_volume_usd": volume * 0.8,
            "market_cap": mc,
            "circulating_supply": [supply] * 60,
            "tvl": [800_000_000.0] * 60,
            "tx_count": np.random.randint(10000, 15000, 60),
            "active_addresses": np.random.randint(3500, 6000, 60),
            "pool_reserve0": [500_000.0] * 60,
            "pool_reserve1": prices * 500_000.0,
        }
    )
    return df


# ==============================================================================
# 1. KIỂM THỬ BASE CLASS
# ==============================================================================

def test_base_model_validation(sample_dataset):
    model = NVTValuationModel()
    # Kiểm tra thiếu cột
    with pytest.raises(ValueError, match="Dữ liệu đầu vào thiếu các cột bắt buộc"):
        model.validate_input(pd.DataFrame({"col_a": [1, 2]}), ["market_cap", "missing_col"])


def test_base_model_save_and_load_params(sample_dataset):
    model = NVTValuationModel(rolling_window=30)
    model.fit(sample_dataset)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        model.save_params(tmp_path)
        new_model = NVTValuationModel()
        new_model.load_params(tmp_path)
        assert new_model.is_fitted
        assert new_model.params["rolling_window"] == 30
        assert "nvt_benchmark" in new_model.params
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ==============================================================================
# 2. KIỂM THỬ NVT & METCALFE MODEL
# ==============================================================================

def test_nvt_model_variants(sample_dataset):
    model = NVTValuationModel(rolling_window=30, metcalfe_weight=0.4)
    model.fit(sample_dataset)

    assert model.is_fitted
    assert model.nvt_benchmark is not None and model.nvt_benchmark > 0
    assert model.metcalfe_alpha is not None and model.metcalfe_alpha > 0

    p_nvt_only = model.predict_nvt_only(sample_dataset)
    assert len(p_nvt_only) == len(sample_dataset)
    assert (p_nvt_only > 0).all()

    p_metcalfe_only = model.predict_metcalfe_only(sample_dataset)
    assert len(p_metcalfe_only) == len(sample_dataset)
    assert (p_metcalfe_only > 0).all()

    p_blended = model.predict(sample_dataset)
    assert len(p_blended) == len(sample_dataset)
    assert (p_blended > 0).all()

    # Kiểm tra sai số mô hình
    metrics = model.evaluate(sample_dataset)
    assert "MAE" in metrics and metrics["MAE"] >= 0
    assert "RMSE" in metrics and metrics["RMSE"] >= 0
    assert "MAPE" in metrics and metrics["MAPE"] >= 0


# ==============================================================================
# 3. KIỂM THỬ ENSEMBLE MODEL VÀ TỐI ƯU HÓA TRỌNG SỐ
# ==============================================================================

def test_ensemble_optimization(sample_dataset):
    m1 = NVTValuationModel(rolling_window=30)
    m2 = MVPQValuationModel()
    m3 = TWAPValuationModel(window=7)
    m4 = ComparableValuationModel()

    ensemble = EnsembleValuationModel([m1, m2, m3, m4], loss_metric="MAE")
    ensemble.fit(sample_dataset, target_col="price_usd", optimize_weights=True)

    assert ensemble.is_fitted
    weights = ensemble.weights

    # Kiểm tra ràng buộc trọng số: sum(w) == 1.0 và w >= 0
    total_w = sum(weights.values())
    assert pytest.approx(total_w, abs=1e-3) == 1.0
    for name, w in weights.items():
        assert w >= 0.0

    preds = ensemble.predict(sample_dataset)
    assert len(preds) == len(sample_dataset)
    assert (preds > 0).all()

    # Kiểm tra tính toán sai số của Ensemble
    metrics = ensemble.evaluate(sample_dataset)
    assert metrics["MAPE"] < 25.0  # Sai số Ensemble trên tập fit phải hợp lý


def test_ensemble_load_yaml_weights():
    m1 = NVTValuationModel()
    m2 = MVPQValuationModel()
    m3 = TWAPValuationModel()
    m4 = ComparableValuationModel()

    ensemble = EnsembleValuationModel([m1, m2, m3, m4])
    ensemble.load_weights_from_yaml(config_path="config/weights.yaml", sector="DEX")

    # DEX ưu tiên TWAP và TVL
    assert "Uniswap_TWAP" in ensemble.weights
    assert sum(ensemble.weights.values()) == pytest.approx(1.0, abs=1e-3)


# ==============================================================================
# 4. KIỂM THỬ ORACLE PUBLISHER
# ==============================================================================

def test_publisher_format_conversions():
    publisher = ValuationPublisher(dry_run=True)
    raw_val = publisher.format_fair_price_to_uint256(12.3456)
    assert raw_val == 1234560000
    converted_usd = publisher.format_uint256_to_usd(raw_val)
    assert pytest.approx(converted_usd, 1e-4) == 12.3456


def test_publisher_single_and_batch_execution():
    publisher = ValuationPublisher(dry_run=True)
    token_a = "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984"
    res_single = publisher.publish_single_valuation(token_a, 10.75)

    assert res_single["status"] == "success"
    assert res_single["token"] == token_a
    assert res_single["fair_price_usd"] == 10.75
    assert res_single["tx_hash"].startswith("0x")
    assert "sepolia.etherscan.io" in res_single["block_explorer"]

    tokens = [token_a, "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9"]
    prices = [10.75, 88.50]
    res_batch = publisher.publish_batch_valuations(tokens, prices)
    assert res_batch["status"] == "success"
    assert res_batch["total_published"] == 2
