from config import MIN_TICKERS, MAX_TICKERS, MAX_ASSET_WEIGHT
from core.universe import UNIVERSE_TICKERS


def build_portfolio(tickers, weights=None, mode="equal"):
    unique_tickers = list(dict.fromkeys([ticker.upper() for ticker in tickers]))

    if len(unique_tickers) < MIN_TICKERS:
        raise ValueError(f"Portfolio must contain at least {MIN_TICKERS} tickers.")

    if len(unique_tickers) > MAX_TICKERS:
        raise ValueError(f"Portfolio must contain no more than {MAX_TICKERS} tickers.")

    invalid_tickers = [ticker for ticker in unique_tickers if ticker not in UNIVERSE_TICKERS]
    if invalid_tickers:
        raise ValueError(f"Invalid tickers: {', '.join(invalid_tickers)}")

    if mode == "equal":
        weight = 1 / len(unique_tickers)
        holdings = {ticker: weight for ticker in unique_tickers}
    else:
        if weights is None:
            raise ValueError("Weights must be provided for custom mode.")

        if len(weights) != len(unique_tickers):
            raise ValueError("Number of weights must match number of tickers.")

        if any(weight < 0 for weight in weights):
            raise ValueError("Weights cannot be negative.")

        if round(sum(weights), 6) != 1.0:
            raise ValueError("Weights must sum to 1.")

        holdings = dict(zip(unique_tickers, weights))

    for ticker, weight in holdings.items():
        if weight > MAX_ASSET_WEIGHT:
            raise ValueError(f"{ticker} exceeds maximum allowed weight of {MAX_ASSET_WEIGHT}.")

    return holdings