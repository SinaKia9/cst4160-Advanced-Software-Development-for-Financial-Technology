import pandas as pd
import pytest

from core.strategy import calculate_momentum_scores, select_top_momentum_tickers


def make_price_data():
    dates = pd.date_range("2024-01-01", periods=100, freq="D")

    data = []

    for i, date in enumerate(dates):
        data.append({"ticker": "AAPL", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 1.0})
        data.append({"ticker": "MSFT", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 0.8})
        data.append({"ticker": "NVDA", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 1.2})
        data.append({"ticker": "JPM", "date": date.strftime("%Y-%m-%d"), "close": 100 + i * 0.3})

    return pd.DataFrame(data)


def test_calculate_momentum_scores_success():
    price_df = make_price_data()
    scores_df = calculate_momentum_scores(price_df)

    assert isinstance(scores_df, pd.DataFrame)
    assert "30_day" in scores_df.columns
    assert "60_day" in scores_df.columns
    assert "90_day" in scores_df.columns
    assert "combined" in scores_df.columns

    assert "AAPL" in scores_df.index
    assert "MSFT" in scores_df.index
    assert "NVDA" in scores_df.index
    assert "JPM" in scores_df.index


def test_select_top_momentum_tickers_success():
    price_df = make_price_data()
    top_tickers = select_top_momentum_tickers(price_df, strategy_type="combined", top_n=2)

    assert isinstance(top_tickers, list)
    assert len(top_tickers) == 2
    assert "NVDA" in top_tickers


def test_invalid_strategy_type_raises_error():
    price_df = make_price_data()

    with pytest.raises(ValueError):
        select_top_momentum_tickers(price_df, strategy_type="invalid_type", top_n=2)


def test_empty_price_df_raises_error():
    with pytest.raises(ValueError):
        calculate_momentum_scores(pd.DataFrame())