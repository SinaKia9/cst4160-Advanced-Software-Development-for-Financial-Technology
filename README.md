
Portfolio Tracker & Risk Analytics App

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
