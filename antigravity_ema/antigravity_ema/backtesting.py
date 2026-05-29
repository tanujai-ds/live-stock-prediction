"""
Anti-Gravity EMA Trading System
Backtesting Engine — strategy performance on historical data
"""
import pandas as pd
import numpy as np
from typing import Optional
from config import config
from indicators import add_all_indicators
from signal_engine import generate_signals
from risk_manager import RiskManager


def run_backtest(
    df: pd.DataFrame,
    initial_balance: float = config.INITIAL_BALANCE,
    stop_loss_pct: float = config.STOP_LOSS_PCT,
    take_profit_pct: float = config.TAKE_PROFIT_PCT,
    position_size_pct: float = config.POSITION_SIZE_PCT,
) -> dict:
    """
    Run EMA strategy backtest on a DataFrame of candles.
    Returns a results dict with metrics and a trades list.
    """
    df = add_all_indicators(df)
    df = generate_signals(df)

    balance       = initial_balance
    equity_curve  = [initial_balance]
    trades        = []
    open_trade_: Optional[dict] = None

    for i in range(1, len(df)):
        row   = df.iloc[i]
        price = float(row["close"])
        sig   = row["signal"]

        # Check SL / TP on open trade
        if open_trade_:
            side   = open_trade_["side"]
            entry  = open_trade_["entry"]
            qty    = open_trade_["qty"]
            sl     = open_trade_["sl"]
            tp     = open_trade_["tp"]

            closed = False
            status = "OPEN"

            if side == "BUY":
                if price <= sl:
                    closed, status = True, "SL"
                elif price >= tp:
                    closed, status = True, "TP"
            else:
                if price >= sl:
                    closed, status = True, "SL"
                elif price <= tp:
                    closed, status = True, "TP"

            if sig == "SELL" and side == "BUY":
                closed, status = True, "SIGNAL"
            elif sig == "BUY" and side == "SELL":
                closed, status = True, "SIGNAL"

            if closed:
                pnl = (price - entry) * qty if side == "BUY" else (entry - price) * qty
                balance += pnl
                open_trade_["exit"]   = price
                open_trade_["pnl"]    = round(pnl, 4)
                open_trade_["pnl_pct"] = round(pnl / (entry * qty) * 100, 2)
                open_trade_["status"] = status
                open_trade_["exit_bar"] = i
                trades.append(open_trade_)
                open_trade_ = None

        # Open new trade
        if open_trade_ is None and sig in ("BUY", "SELL"):
            capital = balance * position_size_pct
            qty     = capital / price
            if sig == "BUY":
                sl = price * (1 - stop_loss_pct)
                tp = price * (1 + take_profit_pct)
            else:
                sl = price * (1 + stop_loss_pct)
                tp = price * (1 - take_profit_pct)
            open_trade_ = {
                "side":      sig,
                "entry":     price,
                "entry_bar": i,
                "qty":       round(qty, 6),
                "sl":        round(sl, 2),
                "tp":        round(tp, 2),
            }

        equity_curve.append(balance)

    # Close any remaining open trade at last price
    if open_trade_:
        last_price = float(df.iloc[-1]["close"])
        side  = open_trade_["side"]
        entry = open_trade_["entry"]
        qty   = open_trade_["qty"]
        pnl   = (last_price - entry) * qty if side == "BUY" else (entry - last_price) * qty
        balance += pnl
        open_trade_["exit"]    = last_price
        open_trade_["pnl"]     = round(pnl, 4)
        open_trade_["pnl_pct"] = round(pnl / (entry * qty) * 100, 2)
        open_trade_["status"]  = "OPEN_CLOSE"
        open_trade_["exit_bar"] = len(df) - 1
        trades.append(open_trade_)
        equity_curve.append(balance)

    return _compute_metrics(trades, equity_curve, initial_balance, df)


def _compute_metrics(
    trades: list, equity_curve: list, initial_balance: float, df: pd.DataFrame
) -> dict:
    eq = np.array(equity_curve)
    trade_df = pd.DataFrame(trades) if trades else pd.DataFrame()

    total_trades = len(trades)
    winning      = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losing       = total_trades - winning
    win_rate     = (winning / total_trades * 100) if total_trades else 0.0

    total_pnl  = sum(t.get("pnl", 0) for t in trades)
    gross_win  = sum(t["pnl"] for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t["pnl"] for t in trades if t.get("pnl", 0) < 0))
    profit_factor = (gross_win / gross_loss) if gross_loss else float("inf")

    # Max drawdown
    peak       = np.maximum.accumulate(eq)
    drawdown   = (peak - eq) / peak
    max_dd     = float(np.max(drawdown)) * 100 if len(drawdown) > 0 else 0.0

    # Sharpe ratio (daily returns approximation)
    returns = np.diff(eq) / eq[:-1]
    sharpe  = (float(np.mean(returns)) / float(np.std(returns)) * np.sqrt(252)) \
              if len(returns) > 1 and np.std(returns) > 0 else 0.0

    final_balance = float(eq[-1]) if len(eq) > 0 else initial_balance
    total_return  = (final_balance - initial_balance) / initial_balance * 100

    return {
        "total_trades":   total_trades,
        "winning":        winning,
        "losing":         losing,
        "win_rate":       round(win_rate, 2),
        "total_pnl":      round(total_pnl, 2),
        "total_return":   round(total_return, 2),
        "profit_factor":  round(profit_factor, 3),
        "max_drawdown":   round(max_dd, 2),
        "sharpe_ratio":   round(sharpe, 3),
        "initial_balance": initial_balance,
        "final_balance":  round(final_balance, 2),
        "equity_curve":   equity_curve,
        "trades":         trades,
        "trade_df":       trade_df,
    }
