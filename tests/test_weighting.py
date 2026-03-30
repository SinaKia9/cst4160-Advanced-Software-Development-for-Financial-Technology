import pandas as pd
import pytest

from core.weighting import (
    equal_weighting,
    momentum_weighting,
    inverse_volatility_weighting
)


def make_price_data():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")

    data = []

    for i, date in enumerate(dates):
        data.append({"ticker": "AAPL", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 1.0})
        data.append({"ticker": "MSFT", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 0.8})
        data.append({"ticker": "NVDA", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 1.2})

    return pd.DataFrame(data)


def test_equal_weighting():
    tickers = ["AAPL", "MSFT", "NVDA"]
    weights = equal_weighting(tickers)

    assert isinstance(weights, dict)
    assert len(weights) == 3
    assert sum(weights.values()) == pytest.approx(1.0, rel=1e-6)


def test_momentum_weighting():
    price_df = make_price_data()
    tickers = ["AAPL", "MSFT", "NVDA"]

    weights = momentum_weighting(price_df, tickers, strategy_type="combined")

    assert isinstance(weights, dict)
    assert len(weights) == 3
    assert sum(weights.values()) == pytest.approx(1.0, rel=1e-6)


def test_inverse_volatility_weighting():
    price_df = make_price_data()
    tickers = ["AAPL", "MSFT", "NVDA"]

    weights = inverse_volatility_weighting(price_df, tickers)

    assert isinstance(weights, dict)
    assert len(weights) == 3
    assert sum(weights.values()) == pytest.approx(1.0, rel=1e-6)


def test_empty_price_df_raises_error():
    with pytest.raises(ValueError):
        inverse_volatility_weighting(pd.DataFrame(), ["AAPL"])