import pandas as pd

from config import (
    MOMENTUM_LOOKBACK_SHORT,
    MOMENTUM_LOOKBACK_MEDIUM,
    MOMENTUM_LOOKBACK_LONG,
    TOP_N_SELECTION
)


def calculate_momentum_scores(price_df):
    if price_df.empty:
        raise ValueError("Price DataFrame is empty.")

    price_matrix = price_df.pivot(index="date", columns="ticker", values="close").sort_index()

    if len(price_matrix) < MOMENTUM_LOOKBACK_LONG:
        raise ValueError("Not enough historical data to calculate 90-day momentum.")

    latest_prices = price_matrix.iloc[-1]
    momentum_30 = (latest_prices / price_matrix.iloc[-MOMENTUM_LOOKBACK_SHORT]) - 1
    momentum_60 = (latest_prices / price_matrix.iloc[-MOMENTUM_LOOKBACK_MEDIUM]) - 1
    momentum_90 = (latest_prices / price_matrix.iloc[-MOMENTUM_LOOKBACK_LONG]) - 1

    scores_df = pd.DataFrame({
        "30_day": momentum_30,
        "60_day": momentum_60,
        "90_day": momentum_90
    })

    scores_df["combined"] = (
        0.3 * scores_df["30_day"] +
        0.3 * scores_df["60_day"] +
        0.4 * scores_df["90_day"]
    )

    return scores_df.sort_index()


def select_top_momentum_tickers(price_df, strategy_type="combined", top_n=TOP_N_SELECTION):
    scores_df = calculate_momentum_scores(price_df)

    valid_strategies = ["30_day", "60_day", "90_day", "combined"]
    if strategy_type not in valid_strategies:
        raise ValueError(f"Invalid strategy_type. Choose from: {', '.join(valid_strategies)}")

    ranked = scores_df.sort_values(by=strategy_type, ascending=False)

    return ranked.head(top_n).index.tolist()