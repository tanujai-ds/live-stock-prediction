"""
Anti-Gravity EMA Trading System
Database Module — SQLite integration
Tables: candles, signals, trades, performance_metrics
"""
import sqlite3
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import config


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create all tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS candles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol      TEXT    NOT NULL,
            timeframe   TEXT    NOT NULL,
            timestamp   INTEGER NOT NULL,
            open        REAL    NOT NULL,
            high        REAL    NOT NULL,
            low         REAL    NOT NULL,
            close       REAL    NOT NULL,
            volume      REAL    NOT NULL,
            ema7        REAL,
            ema14       REAL,
            ema21       REAL,
            UNIQUE(symbol, timeframe, timestamp)
        );

        CREATE TABLE IF NOT EXISTS signals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol          TEXT    NOT NULL,
            timeframe       TEXT    NOT NULL,
            timestamp       INTEGER NOT NULL,
            signal          TEXT    NOT NULL,   -- BUY | SELL | HOLD
            price           REAL    NOT NULL,
            ema7            REAL,
            ema14           REAL,
            ema21           REAL,
            trend_strength  REAL,
            volume_ratio    REAL,
            ai_confidence   REAL    DEFAULT NULL,
            created_at      TEXT    DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS trades (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol          TEXT    NOT NULL,
            side            TEXT    NOT NULL,   -- BUY | SELL
            entry_price     REAL    NOT NULL,
            exit_price      REAL,
            quantity        REAL    NOT NULL,
            pnl             REAL    DEFAULT 0,
            pnl_pct         REAL    DEFAULT 0,
            status          TEXT    DEFAULT 'OPEN',  -- OPEN | CLOSED | SL | TP
            stop_loss       REAL,
            take_profit     REAL,
            entry_time      TEXT    NOT NULL,
            exit_time       TEXT,
            notes           TEXT
        );

        CREATE TABLE IF NOT EXISTS performance_metrics (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT    NOT NULL UNIQUE,
            total_trades    INTEGER DEFAULT 0,
            winning_trades  INTEGER DEFAULT 0,
            losing_trades   INTEGER DEFAULT 0,
            win_rate        REAL    DEFAULT 0,
            total_pnl       REAL    DEFAULT 0,
            max_drawdown    REAL    DEFAULT 0,
            sharpe_ratio    REAL    DEFAULT 0,
            profit_factor   REAL    DEFAULT 0,
            balance         REAL    DEFAULT 0
        );
        """)


# ── Candles ──────────────────────────────────────────────────────────────────

def save_candles(df: pd.DataFrame, symbol: str, timeframe: str) -> None:
    rows = []
    for _, r in df.iterrows():
        rows.append((
            symbol, timeframe,
            int(r["timestamp"]),
            float(r["open"]), float(r["high"]),
            float(r["low"]), float(r["close"]),
            float(r["volume"]),
            float(r.get("ema7", 0) or 0),
            float(r.get("ema14", 0) or 0),
            float(r.get("ema21", 0) or 0),
        ))
    with get_conn() as conn:
        conn.executemany("""
            INSERT OR REPLACE INTO candles
            (symbol, timeframe, timestamp, open, high, low, close, volume, ema7, ema14, ema21)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, rows)


def load_candles(symbol: str, timeframe: str, limit: int = 200) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM candles
            WHERE symbol=? AND timeframe=?
            ORDER BY timestamp DESC LIMIT ?
        """, conn, params=(symbol, timeframe, limit))
    return df.sort_values("timestamp").reset_index(drop=True)


# ── Signals ──────────────────────────────────────────────────────────────────

def save_signal(data: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO signals
            (symbol, timeframe, timestamp, signal, price, ema7, ema14, ema21,
             trend_strength, volume_ratio, ai_confidence)
            VALUES (:symbol,:timeframe,:timestamp,:signal,:price,:ema7,:ema14,:ema21,
                    :trend_strength,:volume_ratio,:ai_confidence)
        """, data)


def load_signals(symbol: str, timeframe: str, limit: int = 50) -> pd.DataFrame:
    with get_conn() as conn:
        df = pd.read_sql_query("""
            SELECT * FROM signals
            WHERE symbol=? AND timeframe=?
            ORDER BY id DESC LIMIT ?
        """, conn, params=(symbol, timeframe, limit))
    return df


# ── Trades ────────────────────────────────────────────────────────────────────

def open_trade(data: Dict[str, Any]) -> int:
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO trades
            (symbol, side, entry_price, quantity, stop_loss, take_profit,
             entry_time, notes)
            VALUES (:symbol,:side,:entry_price,:quantity,:stop_loss,:take_profit,
                    :entry_time,:notes)
        """, data)
        return cur.lastrowid


def close_trade(trade_id: int, exit_price: float, status: str = "CLOSED") -> None:
    with get_conn() as conn:
        trade = conn.execute(
            "SELECT * FROM trades WHERE id=?", (trade_id,)
        ).fetchone()
        if not trade:
            return
        pnl = (exit_price - trade["entry_price"]) * trade["quantity"]
        if trade["side"] == "SELL":
            pnl = -pnl
        pnl_pct = pnl / (trade["entry_price"] * trade["quantity"]) * 100
        conn.execute("""
            UPDATE trades SET exit_price=?, exit_time=?, pnl=?, pnl_pct=?, status=?
            WHERE id=?
        """, (exit_price, datetime.utcnow().isoformat(), pnl, pnl_pct, status, trade_id))


def load_trades(symbol: Optional[str] = None, status: Optional[str] = None) -> pd.DataFrame:
    query = "SELECT * FROM trades WHERE 1=1"
    params: List[Any] = []
    if symbol:
        query += " AND symbol=?"
        params.append(symbol)
    if status:
        query += " AND status=?"
        params.append(status)
    query += " ORDER BY id DESC"
    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


# ── Performance ───────────────────────────────────────────────────────────────

def upsert_performance(data: Dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO performance_metrics
            (date, total_trades, winning_trades, losing_trades,
             win_rate, total_pnl, max_drawdown, sharpe_ratio, profit_factor, balance)
            VALUES (:date,:total_trades,:winning_trades,:losing_trades,
                    :win_rate,:total_pnl,:max_drawdown,:sharpe_ratio,:profit_factor,:balance)
            ON CONFLICT(date) DO UPDATE SET
                total_trades=excluded.total_trades,
                winning_trades=excluded.winning_trades,
                losing_trades=excluded.losing_trades,
                win_rate=excluded.win_rate,
                total_pnl=excluded.total_pnl,
                max_drawdown=excluded.max_drawdown,
                sharpe_ratio=excluded.sharpe_ratio,
                profit_factor=excluded.profit_factor,
                balance=excluded.balance
        """, data)


def load_performance() -> pd.DataFrame:
    with get_conn() as conn:
        return pd.read_sql_query(
            "SELECT * FROM performance_metrics ORDER BY date DESC LIMIT 30", conn
        )


# initialise on import
init_db()
