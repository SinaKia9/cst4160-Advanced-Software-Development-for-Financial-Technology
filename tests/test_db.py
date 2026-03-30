import os
import sqlite3
from data.db import (
    init_db,
    create_portfolio,
    save_holdings,
    load_portfolio,
    list_portfolios,
    save_report
)
from config import DB_PATH


def setup_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


def teardown_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def test_create_portfolio():
    portfolio_id = create_portfolio("TestPortfolio")
    assert isinstance(portfolio_id, int)


def test_save_and_load_holdings():
    portfolio_id = create_portfolio("GrowthPortfolio")
    holdings = {"AAPL": 0.4, "MSFT": 0.3, "NVDA": 0.3}

    save_holdings(portfolio_id, holdings)
    loaded_holdings = load_portfolio("GrowthPortfolio")

    assert loaded_holdings == holdings


def test_list_portfolios():
    create_portfolio("PortfolioOne")
    create_portfolio("PortfolioTwo")

    portfolios = list_portfolios()

    assert "PortfolioOne" in portfolios
    assert "PortfolioTwo" in portfolios


def test_save_report():
    portfolio_id = create_portfolio("RiskPortfolio")
    report = {
        "annualised_volatility": 0.25,
        "sharpe_ratio": 1.1
    }

    save_report(portfolio_id, report)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT json_summary FROM reports WHERE portfolio_id = ?", (portfolio_id,))
    result = cursor.fetchone()
    conn.close()

    assert result is not None