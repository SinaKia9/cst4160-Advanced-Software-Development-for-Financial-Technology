import numpy as np
import pandas as pd

from core.strategy import calculate_momentum_scores


def equal_weighting(tickers):
    if not tickers:
        raise ValueError("Ticker list is empty.")

    weight = 1 / len(tickers)
    return {ticker: weight for ticker in tickers}


def momentum_weighting(price_df, tickers, strategy_type="combined"):
    if price_df.empty:
        raise ValueError("Price DataFrame is empty.")

    scores_df = calculate_momentum_scores(price_df)

    valid_strategies = ["30_day", "60_day", "90_day", "combined"]
    if strategy_type not in valid_strategies:
        raise ValueError(f"Invalid strategy_type. Choose from: {', '.join(valid_strategies)}")

    selected_scores = scores_df.loc[tickers, strategy_type].copy()

    min_score = selected_scores.min()
    if min_score <= 0:
        selected_scores = selected_scores - min_score + 0.0001

    total_score = selected_scores.sum()
    if total_score == 0:
        raise ValueError("Momentum scores could not produce valid weights.")

    weights = selected_scores / total_score
    return {ticker: round(weight, 6) for ticker, weight in weights.items()}


def inverse_volatility_weighting(price_df, tickers):
    if price_df.empty:
        raise ValueError("Price DataFrame is empty.")

    filtered_df = price_df[price_df["ticker"].isin(tickers)].copy()

    price_matrix = filtered_df.pivot(index="date", columns="ticker", values="close").sort_index()
    returns = price_matrix.pct_change().dropna()

    if returns.empty:
        raise ValueError("Not enough return data to calculate inverse volatility weights.")

    vol = returns.std()

    if (vol == 0).any():
        raise ValueError("At least one ticker has zero volatility.")

    inv_vol = 1 / vol
    weights = inv_vol / inv_vol.sum()

    return {ticker: round(weight, 6) for ticker, weight in weights.items()}