import yfinance as yf
import pandas as pd


def _extract_price_data(raw):
    if raw.empty:
        return pd.DataFrame()

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

    data = data.copy()
    data = data.dropna(axis=1, how="all")
    if data.empty:
        return pd.DataFrame()

    return data.dropna(how="any")


def fetch_data(stocks, period="2y", interval="1d"):
    requested = list(stocks) if isinstance(stocks, (list, tuple, set, pd.Index)) else [stocks]
    requested = [str(s) for s in requested]

    raw = yf.download(
        requested,
        period=period,
        interval=interval
    )
    price_data = _extract_price_data(raw)

    if price_data.empty:
        failed_tickers = requested
        for ticker in failed_tickers:
            print(f"Warning: market data unavailable for {ticker}")
        return pd.DataFrame(), [], failed_tickers

    if len(requested) == 1 and len(price_data.columns) == 1 and requested[0] not in price_data.columns:
        price_data = price_data.rename(columns={price_data.columns[0]: requested[0]})

    valid_tickers = []
    for ticker in requested:
        if ticker in price_data.columns and not price_data[ticker].dropna().empty:
            valid_tickers.append(ticker)
        else:
            print(f"Warning: market data unavailable for {ticker}")

    failed_tickers = [ticker for ticker in requested if ticker not in valid_tickers]

    if not valid_tickers:
        return pd.DataFrame(), [], failed_tickers

    filtered_data = price_data[valid_tickers].copy()
    filtered_data = filtered_data.dropna(how="any")

    if filtered_data.empty:
        for ticker in valid_tickers:
            print(f"Warning: market data unavailable for {ticker}")
        failed_tickers = requested
        return pd.DataFrame(), [], failed_tickers

    return filtered_data, valid_tickers, failed_tickers


def fetch_benchmark_data(ticker="^NSEI", period="2y", interval="1d"):
    raw = yf.download(
        ticker,
        period=period,
        interval=interval
    )
    data = _extract_price_data(raw)
    if data.empty:
        return pd.Series(dtype=float)

    series = data.iloc[:, 0].copy()
    series.name = "benchmark"
    return series


def fetch_ohlcv_data(stocks, period="1y", interval="1d"):
    requested = (
        list(stocks)
        if isinstance(stocks, (list, tuple, set, pd.Index))
        else [stocks]
    )
    requested = [str(s) for s in requested]

    raw = yf.download(
        requested,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        progress=False,
        threads=False,
        actions=False,
    )

    if raw.empty:
        return {}, [], requested

    ohlcv_by_ticker = {}
    required = ["Open", "High", "Low", "Close", "Volume"]

    if isinstance(raw.columns, pd.MultiIndex):
        for ticker in requested:
            if ticker not in raw.columns.get_level_values(0):
                continue

            ticker_df = raw[ticker].copy()
            if not all(col in ticker_df.columns for col in required):
                continue

            ticker_df = ticker_df[required].dropna(how="all")
            if not ticker_df.empty:
                ohlcv_by_ticker[ticker] = ticker_df

    else:
        if all(col in raw.columns for col in required):
            ticker = requested[0]
            ohlcv_by_ticker[ticker] = raw[required].copy().dropna(how="all")

    valid_tickers = list(ohlcv_by_ticker.keys())
    failed_tickers = [
        ticker for ticker in requested
        if ticker not in valid_tickers
    ]

    for ticker in failed_tickers:
        print(f"Warning: OHLCV data unavailable for {ticker}")

    return ohlcv_by_ticker, valid_tickers, failed_tickers


def fetch_india_vix(period="1y", interval="1d"):
    raw = yf.download(
        "^INDIAVIX",
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        threads=False,
        actions=False,
    )

    if raw.empty:
        return pd.Series(dtype=float)

    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" not in raw.columns.get_level_values(0):
            return pd.Series(dtype=float)

        data = raw["Close"]
        series = data.iloc[:, 0] if isinstance(data, pd.DataFrame) else data
    else:
        if "Close" not in raw.columns:
            return pd.Series(dtype=float)

        series = raw["Close"]

    series = series.dropna().copy()
    series.name = "india_vix"

    return series
