import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from services.market_data import fetch_historical_bars


@patch("services.market_data.StockHistoricalDataClient")
def test_fetch_historical_bars_success(mock_client_class):
    mock_df = pd.DataFrame({
        "symbol": ["AAPL", "AAPL", "MSFT", "MSFT"],
        "timestamp": pd.to_datetime([
            "2024-01-01", "2024-01-02",
            "2024-01-01", "2024-01-02"
        ]),
        "open": [100, 101, 200, 201],
        "high": [102, 103, 202, 203],
        "low": [99, 100, 199, 200],
        "close": [101, 102, 201, 202],
        "volume": [1000, 1100, 2000, 2100]
    })

    mock_response = MagicMock()
    mock_response.df = mock_df

    mock_client = MagicMock()
    mock_client.get_stock_bars.return_value = mock_response
    mock_client_class.return_value = mock_client

    result = fetch_historical_bars(["AAPL", "MSFT"], 30)

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert list(result.columns) == ["ticker", "date", "open", "high", "low", "close", "volume"]
    assert "AAPL" in result["ticker"].values
    assert "MSFT" in result["ticker"].values


@patch("services.market_data.StockHistoricalDataClient")
def test_fetch_historical_bars_empty_response(mock_client_class):
    mock_response = MagicMock()
    mock_response.df = pd.DataFrame()

    mock_client = MagicMock()
    mock_client.get_stock_bars.return_value = mock_response
    mock_client_class.return_value = mock_client

    with pytest.raises(ValueError):
        fetch_historical_bars(["AAPL"], 30)