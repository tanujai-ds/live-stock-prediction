import yfinance as yf
import pandas as pd

data = yf.download('RELIANCE.NS', period='1mo', interval='1d', progress=False)
print("Original columns:")
print(data.columns)
print(f"Is MultiIndex: {isinstance(data.columns, pd.MultiIndex)}")

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)
    print("\nAfter get_level_values(0):")
    print(data.columns)
    
data.columns = data.columns.str.capitalize()
print("\nAfter capitalize:")
print(data.columns)

required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
available_cols = [col for col in required_cols if col in data.columns]
print(f"\nAvailable cols: {available_cols}")
print(f"Data shape: {data.shape}")
