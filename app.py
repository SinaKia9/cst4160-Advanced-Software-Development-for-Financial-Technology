import pandas as pd
from datetime import datetime, timedelta

from config import HISTORY_DAYS, MARKET_BENCHMARK, STARTING_CAPITAL
from core.auth import (
    hash_password,
    verify_password,
    is_valid_email,
    generate_code,
    send_email_code,
)
from core.universe import UNIVERSE_TICKERS
from core.portfolio import build_portfolio
from core.strategy import select_top_momentum_tickers
from core.weighting import (
    equal_weighting,
    momentum_weighting,
    inverse_volatility_weighting,
)
from services.market_data import fetch_historical_bars
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
    save_price_bars,
    save_report,
    load_portfolio,
    list_portfolios,
    get_portfolio_id,
)
from core.risk import risk_report


def pct(x):
    return f"{round(float(x) * 100, 2)}%"


def expiry_valid(expiry_str):
    if not expiry_str:
        return False
    expiry_time = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
    return datetime.utcnow() <= expiry_time


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



def ask_to_save(message):
    return input(f"\n{message} (y/n): ").strip().lower() == "y"



def get_starting_capital():
    while True:
        user_input = input(
            f"Enter starting capital (press Enter for default {STARTING_CAPITAL}): "
        ).strip()

        if user_input == "":
            return STARTING_CAPITAL

        try:
            capital = float(user_input)
            if capital > 0:
                return capital
        except Exception:
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



def register_user():
    print("\n--- Register ---")

    while True:
        username = input("Enter username: ").strip()
        if username == "":
            print("Username cannot be empty.")
            continue
        if get_user_by_username(username) is not None:
            print("Username already exists.")
            continue
        break

    while True:
        email = input("Enter email: ").strip()
        if not is_valid_email(email):
            print("Invalid email format.")
            continue
        if get_user_by_email(email) is not None:
            print("Email already exists.")
            continue
        break

    while True:
        password = input("Enter password: ").strip()
        confirm = input("Confirm password: ").strip()

        if len(password) < 6:
            print("Password must be at least 6 characters.")
            continue
        if password != confirm:
            print("Passwords do not match.")
            continue
        break

    password_hash = hash_password(password)
    create_user(username, email, password_hash)

    code = generate_code()
    expiry = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    save_verification_code(email, code, expiry)

    try:
        send_email_code(
            email,
            "Verify your email",
            f"Your verification code is: {code}\n\nThis code expires in 15 minutes.",
        )
        print("Account created successfully. Verification code sent to your email.")
    except Exception:
        print("Account created successfully.")
        print(f"Verification code: {code}")
        print("Use this code to verify your email.")



def verify_email_flow():
    print("\n--- Verify Email ---")
    email = input("Enter your email: ").strip()
    code = input("Enter verification code: ").strip()

    user = get_user_by_email(email)
    if user is None:
        print("Email not found.")
        return

    if user[4] == 1:
        print("Email already verified.")
        return

    if user[5] != code:
        print("Invalid verification code.")
        return

    if not expiry_valid(user[6]):
        print("Verification code expired.")
        return

    verify_user_email(email)
    print("Email verified successfully.")



def login_user():
    print("\n--- Login ---")

    while True:
        identifier = input("Enter username or email: ").strip()
        password = input("Enter password: ").strip()

        user = get_user_by_username(identifier)
        if user is None:
            user = get_user_by_email(identifier)

        if user is None:
            print("User not found.")
        elif user[4] != 1:
            print("Please verify your email first.")
        elif not verify_password(password, user[3]):
            print("Invalid password.")
        else:
            print(f"Logged in as {user[1]}")
            return {
                "user_id": user[0],
                "username": user[1],
                "email": user[2],
            }



def forgot_password():
    print("\n--- Forgot Password ---")
    email = input("Enter your email: ").strip()

    user = get_user_by_email(email)
    if user is None:
        print("Email not found.")
        return

    code = generate_code()
    expiry = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
    save_reset_code(email, code, expiry)

    try:
        send_email_code(
            email,
            "Password reset code",
            f"Your password reset code is: {code}\n\nThis code expires in 15 minutes.",
        )
        print("A reset code has been sent to your email.")
    except Exception:
        print(f"Reset code: {code}")
        print("Use this code in the reset password option within 15 minutes.")



def reset_password():
    print("\n--- Reset Password ---")
    email = input("Enter your email: ").strip()
    code = input("Enter reset code: ").strip()

    user = get_user_by_email(email)
    if user is None:
        print("Email not found.")
        return

    if user[7] != code:
        print("Invalid reset code.")
        return

    if not expiry_valid(user[8]):
        print("Reset code expired.")
        return

    while True:
        new_password = input("Enter new password: ").strip()
        confirm = input("Confirm new password: ").strip()

        if len(new_password) < 6:
            print("Password must be at least 6 characters.")
            continue
        if new_password != confirm:
            print("Passwords do not match.")
            continue
        break

    update_user_password(email, hash_password(new_password))
    print("Password updated successfully.")



def create_new_portfolio(user):
    while True:
        portfolio_name = input("\nEnter portfolio name: ").strip()

        if portfolio_name == "":
            print("Name cannot be empty.")
            continue

        if get_portfolio_id(user["user_id"], portfolio_name) is not None:
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
            selected_tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

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
            strategy_type=strategy_type,
        )

        portfolio_bars = universe_bars[
            universe_bars["ticker"].isin(selected_tickers)
        ].copy()

    holdings = build_weights(weighting_method, portfolio_bars, selected_tickers, strategy_type)
    benchmark_bars = fetch_historical_bars([MARKET_BENCHMARK], HISTORY_DAYS)
    report = risk_report(holdings, portfolio_bars, benchmark_bars, starting_capital)

    display_report(portfolio_name, report)

    if ask_to_save("Do you want to save this portfolio"):
        portfolio_id = create_portfolio(user["user_id"], portfolio_name)
        save_holdings(portfolio_id, holdings)

        all_bars = pd.concat([portfolio_bars, benchmark_bars], ignore_index=True)
        save_price_bars(all_bars)
        save_report(portfolio_id, report)

        print("\nPortfolio saved.")
    else:
        print("\nPortfolio not saved.")



def load_existing_portfolio_flow(user):
    portfolios = list_portfolios(user["user_id"])

    if not portfolios:
        print("\nNo portfolios found.")
        return

    print("\nSaved portfolios:")
    for portfolio_name in portfolios:
        print(f"- {portfolio_name}")

    while True:
        name = input("\nEnter portfolio name: ").strip()
        holdings = load_portfolio(user["user_id"], name)

        if holdings is not None:
            break

        print("Portfolio not found.")

    portfolio_id = get_portfolio_id(user["user_id"], name)
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



def user_menu(user):
    while True:
        print(f"\n--- Welcome, {user['username']} ---")
        print("1. Create new portfolio")
        print("2. Load existing portfolio")
        print("3. Log out")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            create_new_portfolio(user)
        elif choice == "2":
            load_existing_portfolio_flow(user)
        elif choice == "3":
            print("Logged out.")
            break
        else:
            print("Invalid choice, try again.")



def main():
    init_db()

    while True:
        print("\n1. Register")
        print("2. Verify email")
        print("3. Login")
        print("4. Forgot password")
        print("5. Reset password")
        print("6. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            register_user()
        elif choice == "2":
            verify_email_flow()
        elif choice == "3":
            user = login_user()
            if user is not None:
                user_menu(user)
        elif choice == "4":
            forgot_password()
        elif choice == "5":
            reset_password()
        elif choice == "6":
            print("Goodbye.")
            break
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()
