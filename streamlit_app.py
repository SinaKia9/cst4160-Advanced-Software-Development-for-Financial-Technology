import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

from config import HISTORY_DAYS, MARKET_BENCHMARK, STARTING_CAPITAL
from core.auth import (
    hash_password,
    verify_password,
    is_valid_email,
    generate_code,
    send_email_code
)
from core.universe import UNIVERSE_TICKERS
from core.portfolio import build_portfolio
from core.strategy import select_top_momentum_tickers
from core.weighting import (
    equal_weighting,
    momentum_weighting,
    inverse_volatility_weighting
)
from core.risk import risk_report
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
    get_portfolio_id
)

init_db()


def pct(x):
    return f"{round(float(x) * 100, 2)}%"


def expiry_valid(expiry_str):
    if not expiry_str:
        return False
    expiry_time = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")
    return datetime.utcnow() <= expiry_time


def build_weights(method, price_df, tickers, strategy_type="combined"):
    if method == "equal":
        return equal_weighting(tickers)
    if method == "momentum":
        return momentum_weighting(price_df, tickers, strategy_type=strategy_type)
    if method == "inverse_volatility":
        return inverse_volatility_weighting(price_df, tickers)
    raise ValueError("Invalid weighting method.")


def compute_portfolio_series(holdings, portfolio_bars, benchmark_bars, starting_capital):
    price_matrix = portfolio_bars.pivot(index="date", columns="ticker", values="close").sort_index()
    asset_returns = price_matrix.pct_change().dropna()

    weights_series = pd.Series(holdings).reindex(asset_returns.columns).fillna(0.0)
    portfolio_daily_returns = asset_returns.mul(weights_series, axis=1).sum(axis=1)
    portfolio_value = float(starting_capital) * (1 + portfolio_daily_returns).cumprod()

    benchmark_matrix = benchmark_bars.pivot(index="date", columns="ticker", values="close").sort_index()
    benchmark_close = benchmark_matrix.iloc[:, 0]
    benchmark_returns = benchmark_close.pct_change().dropna()

    common_index = portfolio_daily_returns.index.intersection(benchmark_returns.index)
    portfolio_value = portfolio_value.loc[common_index]
    benchmark_value = float(starting_capital) * (1 + benchmark_returns.loc[common_index]).cumprod()

    normalized_assets = (price_matrix / price_matrix.iloc[0]) * 100
    normalized_assets = normalized_assets.dropna()

    return portfolio_value, benchmark_value, normalized_assets


def show_report(portfolio_name, report, selected_tickers, strategy_label, holdings, portfolio_bars, benchmark_bars):
    st.success("Portfolio generated successfully.")

    st.subheader("Portfolio")
    st.write(f"Name: {portfolio_name}")
    st.write(f"Starting capital: {float(report['starting_capital']):.2f}")
    st.write(f"Strategy used: {strategy_label}")

    st.subheader("Selected Tickers")
    st.write(selected_tickers)

    st.subheader("Weights")
    weights_df = pd.DataFrame({
        "Ticker": list(report["weights"].keys()),
        "Weight": [pct(v) for v in report["weights"].values()]
    })
    st.dataframe(weights_df, width="stretch")

    st.subheader("Allocations")
    alloc_df = pd.DataFrame({
        "Ticker": list(report["allocations"].keys()),
        "Allocation": [f"{float(v):.2f}" for v in report["allocations"].values()]
    })
    st.dataframe(alloc_df, width="stretch")

    st.subheader("Risk & Performance Metrics")
    metrics_df = pd.DataFrame({
        "Metric": [
            "Cumulative Return",
            "Expected Annual Return",
            "Annualised Volatility",
            "Max Drawdown",
            "Historical VaR (5%)",
            "Sharpe Ratio",
            "Beta vs Benchmark",
            "Best Day Return",
            "Worst Day Return"
        ],
        "Value": [
            pct(report["cumulative_return"]),
            pct(report["expected_annual_return"]),
            pct(report["annualised_volatility"]),
            pct(report["max_drawdown"]),
            pct(report["historical_var_5pct"]),
            str(round(float(report["sharpe_ratio"]), 4)),
            str(round(float(report["beta_vs_benchmark"]), 4)),
            pct(report["best_day_return"]),
            pct(report["worst_day_return"])
        ]
    })
    st.dataframe(metrics_df, width="stretch")

    st.subheader("Risk Contribution")
    risk_df = pd.DataFrame({
        "Ticker": list(report["risk_contribution"].keys()),
        "Risk Contribution": [pct(v) for v in report["risk_contribution"].values()]
    })
    st.dataframe(risk_df, width="stretch")

    portfolio_value, benchmark_value, normalized_assets = compute_portfolio_series(
        holdings,
        portfolio_bars,
        benchmark_bars,
        report["starting_capital"]
    )

    st.subheader("Portfolio Growth")
    st.line_chart(portfolio_value, width="stretch")

    st.subheader("Portfolio vs Benchmark")
    compare_df = pd.DataFrame({
        "Portfolio": portfolio_value,
        "Benchmark": benchmark_value
    })
    st.line_chart(compare_df, width="stretch")

    st.subheader("Selected Stocks Performance (Base = 100)")
    st.line_chart(normalized_assets, width="stretch")


