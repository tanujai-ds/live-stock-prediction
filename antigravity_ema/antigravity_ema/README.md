# 🚀 Anti-Gravity EMA Trading System

Free live crypto trading dashboard with EMA 7/14/21 signals, Binance data,
candlestick charts, paper trading, backtesting, and Telegram alerts.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set Binance API keys for private endpoints
export BINANCE_API_KEY=your_key
export BINANCE_SECRET=your_secret

# 3. (Optional) Telegram alerts
export TELEGRAM_TOKEN=your_bot_token
export TELEGRAM_CHAT_ID=your_chat_id

# 4. Launch dashboard
streamlit run dashboard.py
```

> **No API keys needed** for live market data — Binance public endpoints are free.

---

## Project Structure

```
antigravity_ema/
├── config.py          — All settings (EMA periods, risk %, Telegram, DB path)
├── database.py        — SQLite: candles / signals / trades / performance_metrics
├── data_fetcher.py    — Binance OHLCV via ccxt (free public API)
├── indicators.py      — EMA 7/14/21 + volume metrics + trend strength formula
├── signal_engine.py   — BUY / SELL / HOLD logic with crossover + volume filter
├── trend_analyzer.py  — Trend label, colour, direction analysis
├── paper_trading.py   — Virtual balance, SL/TP execution, P&L tracking
├── backtesting.py     — Historical strategy test: win rate, Sharpe, drawdown
├── alerts.py          — Telegram BUY/SELL/reversal notifications
├── risk_manager.py    — Position sizing, stop-loss, take-profit, daily loss cap
├── dashboard.py       — Streamlit app (4 tabs: Live | Backtest | Paper | Logs)
└── requirements.txt
```

---

## Trading Strategy

| Signal | Conditions |
|--------|-----------|
| **BUY**  | EMA7 > EMA14 > EMA21 + bullish crossover + volume ≥ 1.2× avg |
| **SELL** | EMA7 < EMA14 < EMA21 + bearish crossover + volume weakening |
| **HOLD** | Anything else |

**Trend Strength** = `(EMA7 − EMA21) / Price`

---

## Dashboard Tabs

1. **📊 Live** — Candlestick chart, EMA overlays, BUY/SELL arrows, trend meter, signal history
2. **🔬 Backtest** — Run the strategy on historical candles, equity curve, metrics
3. **💼 Paper Trading** — Virtual balance, trade history, P&L chart
4. **📋 Logs & DB** — Raw signal and trade tables, AI upgrade slots

---

## Risk Settings (defaults)

| Parameter | Default |
|-----------|---------|
| Stop Loss | 2 % |
| Take Profit | 4 % |
| Position Size | 10 % of balance |
| Max Daily Loss | 5 % of balance |

All adjustable from the sidebar at runtime.

---

## Future AI Upgrades

The codebase is modular — plug in AI models by replacing or wrapping:

- `signal_engine.classify_signal()` → LSTM or Transformer predictions
- `indicators.add_all_indicators()` → add feature engineering
- `signals` table has an `ai_confidence` column ready to use
- `config.AI_ENABLED` flag to toggle AI mode

---

## Supported Pairs & Timeframes

**Pairs:** Any USDT pair on Binance (BTC, ETH, BNB, SOL, XRP…)  
**Timeframes:** 1m · 5m · 15m · 1h · 4h

---

*Built for the Anti-Gravity EMA System — free, open, modular.*
