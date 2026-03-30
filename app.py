import pandas as pd

from config import (
    HISTORY_DAYS,
    MARKET_BENCHMARK,
    STARTING_CAPITAL
)
from core.universe import UNIVERSE_TICKERS
from core.portfolio import build_portfolio
from core.strategy import select_top_momentum_tickers
from core.weighting import (
    equal_weighting,
    momentum_weighting,
    inverse_volatility_weighting
)
from services.market_data import fetch_historical_bars
from data.db import (
    init_db,
    create_portfolio,
    save_holdings,
    save_price_bars,
    save_report,
    load_portfolio,
    list_portfolios,
    get_portfolio_id
)
from core.risk import risk_report


def pct(x):
    return f"{round(x * 100, 2)}%"


def display_report(portfolio_name, report):
    print("\nPortfolio created successfully.")
    print(f"Portfolio name: {portfolio_name}")
    print(f"Starting capital: {report['starting_capital']}")

    print(f"Holdings: {report['weights']}")
    print(f"Allocations: {report['allocations']}")

    print(f"Cumulative return: {pct(report['cumulative_return'])}")
    print(f"Expected annual return: {pct(report['expected_annual_return'])}")
    print(f"Annualised volatility: {pct(report['annualised_volatility'])}")
    print(f"Max drawdown: {pct(report['max_drawdown'])}")
    print(f"Historical VaR (5%): {pct(report['historical_var_5pct'])}")

    print(f"Sharpe ratio: {report['sharpe_ratio']}")
    print(f"Beta vs benchmark: {report['beta_vs_benchmark']}")

    print(f"Best day return: {pct(report['best_day_return'])}")
    print(f"Worst day return: {pct(report['worst_day_return'])}")

    risk_pct = {k: pct(v) for k, v in report['risk_contribution'].items()}
    print(f"Risk contribution: {risk_pct}")


def main():
    init_db()

    while True:
        print("\n1. Create new portfolio")
        print("2. Load existing portfolio")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            create_new_portfolio()
            break
        elif choice == "2":
            load_existing_portfolio_flow()
            break
        else:
            print("Invalid choice, try again.")


def get_starting_capital():
    while True:
        user_input = input(f"Enter starting capital (press Enter for default {STARTING_CAPITAL}): ").strip()

        if user_input == "":
            return STARTING_CAPITAL

        try:
            capital = float(user_input)
            if capital > 0:
                return capital
        except:
            pass

        print("Invalid capital, try again.")


def choose_strategy_mode():
    while True:
        print("\nChoose portfolio mode:")
        print("1. manual")
        print("2. momentum")

        choice = input("Enter choice: ").strip()

        if choice == "" or choice == "1":
            return "manual"
        if choice == "2":
            return "momentum"

        print("Invalid choice, try again.")


def choose_weighting_method():
    while True:
        print("\nChoose weighting method:")
        print("1. equal")
        print("2. momentum")
        print("3. inverse_volatility")

        choice = input("Enter choice: ").strip()

        if choice == "" or choice == "1":
            return "equal"
        if choice == "2":
            return "momentum"
        if choice == "3":
            return "inverse_volatility"

        print("Invalid choice, try again.")


def choose_momentum_type():
    while True:
        print("\nChoose momentum strategy:")
        print("1. 30_day")
        print("2. 60_day")
        print("3. 90_day")
        print("4. combined")

        choice = input("Enter choice: ").strip()

        if choice == "" or choice == "4":
            return "combined"
        if choice == "1":
            return "30_day"
        if choice == "2":
            return "60_day"
        if choice == "3":
            return "90_day"

        print("Invalid choice, try again.")


def build_weights(method, price_df, tickers, strategy_type="combined"):
    if method == "equal":
        return equal_weighting(tickers)

    if method == "momentum":
        return momentum_weighting(price_df, tickers, strategy_type=strategy_type)

    if method == "inverse_volatility":
        return inverse_volatility_weighting(price_df, tickers)

    raise ValueError("Invalid weighting method.")


def ask_to_save(message):
    return input(f"\n{message} (y/n): ").strip().lower() == "y"


def create_new_portfolio():
    while True:
        portfolio_name = input("\nEnter portfolio name: ").strip()

        if portfolio_name == "":
            print("Name cannot be empty.")
            continue

        if get_portfolio_id(portfolio_name) is not None:
            print("Portfolio already exists. Choose another name.")
            continue

        break

    starting_capital = get_starting_capital()
    strategy_mode = choose_strategy_mode()
    weighting_method = choose_weighting_method()

    if strategy_mode == "manual":
        print("\nAvailable tickers:")
        print(", ".join(UNIVERSE_TICKERS))

        while True:
            ticker_input = input("\nEnter 3 to 7 tickers: ").strip()
            selected_tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]

            if 3 <= len(selected_tickers) <= 7:
                break

            print("Enter between 3 and 7 tickers.")

        base_holdings = build_portfolio(selected_tickers, mode="equal")
        selected_tickers = list(base_holdings.keys())

        portfolio_bars = fetch_historical_bars(selected_tickers, HISTORY_DAYS)
        strategy_type = "combined"

    else:
        strategy_type = choose_momentum_type()
        universe_bars = fetch_historical_bars(UNIVERSE_TICKERS, HISTORY_DAYS)

        selected_tickers = select_top_momentum_tickers(
            universe_bars,
            strategy_type=strategy_type
        )

        portfolio_bars = universe_bars[universe_bars["ticker"].isin(selected_tickers)].copy()

    holdings = build_weights(weighting_method, portfolio_bars, selected_tickers, strategy_type)

    benchmark_bars = fetch_historical_bars([MARKET_BENCHMARK], HISTORY_DAYS)

    report = risk_report(holdings, portfolio_bars, benchmark_bars, starting_capital)

    display_report(portfolio_name, report)

    if ask_to_save("Do you want to save this portfolio"):
        portfolio_id = create_portfolio(portfolio_name)
        save_holdings(portfolio_id, holdings)

        all_bars = pd.concat([portfolio_bars, benchmark_bars], ignore_index=True)
        save_price_bars(all_bars)
        save_report(portfolio_id, report)

        print("\nPortfolio saved.")
    else:
        print("\nPortfolio not saved.")


def load_existing_portfolio_flow():
    portfolios = list_portfolios()

    if not portfolios:
        print("\nNo portfolios found.")
        return

    print("\nSaved portfolios:")
    for p in portfolios:
        print(f"- {p}")

    while True:
        name = input("\nEnter portfolio name: ").strip()
        holdings = load_portfolio(name)

        if holdings is not None:
            break

        print("Portfolio not found.")

    portfolio_id = get_portfolio_id(name)
    starting_capital = get_starting_capital()

    tickers = list(holdings.keys())

    portfolio_bars = fetch_historical_bars(tickers, HISTORY_DAYS)
    benchmark_bars = fetch_historical_bars([MARKET_BENCHMARK], HISTORY_DAYS)

    report = risk_report(holdings, portfolio_bars, benchmark_bars, starting_capital)

    display_report(name, report)

    if ask_to_save("Save updated report"):
        all_bars = pd.concat([portfolio_bars, benchmark_bars], ignore_index=True)
        save_price_bars(all_bars)
        save_report(portfolio_id, report)

        print("\nReport saved.")
    else:
        print("\nReport not saved.")


if __name__ == "__main__":
    main()