st.set_page_config(page_title="Portfolio Tracker", layout="wide")
st.title("Portfolio Tracker & Risk Analytics")
st.write("Register, verify your email, log in, and manage your own portfolios.")

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

if "pending_verification_email" not in st.session_state:
    st.session_state.pending_verification_email = None

if "show_verification_screen" not in st.session_state:
    st.session_state.show_verification_screen = False

if "flash_success" not in st.session_state:
    st.session_state.flash_success = None

if "flash_error" not in st.session_state:
    st.session_state.flash_error = None


if st.session_state.flash_success:
    st.success(st.session_state.flash_success)
    st.session_state.flash_success = None

if st.session_state.flash_error:
    st.error(st.session_state.flash_error)
    st.session_state.flash_error = None


# ---------------- AUTH SECTION ----------------
if st.session_state.auth_user is None:
    if st.session_state.show_verification_screen:
        st.subheader("Verify Your Email")
        st.write(f"A verification code was sent to: {st.session_state.pending_verification_email}")

        verify_code = st.text_input("Verification Code")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Verify Email"):
                verify_email = st.session_state.pending_verification_email
                user = get_user_by_email(verify_email)

                if user is None:
                    st.error("Email not found.")
                elif user[4] == 1:
                    st.info("Email already verified.")
                elif user[5] != verify_code:
                    st.error("Invalid verification code.")
                elif not expiry_valid(user[6]):
                    st.error("Verification code expired.")
                else:
                    verify_user_email(verify_email)
                    st.session_state.flash_success = "Account created and email verified successfully. You can now log in."
                    st.session_state.show_verification_screen = False
                    st.session_state.pending_verification_email = None
                    st.rerun()

        with col2:
            if st.button("Back to Login/Register"):
                st.session_state.show_verification_screen = False
                st.session_state.pending_verification_email = None
                st.rerun()

    else:
        auth_mode = st.radio(
            "Account Access",
            ["Login", "Register", "Forgot Password"]
        )

        if auth_mode == "Login":
            st.subheader("Login")
            login_identifier = st.text_input("Username or Email")
            login_password = st.text_input("Password", type="password")

            if st.button("Log In"):
                user = get_user_by_username(login_identifier)
                if user is None:
                    user = get_user_by_email(login_identifier)

                if user is None:
                    st.error("User not found.")
                elif user[4] != 1:
                    st.error("Please verify your email first.")
                elif not verify_password(login_password, user[3]):
                    st.error("Invalid password.")
                else:
                    st.session_state.auth_user = {
                        "user_id": user[0],
                        "username": user[1],
                        "email": user[2]
                    }
                    st.session_state.generated_data = None
                    st.rerun()

        elif auth_mode == "Register":
            st.subheader("Create Account")
            reg_username = st.text_input("Username")
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            reg_confirm = st.text_input("Confirm Password", type="password")

            if st.button("Register"):
                if reg_username.strip() == "":
                    st.error("Username cannot be empty.")
                elif not is_valid_email(reg_email):
                    st.error("Enter a valid email address.")
                elif reg_password != reg_confirm:
                    st.error("Passwords do not match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                elif get_user_by_username(reg_username) is not None:
                    st.error("Username already exists.")
                elif get_user_by_email(reg_email) is not None:
                    st.error("Email already exists.")
                else:
                    password_hash = hash_password(reg_password)
                    create_user(reg_username, reg_email, password_hash)

                    code = generate_code()
                    expiry = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
                    save_verification_code(reg_email, code, expiry)

                    try:
                        send_email_code(
                            reg_email,
                            "Verify your Portfolio App account",
                            f"Your verification code is: {code}\n\nThis code expires in 15 minutes."
                        )
                        st.session_state.flash_success = "Account created successfully. A verification code was sent to your email."
                    except Exception as e:
                        st.session_state.flash_error = f"Account created, but email could not be sent: {e}"

                    st.session_state.pending_verification_email = reg_email
                    st.session_state.show_verification_screen = True
                    st.rerun()

        else:
            st.subheader("Forgot Password")
            reset_email = st.text_input("Account Email")

            if st.button("Send Reset Code"):
                user = get_user_by_email(reset_email)

                if user is None:
                    st.error("Email not found.")
                else:
                    code = generate_code()
                    expiry = (datetime.utcnow() + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S")
                    save_reset_code(reset_email, code, expiry)

                    try:
                        send_email_code(
                            reset_email,
                            "Portfolio App password reset code",
                            f"Your reset code is: {code}\n\nThis code expires in 15 minutes."
                        )
                        st.session_state.flash_success = "Reset code sent to your email."
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not send email: {e}")

            reset_code = st.text_input("Reset Code")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            if st.button("Set New Password"):
                user = get_user_by_email(reset_email)

                if user is None:
                    st.error("Email not found.")
                elif user[7] != reset_code:
                    st.error("Invalid reset code.")
                elif not expiry_valid(user[8]):
                    st.error("Reset code expired.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    update_user_password(reset_email, hash_password(new_password))
                    st.session_state.flash_success = "Password reset successfully. You can now log in."
                    st.rerun()


# ---------------- APP SECTION ----------------
else:
    st.sidebar.success(f"Logged in as: {st.session_state.auth_user['username']}")
    if st.sidebar.button("Log Out"):
        st.session_state.auth_user = None
        st.session_state.generated_data = None
        st.rerun()

    user_id = st.session_state.auth_user["user_id"]

    action = st.radio("Choose action", ["Create new portfolio", "Load existing portfolio"])
    starting_capital = st.number_input(
        "Starting capital",
        min_value=1000.0,
        value=float(STARTING_CAPITAL),
        step=1000.0
    )

    if action == "Create new portfolio":
        portfolio_name = st.text_input("Portfolio name", value="MyPortfolio")
        mode = st.selectbox("Portfolio mode", ["manual", "momentum"])
        weighting_method = st.selectbox("Weighting method", ["equal", "momentum", "inverse_volatility"])

        strategy_type = "combined"
        selected_tickers = []

        if mode == "manual":
            selected_tickers = st.multiselect(
                "Select between 3 and 7 tickers",
                UNIVERSE_TICKERS,
                default=["AAPL", "MSFT", "NVDA"]
            )
        else:
            strategy_type = st.selectbox("Momentum strategy", ["30_day", "60_day", "90_day", "combined"])

        if st.button("Generate Portfolio"):
            try:
                if portfolio_name.strip() == "":
                    st.error("Portfolio name cannot be empty.")
                elif get_portfolio_id(user_id, portfolio_name) is not None:
                    st.error("Portfolio name already exists for this account.")
                elif mode == "manual":
                    if not (3 <= len(selected_tickers) <= 7):
                        st.error("Please select between 3 and 7 tickers.")
                    else:
                        base_holdings = build_portfolio(selected_tickers, mode="equal")
                        selected_tickers = list(base_holdings.keys())

                        portfolio_bars = fetch_historical_bars(selected_tickers, HISTORY_DAYS)
                        holdings = build_weights(weighting_method, portfolio_bars, selected_tickers, "combined")
                        benchmark_bars = fetch_historical_bars([MARKET_BENCHMARK], HISTORY_DAYS)
                        report = risk_report(holdings, portfolio_bars, benchmark_bars, starting_capital)

                        st.session_state.generated_data = {
                            "portfolio_name": portfolio_name,
                            "holdings": holdings,
                            "portfolio_bars": portfolio_bars,
                            "benchmark_bars": benchmark_bars,
                            "report": report,
                            "selected_tickers": selected_tickers,
                            "strategy_label": "manual selection"
                        }

                else:
                    universe_bars = fetch_historical_bars(UNIVERSE_TICKERS, HISTORY_DAYS)
                    selected_tickers = select_top_momentum_tickers(universe_bars, strategy_type=strategy_type)
                    portfolio_bars = universe_bars[universe_bars["ticker"].isin(selected_tickers)].copy()

                    holdings = build_weights(weighting_method, portfolio_bars, selected_tickers, strategy_type)
                    benchmark_bars = fetch_historical_bars([MARKET_BENCHMARK], HISTORY_DAYS)
                    report = risk_report(holdings, portfolio_bars, benchmark_bars, starting_capital)

                    st.session_state.generated_data = {
                        "portfolio_name": portfolio_name,
                        "holdings": holdings,
                        "portfolio_bars": portfolio_bars,
                        "benchmark_bars": benchmark_bars,
                        "report": report,
                        "selected_tickers": selected_tickers,
                        "strategy_label": f"{strategy_type} momentum"
                    }

            except Exception as e:
                st.error(f"Error: {e}")

        if st.session_state.generated_data and action == "Create new portfolio":
            data = st.session_state.generated_data
            show_report(
                data["portfolio_name"],
                data["report"],
                data["selected_tickers"],
                data["strategy_label"],
                data["holdings"],
                data["portfolio_bars"],
                data["benchmark_bars"]
            )

            if st.button("Save Portfolio"):
                try:
                    portfolio_id = create_portfolio(user_id, data["portfolio_name"])
                    save_holdings(portfolio_id, data["holdings"])

                    all_bars = pd.concat([data["portfolio_bars"], data["benchmark_bars"]], ignore_index=True)
                    save_price_bars(all_bars)
                    save_report(portfolio_id, data["report"])

                    st.success("Portfolio saved successfully.")
                except Exception as e:
                    st.error(f"Error saving portfolio: {e}")

    else:
        saved_portfolios = list_portfolios(user_id)

        if not saved_portfolios:
            st.info("No saved portfolios found.")
        else:
            selected_name = st.selectbox("Choose saved portfolio", saved_portfolios)

            if st.button("Load and Analyse"):
                try:
                    holdings = load_portfolio(user_id, selected_name)
                    portfolio_id = get_portfolio_id(user_id, selected_name)

                    if holdings is None or portfolio_id is None:
                        st.error("Portfolio not found.")
                    else:
                        selected_tickers = list(holdings.keys())
                        portfolio_bars = fetch_historical_bars(selected_tickers, HISTORY_DAYS)
                        benchmark_bars = fetch_historical_bars([MARKET_BENCHMARK], HISTORY_DAYS)
                        report = risk_report(holdings, portfolio_bars, benchmark_bars, starting_capital)

                        st.session_state.generated_data = {
                            "portfolio_name": selected_name,
                            "portfolio_id": portfolio_id,
                            "holdings": holdings,
                            "portfolio_bars": portfolio_bars,
                            "benchmark_bars": benchmark_bars,
                            "report": report,
                            "selected_tickers": selected_tickers,
                            "strategy_label": "loaded portfolio"
                        }

                except Exception as e:
                    st.error(f"Error: {e}")

            if st.session_state.generated_data and action == "Load existing portfolio":
                data = st.session_state.generated_data
                show_report(
                    data["portfolio_name"],
                    data["report"],
                    data["selected_tickers"],
                    data["strategy_label"],
                    data["holdings"],
                    data["portfolio_bars"],
                    data["benchmark_bars"]
                )

                if st.button("Save Updated Report"):
                    try:
                        all_bars = pd.concat([data["portfolio_bars"], data["benchmark_bars"]], ignore_index=True)
                        save_price_bars(all_bars)
                        save_report(data["portfolio_id"], data["report"])
                        st.success("Updated report saved successfully.")
                    except Exception as e:
                        st.error(f"Error saving report: {e}")