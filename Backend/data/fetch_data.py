import yfinance as yf
from datetime import datetime, timedelta

def fetch_data(stocks):
    end = datetime.today()
    start = end - timedelta(days=3*365)

    data = yf.download(
        stocks,
        start=start,
        end=end,
        auto_adjust=True
    )

    if isinstance(data.columns, tuple):
        data = data["Close"]
    else:
        data = data["Close"]

    return data.dropna()