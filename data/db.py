import json
import sqlite3
from config import DB_PATH


def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open("data/schema.sql", "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def create_user(username, email, password_hash):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_id, username, email, password_hash, email_verified,
               verification_code, verification_expiry, reset_code, reset_expiry
        FROM users
        WHERE username = ?
        """,
        (username,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


def get_user_by_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT user_id, username, email, password_hash, email_verified,
               verification_code, verification_expiry, reset_code, reset_expiry
        FROM users
        WHERE email = ?
        """,
        (email,)
    )
    result = cursor.fetchone()
    conn.close()
    return result


def save_verification_code(email, code, expiry):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET verification_code = ?, verification_expiry = ? WHERE email = ?",
        (code, expiry, email)
    )
    conn.commit()
    conn.close()


def verify_user_email(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET email_verified = 1,
            verification_code = NULL,
            verification_expiry = NULL
        WHERE email = ?
        """,
        (email,)
    )
    conn.commit()
    conn.close()


def save_reset_code(email, code, expiry):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reset_code = ?, reset_expiry = ? WHERE email = ?",
        (code, expiry, email)
    )
    conn.commit()
    conn.close()


def update_user_password(email, new_password_hash):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET password_hash = ?,
            reset_code = NULL,
            reset_expiry = NULL
        WHERE email = ?
        """,
        (new_password_hash, email)
    )
    conn.commit()
    conn.close()


def create_portfolio(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO portfolios (user_id, name) VALUES (?, ?)",
        (user_id, name)
    )
    conn.commit()
    portfolio_id = cursor.lastrowid
    conn.close()
    return portfolio_id


def get_portfolio_id(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT portfolio_id FROM portfolios WHERE user_id = ? AND name = ?",
        (user_id, name)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


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


def load_portfolio(user_id, name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT portfolio_id FROM portfolios WHERE user_id = ? AND name = ?",
        (user_id, name)
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


def list_portfolios(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM portfolios WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def save_report(portfolio_id, report_dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (portfolio_id, json_summary) VALUES (?, ?)",
        (portfolio_id, json.dumps(report_dict))
    )
    conn.commit()
    conn.close()