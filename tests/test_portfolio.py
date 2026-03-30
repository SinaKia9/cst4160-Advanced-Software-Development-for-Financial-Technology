import pytest
from core.portfolio import build_portfolio


def test_equal_weight_portfolio():
    tickers = ["AAPL", "MSFT", "NVDA"]
    portfolio = build_portfolio(tickers, mode="equal")

    assert len(portfolio) == 3
    assert portfolio["AAPL"] == pytest.approx(1 / 3)
    assert portfolio["MSFT"] == pytest.approx(1 / 3)
    assert portfolio["NVDA"] == pytest.approx(1 / 3)


def test_duplicate_tickers_removed():
    tickers = ["AAPL", "MSFT", "AAPL", "NVDA"]
    portfolio = build_portfolio(tickers, mode="equal")

    assert len(portfolio) == 3
    assert "AAPL" in portfolio
    assert "MSFT" in portfolio
    assert "NVDA" in portfolio


def test_lowercase_tickers_converted_to_uppercase():
    tickers = ["aapl", "msft", "nvda"]
    portfolio = build_portfolio(tickers, mode="equal")

    assert "AAPL" in portfolio
    assert "MSFT" in portfolio
    assert "NVDA" in portfolio


def test_too_few_tickers_raises_error():
    with pytest.raises(ValueError):
        build_portfolio(["AAPL", "MSFT"], mode="equal")


def test_too_many_tickers_raises_error():
    with pytest.raises(ValueError):
        build_portfolio(
            ["AAPL", "MSFT", "NVDA", "JPM", "BAC", "GS", "META", "AMZN"],
            mode="equal"
        )


def test_invalid_ticker_raises_error():
    with pytest.raises(ValueError):
        build_portfolio(["AAPL", "MSFT", "FAKE"], mode="equal")


def test_custom_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        build_portfolio(
            ["AAPL", "MSFT", "NVDA"],
            weights=[0.5, 0.3, 0.1],
            mode="custom"
        )


def test_weight_above_max_raises_error():
    with pytest.raises(ValueError):
        build_portfolio(
            ["AAPL", "MSFT", "NVDA"],
            weights=[0.5, 0.3, 0.2],
            mode="custom"
        )