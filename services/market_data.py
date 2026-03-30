from datetime import datetime, timedelta
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from config import ALPACA_API_KEY, ALPACA_API_SECRET, ALPACA_DATA_FEED


def fetch_historical_bars(tickers, days):
    client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_API_SECRET)

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    request = StockBarsRequest(
        symbol_or_symbols=tickers,
        timeframe=TimeFrame.Day,
        start=start_date,
        end=end_date,
        feed=ALPACA_DATA_FEED
    )

    bars = client.get_stock_bars(request).df

    if bars.empty:
        raise ValueError("No historical data returned from Alpaca API.")

    bars = bars.reset_index()

    if "symbol" in bars.columns:
        bars = bars.rename(columns={"symbol": "ticker"})

    if "timestamp" in bars.columns:
        bars["date"] = pd.to_datetime(bars["timestamp"]).dt.strftime("%Y-%m-%d")
    else:
        raise ValueError("Timestamp column missing from Alpaca response.")

    required_columns = ["ticker", "date", "open", "high", "low", "close", "volume"]
    bars = bars[required_columns]

    return bars