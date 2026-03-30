import numpy as np
import pandas as pd

from config import (
    RISK_FREE_RATE,
    VAR_CONFIDENCE,
    TRADING_DAYS,
    ROUND_DECIMALS
)


def risk_report(holdings_dict, historical_prices_df, benchmark_prices_df, starting_capital):
    if historical_prices_df.empty:
        raise ValueError("Historical prices DataFrame is empty.")

    if benchmark_prices_df.empty:
        raise ValueError("Benchmark prices DataFrame is empty.")

    portfolio_tickers = list(holdings_dict.keys())

    portfolio_prices = historical_prices_df[
        historical_prices_df["ticker"].isin(portfolio_tickers)
    ].copy()

    benchmark_prices = benchmark_prices_df.copy()

    if portfolio_prices.empty:
        raise ValueError("No portfolio price data found for selected tickers.")

    price_matrix = portfolio_prices.pivot(
        index="date",
        columns="ticker",
        values="close"
    ).sort_index()

    benchmark_series = benchmark_prices.pivot(
        index="date",
        columns="ticker",
        values="close"
    ).sort_index()

    if benchmark_series.empty:
        raise ValueError("No benchmark close-price data available.")

    benchmark_close = benchmark_series.iloc[:, 0]

    price_matrix = price_matrix.dropna()
    benchmark_close = benchmark_close.dropna()

    if price_matrix.empty or benchmark_close.empty:
        raise ValueError("Price data contains insufficient valid observations.")

    asset_returns = price_matrix.pct_change().dropna()
    benchmark_returns = benchmark_close.pct_change().dropna()

    if asset_returns.empty or benchmark_returns.empty:
        raise ValueError("Return series could not be calculated.")

    weights = np.array([holdings_dict[ticker] for ticker in asset_returns.columns])

    common_index = asset_returns.index.intersection(benchmark_returns.index)
    asset_returns = asset_returns.loc[common_index]
    benchmark_returns = benchmark_returns.loc[common_index]

    if asset_returns.empty or benchmark_returns.empty:
        raise ValueError("Portfolio and benchmark returns do not overlap in time.")

    portfolio_daily_returns = asset_returns.mul(weights, axis=1).sum(axis=1)

    cumulative_return = (1 + portfolio_daily_returns).prod() - 1
    expected_annual_return = portfolio_daily_returns.mean() * TRADING_DAYS
    annualised_volatility = portfolio_daily_returns.std() * np.sqrt(TRADING_DAYS)

    cumulative_curve = (1 + portfolio_daily_returns).cumprod()
    running_max = cumulative_curve.cummax()
    drawdowns = (cumulative_curve / running_max) - 1
    max_drawdown = drawdowns.min()

    historical_var = np.percentile(portfolio_daily_returns, VAR_CONFIDENCE * 100)

    sharpe_ratio = 0.0
    if annualised_volatility != 0:
        sharpe_ratio = (expected_annual_return - RISK_FREE_RATE) / annualised_volatility

    beta = 0.0
    benchmark_variance = benchmark_returns.var()
    if benchmark_variance != 0:
        beta = portfolio_daily_returns.cov(benchmark_returns) / benchmark_variance

    correlation_matrix = asset_returns.corr()

    asset_volatility = asset_returns.std() * np.sqrt(TRADING_DAYS)
    raw_risk_contribution = weights * asset_volatility.values
    total_contribution = raw_risk_contribution.sum()

    if total_contribution != 0:
        risk_contribution = {
        ticker: float(round(value / total_contribution, ROUND_DECIMALS))
        for ticker, value in zip(asset_returns.columns, raw_risk_contribution)
    }
    else:
        risk_contribution = {
        ticker: 0.0 for ticker in asset_returns.columns
    }

    allocations = {
        ticker: round(weight * starting_capital, 2)
        for ticker, weight in holdings_dict.items()
    }

    best_day_return = portfolio_daily_returns.max()
    worst_day_return = portfolio_daily_returns.min()

    report = {
        "starting_capital": starting_capital,
        "weights": {ticker: round(weight, ROUND_DECIMALS) for ticker, weight in holdings_dict.items()},
        "allocations": allocations,
        "cumulative_return": round(cumulative_return, ROUND_DECIMALS),
        "expected_annual_return": round(expected_annual_return, ROUND_DECIMALS),
        "annualised_volatility": round(annualised_volatility, ROUND_DECIMALS),
        "max_drawdown": round(max_drawdown, ROUND_DECIMALS),
        "historical_var_5pct": round(historical_var, ROUND_DECIMALS),
        "sharpe_ratio": round(sharpe_ratio, ROUND_DECIMALS),
        "beta_vs_benchmark": round(beta, ROUND_DECIMALS),
        "best_day_return": round(best_day_return, ROUND_DECIMALS),
        "worst_day_return": round(worst_day_return, ROUND_DECIMALS),
        "correlation_matrix": correlation_matrix.round(ROUND_DECIMALS).to_dict(),
        "risk_contribution": risk_contribution
    }

    return report