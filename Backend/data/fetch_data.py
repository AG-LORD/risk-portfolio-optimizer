import yfinance as yf
import pandas as pd

def fetch_data(stocks):

    raw = yf.download(
        stocks,
        period="2y",
        interval="1d"
    )
    if raw.empty:
        return pd.DataFrame()

    # yfinance output can vary by version/settings:
    # - MultiIndex columns for multiple tickers (Price, Ticker)
    # - Single-level columns for single ticker
    # - "Adj Close" may be absent; fall back to "Close"
    if isinstance(raw.columns, pd.MultiIndex):
        price_level = raw.columns.get_level_values(0)
        if "Adj Close" in price_level:
            data = raw["Adj Close"]
        elif "Close" in price_level:
            data = raw["Close"]
        else:
            return pd.DataFrame()
    else:
        if "Adj Close" in raw.columns:
            data = raw[["Adj Close"]].copy()
        elif "Close" in raw.columns:
            data = raw[["Close"]].copy()
        else:
            return pd.DataFrame()

    data = data.dropna(how="any")

    return data
