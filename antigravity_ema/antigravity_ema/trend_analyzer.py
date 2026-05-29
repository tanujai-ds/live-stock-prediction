"""
Anti-Gravity EMA Trading System
Trend Analyzer
"""
import pandas as pd
import numpy as np
from typing import Literal

TrendLabel = Literal["STRONG BULL", "BULL", "NEUTRAL", "BEAR", "STRONG BEAR"]


def get_trend_label(trend_strength: float) -> TrendLabel:
    """Map a numeric trend_strength value to a human label."""
    if trend_strength > 0.02:
        return "STRONG BULL"
    elif trend_strength > 0.005:
        return "BULL"
    elif trend_strength > -0.005:
        return "NEUTRAL"
    elif trend_strength > -0.02:
        return "BEAR"
    else:
        return "STRONG BEAR"


def get_trend_color(label: TrendLabel) -> str:
    """Return a hex colour for UI rendering."""
    return {
        "STRONG BULL": "#00c853",
        "BULL":        "#69f0ae",
        "NEUTRAL":     "#ffd740",
        "BEAR":        "#ff6d00",
        "STRONG BEAR": "#d50000",
    }.get(label, "#ffffff")


def analyze_trend(df: pd.DataFrame) -> dict:
    """
    Return a full trend summary for the latest candle.
    """
    if df.empty:
        return {}

    row = df.iloc[-1]
    ts  = float(row.get("trend_strength", 0))
    label = get_trend_label(ts)

    # Simple higher-highs / lower-lows over last 10 bars
    recent = df.tail(10)
    hh = recent["high"].is_monotonic_increasing
    ll = recent["low"].is_monotonic_decreasing

    return {
        "trend_strength":  ts,
        "trend_label":     label,
        "trend_color":     get_trend_color(label),
        "ema7":            float(row.get("ema7", 0)),
        "ema14":           float(row.get("ema14", 0)),
        "ema21":           float(row.get("ema21", 0)),
        "higher_highs":    bool(hh),
        "lower_lows":      bool(ll),
        "vol_ratio":       float(row.get("vol_ratio", 1)),
        "price":           float(row["close"]),
    }
