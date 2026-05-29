import yfinance as yf
import pandas as pd


def fetch_ohlcv(
    symbol="RELIANCE.NS",
    interval="1d",
    period="1y"
):
    """
    Fetch OHLCV data from Yahoo Finance for Indian stocks.
    
    Args:
        symbol: Stock symbol (e.g., "RELIANCE.NS", "TCS.NS")
        interval: Timeframe (1d, 1wk)
        period: Period to fetch (1mo, 3mo, 6mo, 1y, 2y, 5y, max)
    
    Returns:
        DataFrame with OHLCV data indexed by timestamp
    """
    try:
        data = yf.download(
            symbol,
            interval=interval,
            period=period,
            progress=False
        )
        
        if data is None or data.empty or len(data) < 20:
            if interval in {"1d", "1wk"}:
                print(f"Insufficient data for {symbol}. Trying with max history...")
                data = yf.download(
                    symbol,
                    interval="1d",
                    period="max",
                    progress=False
                )
            else:
                return None
        
        if data is None or data.empty:
            print(f"Still no data for {symbol}")
            return None
        
        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            # Flatten MultiIndex: extract Price level (Close, High, Low, Open, Volume)
            data.columns = data.columns.get_level_values(0)
        
        # Normalize column names to match expected format
        data.columns = data.columns.str.capitalize()
        
        # Keep only OHLCV columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        available_cols = [col for col in required_cols if col in data.columns]
        data = data[available_cols]
        
        # Remove rows with NaN values
        data = data.dropna()
        
        # Sort by index (ascending time order)
        data = data.sort_index()
        
        print(f"✓ Fetched {len(data)} candles for {symbol}")
        return data if len(data) > 0 else None
    
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def get_available_symbols():
    """
    Returns a list of commonly traded Indian NSE stocks.
    """
    return [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "ITC.NS",
        "LT.NS",
        "KOTAKBANK.NS",
        "AXISBANK.NS",
        "BHARTIARTL.NS",
        "ASIANPAINT.NS",
        "MARUTI.NS",
        "SUNPHARMA.NS",
        "TITAN.NS",
        "ULTRACEMCO.NS",
        "BAJFINANCE.NS",
        "BAJAJFINSV.NS",
        "NESTLEIND.NS",
        "HCLTECH.NS",
        "WIPRO.NS",
        "TECHM.NS",
        "POWERGRID.NS",
        "NTPC.NS",
        "ONGC.NS",
        "COALINDIA.NS",
        "JSWSTEEL.NS",
        "TATASTEEL.NS",
        "HINDALCO.NS",
        "ADANIENT.NS",
        "ADANIPORTS.NS",
        "INDUSINDBK.NS",
        "DRREDDY.NS",
        "CIPLA.NS",
        "APOLLOHOSP.NS",
        "DIVISLAB.NS",
        "BRITANNIA.NS",
        "HEROMOTOCO.NS",
        "EICHERMOT.NS",
        "M&M.NS",
        "TATAMOTORS.NS",
        "BAJAJ-AUTO.NS",
        "GRASIM.NS",
        "SHREECEM.NS",
        "BPCL.NS",
        "IOC.NS",
        "HDFCLIFE.NS",
        "SBILIFE.NS",
        "ICICIPRULI.NS",
        "PIDILITIND.NS"
    ]