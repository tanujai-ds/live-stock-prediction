"""
Anti-Gravity EMA Trading System
Paper Trading — virtual balance, simulated trade execution, P&L tracking
"""
import pandas as pd
from datetime import datetime
from typing import Optional
from config import config
from risk_manager import RiskManager
from database import open_trade, close_trade, load_trades


class PaperTrader:
    def __init__(self, initial_balance: float = config.INITIAL_BALANCE):
        self.rm              = RiskManager(initial_balance)
        self.open_trade_id:  Optional[int] = None
        self.open_side:      Optional[str] = None
        self.open_price:     Optional[float] = None
        self.open_quantity:  Optional[float] = None
        self.open_sl:        Optional[float] = None
        self.open_tp:        Optional[float] = None

    # ── Public API ──────────────────────────────────────────────────────────

    def on_signal(self, signal: str, price: float, symbol: str) -> Optional[dict]:
        """
        Process a new signal.
        Returns a trade event dict if a trade was opened/closed, else None.
        """
        if not self.rm.can_trade():
            return None

        event = None

        # Close existing position on opposite signal
        if self.open_trade_id and signal in ("BUY", "SELL"):
            if (signal == "BUY" and self.open_side == "SELL") or \
               (signal == "SELL" and self.open_side == "BUY"):
                event = self._close(price, "CLOSED")

        # Check stop-loss / take-profit on current bar
        if self.open_trade_id:
            sl_event = self._check_sl_tp(price)
            if sl_event:
                return sl_event

        # Open new position
        if not self.open_trade_id and signal in ("BUY", "SELL"):
            event = self._open(signal, price, symbol)

        return event

    def portfolio(self) -> dict:
        trades_df = load_trades()
        closed = trades_df[trades_df["status"] != "OPEN"]

        total_pnl   = float(closed["pnl"].sum()) if not closed.empty else 0.0
        wins        = int((closed["pnl"] > 0).sum()) if not closed.empty else 0
        losses      = int((closed["pnl"] <= 0).sum()) if not closed.empty else 0
        total       = wins + losses
        win_rate    = (wins / total * 100) if total else 0.0

        return {
            "balance":      round(self.rm.balance, 2),
            "total_pnl":    round(total_pnl, 2),
            "total_trades": total,
            "wins":         wins,
            "losses":       losses,
            "win_rate":     round(win_rate, 1),
            "open_trade":   self.open_trade_id,
            "open_side":    self.open_side,
            "open_price":   self.open_price,
        }

    # ── Private helpers ─────────────────────────────────────────────────────

    def _open(self, side: str, price: float, symbol: str) -> dict:
        qty = self.rm.position_size(price)
        sl  = self.rm.stop_loss_price(price, side)
        tp  = self.rm.take_profit_price(price, side)

        trade_id = open_trade({
            "symbol":      symbol,
            "side":        side,
            "entry_price": price,
            "quantity":    qty,
            "stop_loss":   sl,
            "take_profit": tp,
            "entry_time":  datetime.utcnow().isoformat(),
            "notes":       "Paper trade",
        })

        self.open_trade_id = trade_id
        self.open_side     = side
        self.open_price    = price
        self.open_quantity = qty
        self.open_sl       = sl
        self.open_tp       = tp

        return {
            "event":    "OPEN",
            "trade_id": trade_id,
            "side":     side,
            "price":    price,
            "qty":      qty,
            "sl":       sl,
            "tp":       tp,
        }

    def _close(self, price: float, status: str = "CLOSED") -> dict:
        close_trade(self.open_trade_id, price, status)

        raw_pnl = (price - self.open_price) * self.open_quantity
        if self.open_side == "SELL":
            raw_pnl = -raw_pnl

        self.rm.update_balance(raw_pnl)
        if raw_pnl < 0:
            self.rm.record_loss(raw_pnl)

        event = {
            "event":    "CLOSE",
            "trade_id": self.open_trade_id,
            "status":   status,
            "entry":    self.open_price,
            "exit":     price,
            "pnl":      round(raw_pnl, 2),
        }

        self.open_trade_id = None
        self.open_side     = None
        self.open_price    = None
        self.open_quantity = None
        self.open_sl       = None
        self.open_tp       = None

        return event

    def _check_sl_tp(self, price: float) -> Optional[dict]:
        if not self.open_trade_id:
            return None
        if self.open_side == "BUY":
            if price <= self.open_sl:
                return self._close(price, "SL")
            if price >= self.open_tp:
                return self._close(price, "TP")
        else:
            if price >= self.open_sl:
                return self._close(price, "SL")
            if price <= self.open_tp:
                return self._close(price, "TP")
        return None
