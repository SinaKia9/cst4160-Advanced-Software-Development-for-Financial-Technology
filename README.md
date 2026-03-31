"""
Portfolio Tracker & Risk Analytics App

Overview:
This application allows users to create and analyse stock portfolios using historical market data.
It integrates financial data, portfolio construction, and risk analysis in a simple system.

Main Features:
- Create or load a portfolio
- Select stocks manually or using momentum strategy (30/60/90 days or combined)
- Apply weighting methods:
    * Equal weighting
    * Momentum-based weighting
    * Inverse volatility weighting
- Calculate key metrics:
    * Return, volatility, drawdown
    * Value at Risk (VaR), Sharpe ratio, beta
    * Risk contribution per asset
- Save and retrieve portfolios using SQLite database

Strategy Logic:
Momentum strategy selects the top-performing stocks based on past returns.
Combined momentum uses a weighted average of 30, 60, and 90-day performance.

Workflow:
1. Choose to create or load a portfolio
2. Select strategy and weighting method
3. Analyse results
4. Optionally save the portfolio

Project Structure:
portfolio_app/
│
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── .env
│
├── core/
│   ├── universe.py
│   ├── portfolio.py
│   ├── strategy.py
│   ├── weighting.py
│   └── risk.py
│
├── services/
│   └── market_data.py
│
├── data/
│   ├── db.py
│   └── schema.sql
│
└── tests/
    ├── test_portfolio.py
    ├── test_db.py
    ├── test_market_data.py
    ├── test_risk.py
    ├── test_strategy.py
    └── test_weighting.py

Note:
This is a simulation tool based on historical data and is not intended for real trading.
"""