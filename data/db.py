import sqlite3
import json
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open("data/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def create_portfolio(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO portfolios (name) VALUES (?)",
        (name,)
    )

    conn.commit()
    portfolio_id = cursor.lastrowid
    conn.close()

    return portfolio_id


def save_holdings(portfolio_id, holdings_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for ticker, weight in holdings_dict.items():
        cursor.execute(
            "INSERT INTO holdings (portfolio_id, ticker, weight) VALUES (?, ?, ?)",
            (portfolio_id, ticker, weight)
        )

    conn.commit()
    conn.close()


def save_price_bars(df_bars):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for _, row in df_bars.iterrows():
        cursor.execute(
            """
            INSERT INTO price_bars (ticker, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["ticker"],
                row["date"],
                row["open"],
                row["high"],
                row["low"],
                row["close"],
                row["volume"]
            )
        )

    conn.commit()
    conn.close()


def load_portfolio(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT portfolio_id FROM portfolios WHERE name = ?",
        (name,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    portfolio_id = result[0]

    cursor.execute(
        "SELECT ticker, weight FROM holdings WHERE portfolio_id = ?",
        (portfolio_id,)
    )
    rows = cursor.fetchall()

    conn.close()

    return {ticker: weight for ticker, weight in rows}


def list_portfolios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM portfolios")
    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]


def save_report(portfolio_id, report_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    json_data = json.dumps(report_dict)

    cursor.execute(
        "INSERT INTO reports (portfolio_id, json_summary) VALUES (?, ?)",
        (portfolio_id, json_data)
    )

    conn.commit()
    conn.close()

    
def get_portfolio_id(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT portfolio_id FROM portfolios WHERE name = ?",
        (name,)
    )
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    return None