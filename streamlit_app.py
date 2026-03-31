import pandas as pd
import streamlit as st

from config import HISTORY_DAYS, MARKET_BENCHMARK, STARTING_CAPITAL
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


def build_weights(method, price_df, tickers, strategy_type="combined"):
    if method == "equal":
        return equal_weighting(tickers)
    if method == "momentum":
        return momentum_weighting(price_df, tickers, strategy_type=strategy_type)
    if method == "inverse_volatility":
        return inverse_volatility_weighting(price_df, tickers)
    raise ValueError("Invalid weighting method.")


def show_report(portfolio_name, report, selected_tickers, strategy_label=None):
    st.success("Portfolio generated successfully.")

    st.subheader("Portfolio")
    st.write(f"Name: {portfolio_name}")
    st.write(f"Starting capital: {float(report['starting_capital']):.2f}")

    if strategy_label:
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


st.set_page_config(page_title="Portfolio Tracker", layout="wide")
st.title("Portfolio Tracker & Risk Analytics")
st.write("Create or load a portfolio, apply strategy and weighting, then analyse performance.")

if "generated_data" not in st.session_state:
    st.session_state.generated_data = None

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

            elif mode == "manual":
                if not (3 <= len(selected_tickers) <= 7):
                    st.error("Please select between 3 and 7 tickers.")
                else:
                    base_holdings = build_portfolio(selected_tickers, mode="equal")
                    selected_tickers = list(base_holdings.keys())

                    portfolio_bars = fetch_historical_bars(selected_tickers, HISTORY_DAYS)
                    holdings = build_weights(
                        weighting_method,
                        portfolio_bars,
                        selected_tickers,
                        strategy_type="combined"
                    )
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
                selected_tickers = select_top_momentum_tickers(
                    universe_bars,
                    strategy_type=strategy_type
                )

                portfolio_bars = universe_bars[universe_bars["ticker"].isin(selected_tickers)].copy()

                holdings = build_weights(
                    weighting_method,
                    portfolio_bars,
                    selected_tickers,
                    strategy_type=strategy_type
                )

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
            data["strategy_label"]
        )

        if st.button("Save Portfolio"):
            try:
                if get_portfolio_id(data["portfolio_name"]) is not None:
                    st.error("Portfolio name already exists. Choose a different name.")
                else:
                    portfolio_id = create_portfolio(data["portfolio_name"])
                    save_holdings(portfolio_id, data["holdings"])

                    all_bars = pd.concat([data["portfolio_bars"], data["benchmark_bars"]], ignore_index=True)
                    save_price_bars(all_bars)
                    save_report(portfolio_id, data["report"])

                    st.success("Portfolio saved successfully.")
            except Exception as e:
                st.error(f"Error saving portfolio: {e}")

else:
    saved_portfolios = list_portfolios()

    if not saved_portfolios:
        st.info("No saved portfolios found.")
    else:
        selected_name = st.selectbox("Choose saved portfolio", saved_portfolios)

        if st.button("Load and Analyse"):
            try:
                holdings = load_portfolio(selected_name)
                portfolio_id = get_portfolio_id(selected_name)

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
                data["strategy_label"]
            )

            if st.button("Save Updated Report"):
                try:
                    all_bars = pd.concat([data["portfolio_bars"], data["benchmark_bars"]], ignore_index=True)
                    save_price_bars(all_bars)
                    save_report(data["portfolio_id"], data["report"])
                    st.success("Updated report saved successfully.")
                except Exception as e:
                    st.error(f"Error saving report: {e}")