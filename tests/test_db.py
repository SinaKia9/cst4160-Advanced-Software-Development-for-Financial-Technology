import os
from data.db import (
    init_db,
    create_user,
    get_user_by_username,
    get_user_by_email,
    save_verification_code,
    verify_user_email,
    save_reset_code,
    update_user_password,
    create_portfolio,
    save_holdings,
    load_portfolio,
    list_portfolios,
    save_report,
    get_portfolio_id
)
from config import DB_PATH


def setup_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()


def teardown_function():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


def test_create_user_and_get_by_username():
    user_id = create_user("john", "john@example.com", "hashed_password_123")
    user = get_user_by_username("john")

    assert isinstance(user_id, int)
    assert user is not None
    assert user[1] == "john"
    assert user[2] == "john@example.com"
    assert user[4] == 0


def test_get_user_by_email():
    create_user("mark", "mark@example.com", "hashed_password_456")
    user = get_user_by_email("mark@example.com")

    assert user is not None
    assert user[1] == "mark"


def test_save_and_verify_email_code():
    create_user("tim", "tim@example.com", "old_hash")
    save_verification_code("tim@example.com", "123456", "2026-12-31 12:00:00")

    user = get_user_by_email("tim@example.com")
    assert user[5] == "123456"
    assert user[6] == "2026-12-31 12:00:00"

    verify_user_email("tim@example.com")
    user = get_user_by_email("tim@example.com")

    assert user[4] == 1
    assert user[5] is None
    assert user[6] is None


def test_save_reset_code():
    create_user("david", "david@example.com", "old_hash")
    save_reset_code("david@example.com", "654321", "2026-12-31 12:00:00")

    user = get_user_by_email("david@example.com")
    assert user[7] == "654321"
    assert user[8] == "2026-12-31 12:00:00"


def test_update_user_password():
    create_user("tom", "tom@example.com", "old_hash")
    save_reset_code("tom@example.com", "111111", "2026-12-31 12:00:00")

    update_user_password("tom@example.com", "new_hash")
    user = get_user_by_email("tom@example.com")

    assert user[3] == "new_hash"
    assert user[7] is None
    assert user[8] is None


def test_create_portfolio_save_and_load_holdings():
    user_id = create_user("john", "john@example.com", "hashed_password")
    portfolio_id = create_portfolio(user_id, "GrowthPortfolio")

    holdings = {"AAPL": 0.4, "MSFT": 0.3, "NVDA": 0.3}
    save_holdings(portfolio_id, holdings)

    loaded_holdings = load_portfolio(user_id, "GrowthPortfolio")
    assert loaded_holdings == holdings


def test_list_portfolios_for_user():
    user1_id = create_user("john", "john@example.com", "hash1")
    user2_id = create_user("mark", "mark@example.com", "hash2")

    create_portfolio(user1_id, "PortfolioOne")
    create_portfolio(user1_id, "PortfolioTwo")
    create_portfolio(user2_id, "OtherPortfolio")

    portfolios_user1 = list_portfolios(user1_id)
    portfolios_user2 = list_portfolios(user2_id)

    assert "PortfolioOne" in portfolios_user1
    assert "PortfolioTwo" in portfolios_user1
    assert "OtherPortfolio" not in portfolios_user1
    assert portfolios_user2 == ["OtherPortfolio"]


def test_get_portfolio_id():
    user_id = create_user("tim", "tim@example.com", "hashed_password")
    created_id = create_portfolio(user_id, "MyPortfolio")
    fetched_id = get_portfolio_id(user_id, "MyPortfolio")

    assert created_id == fetched_id


def test_save_report():
    user_id = create_user("mark", "mark@example.com", "hashed_password")
    portfolio_id = create_portfolio(user_id, "RiskPortfolio")

    report = {
        "annualised_volatility": 0.25,
        "sharpe_ratio": 1.1
    }

    save_report(portfolio_id, report)
    fetched_id = get_portfolio_id(user_id, "RiskPortfolio")

    assert fetched_id == portfolio_id