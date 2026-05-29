"""
Anti-Gravity EMA Trading System
Main Streamlit Dashboard
"""

from datetime import datetime, time
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from ta.momentum import RSIIndicator
from streamlit_autorefresh import st_autorefresh

from config import config
from data_fetcher import fetch_ohlcv, get_available_symbols
from indicators import add_all_indicators
from signal_engine import latest_signal
from trend_analyzer import analyze_trend, get_trend_label


st.set_page_config(
    page_title="Anti-Gravity EMA System",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Market hours gate: only show UI between 09:15 and 15:30 IST ---
try:
    from zoneinfo import ZoneInfo
    tz = ZoneInfo("Asia/Kolkata")
except Exception:
    import pytz
    tz = pytz.timezone("Asia/Kolkata")

now = datetime.now(tz)
market_start = time(9, 15)
market_end = time(15, 30)

if not (market_start <= now.time() <= market_end):
    st.info(f"Market closed — open 09:15 to 15:30 IST. Current: {now.strftime('%Y-%m-%d %I:%M %p')}")
    st.stop()

st.markdown(
    """
    <style>
        .stApp {
            background: radial-gradient(circle at top, #132238 0%, #0e1117 45%, #090b10 100%);
            color: #e8eef7;
        }
        .metric-card {
            background: rgba(20, 28, 44, 0.92);
            border: 1px solid rgba(110, 132, 166, 0.35);
            border-radius: 14px;
            padding: 16px 18px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
        }
        .signal-buy { color: #16d67e; font-size: 2rem; font-weight: 800; }
        .signal-sell { color: #ff6b6b; font-size: 2rem; font-weight: 800; }
        .signal-hold { color: #ffd166; font-size: 2rem; font-weight: 800; }
        div[data-testid="stMetricValue"] { color: #f7fbff; }
        div[data-testid="stMetricLabel"] { color: #9fb0c7; }
    </style>
    """,
    unsafe_allow_html=True,
)


def compute_signal_series(data: pd.DataFrame) -> pd.Series:
    signal = pd.Series("HOLD", index=data.index, dtype="object")
    bullish = (data["EMA7"] > data["EMA14"]) & (data["EMA14"] > data["EMA21"])
    bearish = (data["EMA7"] < data["EMA14"]) & (data["EMA14"] < data["EMA21"])
    signal.loc[bullish] = "BUY"
    signal.loc[bearish] = "SELL"
    return signal


def load_market_data(symbol: str, interval: str, period: str) -> pd.DataFrame | None:
    data = fetch_ohlcv(symbol=symbol, interval=interval, period=period)
    if data is None or data.empty:
        return None

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(set(data.columns)):
        return None

    return data.sort_index().copy()


def add_rsi(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    rsi = RSIIndicator(close=result["Close"], window=14)
    result["RSI"] = rsi.rsi()
    return result


def add_display_columns(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    result["open"] = result["Open"]
    result["high"] = result["High"]
    result["low"] = result["Low"]
    result["close"] = result["Close"]
    result["volume"] = result["Volume"]
    result["ema7"] = result["EMA7"]
    result["ema14"] = result["EMA14"]
    result["ema21"] = result["EMA21"]
    result["trend_strength"] = (result["EMA7"] - result["EMA21"]) / result["Close"]
    result["signal"] = compute_signal_series(result)
    return result


def get_period_options(interval: str) -> list[str]:
    if interval in {"1m", "5m"}:
        return ["1d", "5d", "1mo"]
    if interval in {"15m", "1h", "4h"}:
        return ["5d", "1mo", "3mo", "6mo"]
    return ["1mo", "3mo", "6mo", "1y"]


def get_time_axis_format(interval: str) -> tuple[str, str]:
    if interval in {"1m", "5m", "15m", "1h", "4h"}:
        return "%b %d\n%I:%M %p", "Date / Time (AM/PM)"
    return "%b %d", "Date"


def get_interval_delta(interval: str) -> timedelta:
    return {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "1h": timedelta(hours=1),
        "4h": timedelta(hours=4),
        "1d": timedelta(days=1),
        "1wk": timedelta(days=7),
    }.get(interval, timedelta(days=1))


def predict_next_close(data: pd.DataFrame, interval: str) -> dict:
    recent = data.tail(8).copy()
    latest = recent.iloc[-1]
    last_close = float(latest["Close"])
    returns = recent["Close"].pct_change().dropna()
    mean_return = float(returns.tail(5).mean()) if not returns.empty else 0.0
    trend_strength = float(latest.get("trend_strength", 0.0))
    signal = str(latest.get("signal", "HOLD"))

    bias = 0.002 if signal == "BUY" else -0.002 if signal == "SELL" else 0.0
    forecast_return = (0.7 * mean_return) + (0.3 * trend_strength) + bias
    forecast_return = max(min(forecast_return, 0.08), -0.08)
    predicted_close = max(last_close * (1 + forecast_return), 0.01)
    forecast_time = data.index[-1] + get_interval_delta(interval)

    if predicted_close > last_close * 1.002:
        direction = "UP"
    elif predicted_close < last_close * 0.998:
        direction = "DOWN"
    else:
        direction = "SIDEWAYS"

    return {
        "forecast_time": forecast_time,
        "predicted_close": predicted_close,
        "forecast_return": forecast_return,
        "direction": direction,
    }


st.title("🚀 Anti-Gravity EMA Trading Dashboard")
st.caption("Real-time market scanner with EMA trend signals and RSI confirmation")

# Refresh the dashboard every 60 seconds so the chart and table stay live.
st_autorefresh(interval=60000, key="anti_gravity_live_refresh")

with st.sidebar:
    st.header("Market Settings")
    symbol = st.selectbox("Symbol", get_available_symbols(), index=0)
    interval = st.selectbox("Interval", config.TIMEFRAMES, index=config.TIMEFRAMES.index(config.TIMEFRAME))
    period_options = get_period_options(interval)
    period = st.selectbox("Period", period_options, index=min(1, len(period_options) - 1))
    st.caption(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")

with st.spinner(f"Loading {symbol}..."):
    raw_data = load_market_data(symbol, interval, period)

if raw_data is None:
    st.error("No chart data was returned for the selected symbol/timeframe. Try a different pair or interval.")
    st.stop()

if len(raw_data) < 21:
    st.warning("Not enough candles to build the chart yet. Try a longer period.")
    st.stop()

featured = add_all_indicators(raw_data.copy())
featured = add_rsi(featured)
featured = add_display_columns(featured)

latest_row = featured.iloc[-1]
signal = latest_signal(featured)
trend_info = analyze_trend(featured)
trend_label = trend_info.get("trend_label", get_trend_label(float(latest_row.get("trend_strength", 0))))
forecast = predict_next_close(featured, interval)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Last Price", f"{latest_row['Close']:.2f}")
col2.metric("Signal", signal)
col3.metric("Trend", trend_label)
col4.metric("RSI", f"{latest_row['RSI']:.2f}" if pd.notna(latest_row.get("RSI")) else "n/a")
col5.metric("Prediction", f"{forecast['predicted_close']:.2f}", delta=f"{forecast['forecast_return'] * 100:+.2f}%")

st.markdown("### Live Trading Chart")
st.caption(f"{'AM/PM time' if interval in {'1m', '5m', '15m', '1h', '4h'} else 'Date only'} view with a one-step single-day forecast.")

fig = go.Figure()

# Candlestick trace
fig.add_trace(
    go.Candlestick(
        x=featured.index,
        open=featured["Open"],
        high=featured["High"],
        low=featured["Low"],
        close=featured["Close"],
        name="Candles",
        increasing_line_color="#16d67e",
        decreasing_line_color="#ff6b6b",
    )
)

# EMA lines with hover signal information
ema_config = [
    ("EMA7", featured["EMA7"], "#7dd3fc", "Cyan"),
    ("EMA14", featured["EMA14"], "#fbbf24", "Yellow"),
    ("EMA21", featured["EMA21"], "#fb7185", "Pink"),
]

for ema_name, ema_values, color, color_name in ema_config:
    fig.add_trace(
        go.Scatter(
            x=featured.index,
            y=ema_values,
            mode="lines",
            name=ema_name,
            line=dict(color=color, width=2),
            hovertemplate=(
                "<b>%{x|%Y-%m-%d %I:%M %p}</b><br>"
                f"<b>{ema_name}:</b> %{{y:.2f}}<br>"
                "<extra></extra>"
            ),
        )
    )

# Add signal markers on hover (invisible markers at EMA points)
signal_customdata = featured[["signal", "RSI", "Close"]].to_numpy()
fig.add_trace(
    go.Scatter(
        x=featured.index,
        y=featured["EMA7"],
        mode="markers",
        name="Signal Data",
        marker=dict(size=0.1, opacity=0),
        customdata=signal_customdata,
        hovertemplate=(
            "<b>%{x|%Y-%m-%d %I:%M %p}</b><br>"
            "<b>Signal:</b> %{customdata[0]}<br>"
            "<b>RSI:</b> %{customdata[1]:.2f}<br>"
            "<b>Close:</b> %{customdata[2]:.2f}<br>"
            "<extra></extra>"
        ),
        showlegend=False,
    )
)

fig.add_trace(
    go.Scatter(
        x=[featured.index[-1], forecast["forecast_time"]],
        y=[float(latest_row["Close"]), float(forecast["predicted_close"])],
        mode="lines+markers",
        name="Prediction",
        line=dict(color="#00bcd4", width=2, dash="dash"),
        marker=dict(size=7, color="#00bcd4"),
        hovertemplate=(
            "<b>%{x|%Y-%m-%d %I:%M %p}</b><br>"
            "<b>Predicted Close:</b> %{y:.2f}<br>"
            "<extra></extra>"
        ),
    )
)

fig.update_layout(
    template="plotly_dark",
    title={
        "text": f"<b>{symbol}</b> {interval.upper()} Live Chart",
        "x": 0.5,
        "xanchor": "center",
        "font": {"size": 20, "color": "#e8eef7"},
    },
    height=800,
    margin=dict(l=50, r=50, t=80, b=50),
    xaxis_rangeslider_visible=False,
    xaxis_rangeselector_visible=False,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01,
        bgcolor="rgba(20, 28, 44, 0.7)",
        bordercolor="#6e84a6",
        borderwidth=1,
    ),
    paper_bgcolor="rgba(9, 11, 16, 0.95)",
    plot_bgcolor="rgba(15, 20, 32, 0.95)",
    font=dict(family="Inter, Segoe UI, sans-serif", color="#e8eef7", size=11),
    hovermode="x unified",
)

fig.update_xaxes(
    showgrid=True,
    gridwidth=1,
    gridcolor="rgba(255, 255, 255, 0.05)",
    zeroline=False,
    rangeslider_visible=False,
    showspikes=True,
    spikemode="across",
    spikesnap="cursor",
    spikecolor="rgba(125, 211, 252, 0.3)",
    tickformat=get_time_axis_format(interval)[0],
    title_text=get_time_axis_format(interval)[1],
)

fig.update_yaxes(
    showgrid=True,
    gridwidth=1,
    gridcolor="rgba(255, 255, 255, 0.05)",
    zeroline=False,
    side="right",
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

st.markdown("### Latest Candles")
st.dataframe(
    featured[["Open", "High", "Low", "Close", "Volume", "EMA7", "EMA14", "EMA21", "RSI", "signal"]].tail(25),
    use_container_width=True,
)
