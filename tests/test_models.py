"""
Unit test kiểm thử các mô hình định giá token (Kha & Huỳnh)
"""

import pytest
import pandas as pd
import numpy as np
from src.models import (
    NVTValuationModel,
    MVPQValuationModel,
    TWAPValuationModel,
    ComparableValuationModel,
    EnsembleValuationModel,
)


@pytest.fixture
def sample_market_data():
    dates = pd.date_range("2026-01-01", periods=30, freq="D")
    df = pd.DataFrame(
        {
            "date": dates,
            "token": ["UNI"] * 30,
            "price_usd": [10.0 + i * 0.1 for i in range(30)],
            "volume_24h": [50_000_000.0] * 30,
            "market_cap": [1_000_000_000.0] * 30,
            "circulating_supply": [100_000_000.0] * 30,
            "tvl": [800_000_000.0] * 30,
            "tx_count": [15000] * 30,
            "active_addresses": [5000] * 30,
            "onchain_volume_usd": [40_000_000.0] * 30,
            "pool_reserve0": [500_000.0] * 30,
            "pool_reserve1": [5_000_000.0] * 30,
        }
    )
    return df


def test_nvt_model_fit_and_predict(sample_market_data):
    model = NVTValuationModel()
    model.fit(sample_market_data)
    assert model.is_fitted
    preds = model.predict(sample_market_data)
    assert len(preds) == len(sample_market_data)
    assert (preds > 0).all()


def test_mvpq_model(sample_market_data):
    model = MVPQValuationModel()
    model.fit(sample_market_data)
    assert model.is_fitted
    preds = model.predict(sample_market_data)
    assert len(preds) == len(sample_market_data)
    assert (preds > 0).all()


def test_twap_model(sample_market_data):
    model = TWAPValuationModel(window=5)
    model.fit(sample_market_data)
    assert model.is_fitted
    preds = model.predict(sample_market_data)
    assert len(preds) == len(sample_market_data)
    assert (preds > 0).all()


def test_comparable_model(sample_market_data):
    model = ComparableValuationModel()
    model.fit(sample_market_data)
    assert model.is_fitted
    preds = model.predict(sample_market_data)
    assert len(preds) == len(sample_market_data)
    assert (preds > 0).all()


def test_ensemble_model(sample_market_data):
    m1 = NVTValuationModel()
    m2 = MVPQValuationModel()
    m3 = TWAPValuationModel()
    m4 = ComparableValuationModel()
    ensemble = EnsembleValuationModel([m1, m2, m3, m4])
    ensemble.fit(sample_market_data)
    assert ensemble.is_fitted
    preds = ensemble.predict(sample_market_data)
    assert len(preds) == len(sample_market_data)
    assert (preds > 0).all()
