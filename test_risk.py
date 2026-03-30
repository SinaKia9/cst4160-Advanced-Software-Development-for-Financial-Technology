import pandas as pd
import pytest

from core.risk import risk_report
from config import STARTING_CAPITAL


def test_risk_report_success():
    holdings = {
        "AAPL": 0.4,
        "MSFT": 0.3,
        "NVDA": 0.3
    }

    historical_prices_df = pd.DataFrame({
        "ticker": [
            "AAPL", "AAPL", "AAPL", "AAPL",
            "MSFT", "MSFT", "MSFT", "MSFT",
            "NVDA", "NVDA", "NVDA", "NVDA"
        ],
        "date": [
            "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04",
            "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04",
            "2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"
        ],
        "close": [
            100, 102, 101, 103,
            200, 202, 201, 205,
            300, 303, 302, 306
        ]
    })

    benchmark_prices_df = pd.DataFrame({
        "ticker": ["SPY", "SPY", "SPY", "SPY"],
        "date": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
        "close": [400, 402, 401, 404]
    })

    report = risk_report(holdings, historical_prices_df, benchmark_prices_df, STARTING_CAPITAL)

    assert isinstance(report, dict)

    assert "starting_capital" in report
    assert "weights" in report
    assert "allocations" in report
    assert "cumulative_return" in report
    assert "expected_annual_return" in report
    assert "annualised_volatility" in report
    assert "max_drawdown" in report
    assert "historical_var_5pct" in report
    assert "sharpe_ratio" in report
    assert "beta_vs_benchmark" in report
    assert "best_day_return" in report
    assert "worst_day_return" in report
    assert "correlation_matrix" in report
    assert "risk_contribution" in report

    assert report["starting_capital"] == STARTING_CAPITAL
    assert report["allocations"]["AAPL"] == round(0.4 * STARTING_CAPITAL, 2)
    assert report["allocations"]["MSFT"] == round(0.3 * STARTING_CAPITAL, 2)
    assert report["allocations"]["NVDA"] == round(0.3 * STARTING_CAPITAL, 2)

    assert "AAPL" in report["correlation_matrix"]
    assert "MSFT" in report["correlation_matrix"]
    assert "NVDA" in report["correlation_matrix"]

    assert "AAPL" in report["risk_contribution"]
    assert "MSFT" in report["risk_contribution"]
    assert "NVDA" in report["risk_contribution"]


def test_risk_report_empty_historical_prices():
    holdings = {"AAPL": 0.5, "MSFT": 0.5}
    historical_prices_df = pd.DataFrame()
    benchmark_prices_df = pd.DataFrame({
        "ticker": ["SPY", "SPY"],
        "date": ["2024-01-01", "2024-01-02"],
        "close": [400, 401]
    })

    with pytest.raises(ValueError):
        risk_report(holdings, historical_prices_df, benchmark_prices_df, STARTING_CAPITAL)


def test_risk_report_empty_benchmark_prices():
    holdings = {"AAPL": 0.5, "MSFT": 0.5}
    historical_prices_df = pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
        "date": ["2024-01-01", "2024-01-02", "2024-01-01", "2024-01-02"],
        "close": [100, 101, 200, 201]
    })
    benchmark_prices_df = pd.DataFrame()

    with pytest.raises(ValueError):
        risk_report(holdings, historical_prices_df, benchmark_prices_df, STARTING_CAPITAL)