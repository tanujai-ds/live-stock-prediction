"""
Anti-Gravity EMA Trading System
Alerts Module — Telegram BUY / SELL / trend reversal notifications
"""
import requests
from datetime import datetime
from typing import Optional
from config import config


def _send(message: str) -> bool:
    """Send a message to the configured Telegram chat."""
    if not config.ENABLE_TELEGRAM:
        return False
    if not config.TELEGRAM_TOKEN or not config.TELEGRAM_CHAT_ID:
        return False
    url = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=5)
        return resp.status_code == 200
    except Exception:
        return False


def alert_signal(
    signal: str,
    symbol: str,
    price: float,
    trend_strength: float,
    timeframe: str,
) -> bool:
    emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
    ts    = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    msg = (
        f"{emoji} <b>Anti-Gravity EMA — {signal} SIGNAL</b>\n"
        f"Symbol    : <code>{symbol}</code>\n"
        f"Timeframe : <code>{timeframe}</code>\n"
        f"Price     : <code>${price:,.4f}</code>\n"
        f"Trend Str : <code>{trend_strength:.4f}</code>\n"
        f"Time      : {ts}"
    )
    return _send(msg)


def alert_reversal(
    symbol: str,
    from_trend: str,
    to_trend: str,
    price: float,
) -> bool:
    ts  = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    msg = (
        f"⚡ <b>Trend Reversal Alert</b>\n"
        f"Symbol : <code>{symbol}</code>\n"
        f"From   : <code>{from_trend}</code> → <code>{to_trend}</code>\n"
        f"Price  : <code>${price:,.4f}</code>\n"
        f"Time   : {ts}"
    )
    return _send(msg)


def alert_trade_event(
    event: str,
    symbol: str,
    side: str,
    price: float,
    pnl: Optional[float] = None,
) -> bool:
    emoji = "📈" if side == "BUY" else "📉"
    ts    = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    pnl_line = f"\nP&L     : <code>${pnl:+.2f}</code>" if pnl is not None else ""
    msg = (
        f"{emoji} <b>Paper Trade {event}</b>\n"
        f"Symbol : <code>{symbol}</code>\n"
        f"Side   : <code>{side}</code>\n"
        f"Price  : <code>${price:,.4f}</code>"
        f"{pnl_line}\n"
        f"Time   : {ts}"
    )
    return _send(msg)
