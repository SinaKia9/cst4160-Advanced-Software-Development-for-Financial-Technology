Portfolio Tracker & Risk Analytics App

Overview
This project is a Python-based application that allows users to create and analyse stock portfolios using historical market data. It combines portfolio construction, strategy selection, risk analysis, database storage, and user authentication in one system.

The application supports both a terminal version and a Streamlit web interface.

Main Features
- User registration and login
- Email verification when creating an account
- Forgot password with reset code sent by email
- Create a new portfolio or load an existing one
- Manual stock selection or momentum-based selection
- Momentum strategies:
  - 30-day
  - 60-day
  - 90-day
  - combined momentum
- Weighting methods:
  - Equal weighting
  - Momentum weighting
  - Inverse volatility weighting
- Risk and performance metrics:
  - Cumulative return
  - Expected annual return
  - Annualised volatility
  - Maximum drawdown
  - Value at Risk (VaR)
  - Sharpe ratio
  - Beta vs benchmark
  - Best and worst day return
  - Risk contribution per asset
- Save and load portfolios using SQLite
- Charts in Streamlit:
  - Portfolio growth
  - Portfolio vs benchmark
  - Selected stocks performance

Project Structure
- app.py -> main terminal application
- streamlit_app.py -> web interface
- core/auth.py -> authentication logic
- core/strategy.py -> momentum strategy
- core/weighting.py -> weighting methods
- core/risk.py -> risk calculations
- core/portfolio.py -> portfolio validation and construction
- core/universe.py -> stock universe
- services/market_data.py -> Alpaca market data
- data/schema.sql -> database schema
- data/db.py -> database functions
- tests/ -> unit tests

How It Works
1. The user registers and verifies their email
2. The user logs in
3. The user creates a portfolio manually or by momentum strategy
4. The app applies the selected weighting method
5. Historical data is fetched from Alpaca
6. Risk and return metrics are calculated
7. The portfolio can be saved and loaded later
8. In Streamlit, charts show portfolio performance visually

Technologies Used
- Python
- Pandas
- NumPy
- SQLite
- Alpaca API
- Streamlit
- Pytest
- Bcrypt

How to Run
1. Install dependencies:
   python -m pip install -r requirements.txt

2. Create a .env file with:

ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_APP_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

4. Run terminal app:
   python app.py

5. Run Streamlit app:
   python -m streamlit run streamlit_app.py

6. Run tests:
   python -m pytest 

Note: Each student provides the global variables (config.py) and required .env details in the appendix of their individual report
