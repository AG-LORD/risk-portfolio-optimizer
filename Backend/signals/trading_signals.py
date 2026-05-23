import numpy as np
import pandas as pd
from data.stock_sectors import get_sector


def _calculate_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    rs = avg_gain / (avg_loss + 1e-12)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def _moving_average_signal(sma20, sma50):
    if np.isnan(sma20) or np.isnan(sma50):
        return "HOLD"
    if sma20 > sma50:
        return "BUY"
    if sma20 < sma50:
        return "SELL"
    return "HOLD"


def _rsi_signal(rsi_value):
    if np.isnan(rsi_value):
        return "HOLD"
    if rsi_value < 30:
        return "BUY"
    if rsi_value > 70:
        return "SELL"
    return "HOLD"


def _momentum_signal(price_series):
    if price_series.empty or len(price_series) < 11:
        return "HOLD"

    momentum_10d = float(price_series.pct_change(periods=10).iloc[-1])

    if np.isnan(momentum_10d):
        return "HOLD"
    if momentum_10d > 0.03:
        return "BUY"
    if momentum_10d < -0.03:
        return "SELL"
    return "HOLD"


def _combined_signal(rsi_value, sma20, sma50, price_series):
    if np.isnan(rsi_value) or np.isnan(sma20) or np.isnan(sma50):
        return "HOLD"

    score = 0

    if rsi_value < 30:
        score += 2
    elif rsi_value < 40:
        score += 1
    elif rsi_value > 70:
        score -= 2
    elif rsi_value > 60:
        score -= 1

    if sma20 > sma50:
        score += 1
    elif sma20 < sma50:
        score -= 1

    momentum_signal = _momentum_signal(price_series)
    if momentum_signal == "BUY":
        score += 1
    elif momentum_signal == "SELL":
        score -= 1

    if score >= 2:
        return "BUY"
    if score <= -2:
        return "SELL"
    return "HOLD"


def _confidence_from_rsi(rsi_value):
    if np.isnan(rsi_value):
        return 0.0
    confidence = abs(float(rsi_value) - 50.0) / 50.0
    return float(np.clip(confidence, 0.0, 1.0))


def _resolve_price_series(price_data, stock, ticker):
    columns = list(price_data.columns)
    if ticker in price_data.columns:
        return price_data[ticker].dropna()
    if stock in price_data.columns:
        return price_data[stock].dropna()
    if len(columns) == 1:
        return price_data[columns[0]].dropna()
    return pd.Series(dtype=float)


def generate_signals(price_data, stocks, tickers):
    signals = []

    for stock, ticker in zip(stocks, tickers):
        price_series = _resolve_price_series(price_data, stock, ticker)
        if price_series.empty:
            signals.append({
                "stock": stock,
                "sector": get_sector(stock),
                "signal": "HOLD",
                "confidence": 0.0,
                "rsi": None,
                "sma20": None,
                "sma50": None
            })
            continue

        rsi_series = _calculate_rsi(price_series, period=14)
        rsi_value = float(rsi_series.iloc[-1]) if not rsi_series.empty else np.nan
        sma20 = float(price_series.rolling(window=20, min_periods=20).mean().iloc[-1])
        sma50 = float(price_series.rolling(window=50, min_periods=50).mean().iloc[-1])

        momentum_signal = _momentum_signal(price_series)
        signal = _combined_signal(rsi_value, sma20, sma50, price_series)
        confidence = _confidence_from_rsi(rsi_value)

        signals.append({
            "stock": stock,
            "sector": get_sector(stock),
            "signal": signal,
            "confidence": round(confidence, 2),
            "rsi": None if np.isnan(rsi_value) else round(rsi_value, 2),
            "sma20": None if np.isnan(sma20) else round(sma20, 2),
            "sma50": None if np.isnan(sma50) else round(sma50, 2),
            "rsi_signal": _rsi_signal(rsi_value),
            "ma_signal": _moving_average_signal(sma20, sma50),
            "momentum_signal": momentum_signal
        })

    return signals


def generate_portfolio_signal(signals):
    if not signals:
        return "HOLD"

    total = len(signals)
    buy_count = sum(1 for item in signals if item.get("signal") == "BUY")
    sell_count = sum(1 for item in signals if item.get("signal") == "SELL")

    if buy_count / total > 0.6:
        return "BUY"
    if sell_count / total > 0.6:
        return "SELL"
    return "HOLD"
