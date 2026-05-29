"""
Anti-Gravity EMA Trading System
Configuration Module
"""
import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class Config:
    # ── Binance API ──────────────────────────────────────────────────────────
    BINANCE_API_KEY: str = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET: str = os.getenv("BINANCE_SECRET", "")

    # ── Default trading pair / timeframe ────────────────────────────────────
    SYMBOL: str = "RELIANCE.NS"
    TIMEFRAME: str = "1d"
    CANDLE_LIMIT: int = 500          # how many candles to fetch
    REFRESH_INTERVAL: int = 30       # dashboard refresh (seconds)

    # ── EMA periods ─────────────────────────────────────────────────────────
    EMA_SHORT: int = 7
    EMA_MID: int = 14
    EMA_LONG: int = 21

    # ── Volume ───────────────────────────────────────────────────────────────
    VOLUME_MULTIPLIER: float = 1.2   # volume must be 1.2× avg to confirm signal
    VOLUME_AVG_PERIOD: int = 20

    # ── Paper trading ────────────────────────────────────────────────────────
    INITIAL_BALANCE: float = 10_000.0  # USD

    # ── Risk management ──────────────────────────────────────────────────────
    STOP_LOSS_PCT: float = 0.02       # 2 %
    TAKE_PROFIT_PCT: float = 0.04     # 4 %
    MAX_DAILY_LOSS_PCT: float = 0.05  # 5 % of balance
    POSITION_SIZE_PCT: float = 0.10   # 10 % of balance per trade

    # ── Telegram alerts ──────────────────────────────────────────────────────
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    ENABLE_TELEGRAM: bool = False

    # ── Database ─────────────────────────────────────────────────────────────
    DB_PATH: str = "antigravity_ema.db"

    # ── Supported timeframes ─────────────────────────────────────────────────
    TIMEFRAMES: List[str] = field(
        default_factory=lambda: ["1m", "5m", "15m", "1h", "4h", "1d", "1wk"]
    )

    # ── Backtesting defaults ─────────────────────────────────────────────────
    BACKTEST_CANDLES: int = 500

    # ── Future AI ────────────────────────────────────────────────────────────
    AI_ENABLED: bool = False          # flip True when LSTM/XGBoost module ready
    AI_CONFIDENCE_THRESHOLD: float = 0.65


config = Config()
