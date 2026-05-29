"""
Anti-Gravity EMA Trading System
Risk Manager — stop-loss, take-profit, position sizing, daily loss cap
"""
from config import config


class RiskManager:
    def __init__(self, balance: float = config.INITIAL_BALANCE):
        self.initial_balance = balance
        self.balance         = balance
        self.daily_loss      = 0.0
        self.daily_loss_cap  = balance * config.MAX_DAILY_LOSS_PCT

    def position_size(self, price: float) -> float:
        """How many units to buy given current balance and position size %."""
        capital = self.balance * config.POSITION_SIZE_PCT
        return round(capital / price, 6)

    def stop_loss_price(self, entry: float, side: str = "BUY") -> float:
        if side == "BUY":
            return round(entry * (1 - config.STOP_LOSS_PCT), 2)
        return round(entry * (1 + config.STOP_LOSS_PCT), 2)

    def take_profit_price(self, entry: float, side: str = "BUY") -> float:
        if side == "BUY":
            return round(entry * (1 + config.TAKE_PROFIT_PCT), 2)
        return round(entry * (1 - config.TAKE_PROFIT_PCT), 2)

    def can_trade(self) -> bool:
        """Returns False if daily loss cap has been hit."""
        return self.daily_loss < self.daily_loss_cap

    def record_loss(self, loss: float) -> None:
        """Track losses for the day (pass positive value)."""
        self.daily_loss += abs(loss)

    def reset_daily(self) -> None:
        self.daily_loss = 0.0

    def update_balance(self, pnl: float) -> None:
        self.balance = max(0.0, self.balance + pnl)

    def risk_reward_ratio(self) -> float:
        return config.TAKE_PROFIT_PCT / config.STOP_LOSS_PCT

    def summary(self) -> dict:
        return {
            "balance":          round(self.balance, 2),
            "daily_loss":       round(self.daily_loss, 2),
            "daily_loss_cap":   round(self.daily_loss_cap, 2),
            "can_trade":        self.can_trade(),
            "risk_reward":      self.risk_reward_ratio(),
            "position_size_pct": config.POSITION_SIZE_PCT * 100,
            "stop_loss_pct":    config.STOP_LOSS_PCT * 100,
            "take_profit_pct":  config.TAKE_PROFIT_PCT * 100,
        }
