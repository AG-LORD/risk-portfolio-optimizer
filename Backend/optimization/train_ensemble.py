import argparse
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_fscore_support,
    r2_score,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from data.fetch_data import fetch_ohlcv_data, fetch_benchmark_data
from data.stock_sectors import STOCK_SECTORS, get_sector
from optimization.ensemble import CLASS_LABELS, ENSEMBLE_FEATURE_ORDER, SimpleEnsembleModel

BENCHMARK_TICKER = "^NSEI"


def classify_future_returns(returns, lower_quantile=0.25, upper_quantile=0.75):
    lower = np.quantile(returns, lower_quantile)
    upper = np.quantile(returns, upper_quantile)
    if not np.isfinite(lower) or not np.isfinite(upper):
        lower, upper = -0.015, 0.015
    labels = np.full(len(returns), "HOLD", dtype=object)
    labels[np.asarray(returns) > upper] = "BUY"
    labels[np.asarray(returns) < lower] = "SELL"
    return labels, lower, upper


def build_sector_exposures(symbols):
    counts = pd.Series([get_sector(symbol) for symbol in STOCK_SECTORS]).value_counts()
    exposures = {}
    for symbol in symbols:
        sector = get_sector(symbol)
        exposures[symbol] = counts.get(sector, 0.0) / max(len(STOCK_SECTORS), 1)
    return exposures


def _compute_rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def build_training_data(ohlcv_by_ticker, benchmark_close, forecast_horizon=5):
    if not ohlcv_by_ticker:
        raise ValueError("No OHLCV data were downloaded for training.")

    all_tickers = list(ohlcv_by_ticker)
    exposures = build_sector_exposures(all_tickers)
    frames = []
    benchmark = benchmark_close.sort_index().astype(float)

    for ticker, df in ohlcv_by_ticker.items():
        if df.empty:
            continue
        close = pd.Series(df["Close"]).dropna().astype(float)
        volume = pd.Series(df.get("Volume", pd.Series(np.nan, index=close.index))).dropna().astype(float)
        if close.empty:
            continue
        combined = pd.DataFrame({"close": close, "volume": volume.reindex(close.index).ffill().bfill()})
        combined["ret_1d"] = combined["close"].pct_change(1)
        combined["ret_20d"] = combined["close"].pct_change(20)
        combined["volatility_20d"] = combined["ret_1d"].rolling(20, min_periods=2).std(ddof=0)
        combined["sma_20"] = combined["close"].rolling(20, min_periods=5).mean()
        combined["ema_20"] = combined["close"].ewm(span=20, adjust=False).mean()
        combined["sma_ratio"] = combined["close"] / combined["sma_20"] - 1.0
        combined["ema_ratio"] = combined["close"] / combined["ema_20"] - 1.0
        combined["rsi_14"] = _compute_rsi(combined["close"], 14)
        ema_short = combined["close"].ewm(span=12, adjust=False).mean()
        ema_long = combined["close"].ewm(span=26, adjust=False).mean()
        combined["macd"] = ema_short - ema_long
        combined["macd_signal"] = combined["macd"].ewm(span=9, adjust=False).mean()
        combined["volume_change"] = combined["volume"].pct_change(5)
        combined["market_return"] = benchmark.reindex(combined.index).pct_change(5).fillna(0.0)
        sector_tickers = [symbol for symbol in all_tickers if get_sector(symbol) == get_sector(ticker)]
        sector_data = pd.concat(
            [ohlcv_by_ticker[symbol]["Close"].rename(symbol) for symbol in sector_tickers if symbol in ohlcv_by_ticker],
            axis=1,
        )
        if not sector_data.empty:
            sector_return = sector_data.pct_change(5).mean(axis=1).reindex(combined.index).fillna(0.0)
        else:
            sector_return = pd.Series(0.0, index=combined.index)
        combined["sector_return"] = sector_return.reindex(combined.index).fillna(0.0)
        combined["sector_exposure"] = exposures.get(ticker, 0.0)
        combined["risk_score"] = 1.0 - combined["volatility_20d"].clip(lower=0.0, upper=1.0)
        combined["future_return"] = combined["close"].shift(-forecast_horizon) / combined["close"] - 1.0
        combined["date"] = combined.index
        combined["ticker"] = ticker

        good = combined.dropna(subset=["future_return", "ret_1d", "volatility_20d", "volume_change", "market_return", "sector_return"]).copy()
        rows = []
        for row in good.itertuples(index=False):
            rows.append({
                "date": row.date,
                "ticker": row.ticker,
                "recent_return": float(row.ret_1d),
                "volatility": float(row.volatility_20d),
                "momentum": float(row.ret_20d),
                "sma_ratio": float(row.sma_ratio),
                "ema_ratio": float(row.ema_ratio),
                "rsi": float(row.rsi_14),
                "macd": float(row.macd),
                "macd_signal": float(row.macd_signal),
                "volume_change": float(row.volume_change),
                "market_return": float(row.market_return),
                "sector_return": float(row.sector_return),
                "sector_exposure": float(row.sector_exposure),
                "risk_score": float(row.risk_score),
                "future_return": float(row.future_return),
            })
        if rows:
            frames.extend(rows)

    if not frames:
        raise ValueError("No usable training rows were generated from the downloaded market data.")

    data = pd.DataFrame(frames)
    data = data.replace([np.inf, -np.inf], np.nan).dropna().sort_values("date").reset_index(drop=True)
    labels, _, _ = classify_future_returns(data["future_return"].to_numpy(), lower_quantile=0.25, upper_quantile=0.75)
    data["label"] = labels
    return data


def time_split(data, val_size=0.15, test_size=0.2, forecast_horizon=5):
    dates = sorted(pd.to_datetime(data["date"]).unique())
    if len(dates) < 12:
        raise ValueError("Not enough distinct dates for a valid time-based split.")

    val_cut = int(len(dates) * (1.0 - test_size - val_size))
    test_cut = int(len(dates) * (1.0 - test_size))
    if val_cut <= forecast_horizon or test_cut <= val_cut + forecast_horizon:
        raise ValueError("The requested split leaves too little data for validation or testing.")

    train_end = dates[val_cut - 1] - pd.Timedelta(days=forecast_horizon)
    val_end = dates[test_cut - 1] - pd.Timedelta(days=forecast_horizon)
    train = data[data["date"] <= train_end].copy()
    val = data[(data["date"] > train_end) & (data["date"] <= val_end)].copy()
    test = data[data["date"] > val_end].copy()

    if train.empty or val.empty or test.empty:
        raise ValueError("The time split produced an empty train, validation, or test set.")
    return train, val, test, train_end, val_end


def evaluate_classification(y_true, y_pred):
    precision, recall, f1_weighted, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=CLASS_LABELS, average="weighted", zero_division=0
    )
    f1_macro = f1_score(y_true, y_pred, average="macro", labels=CLASS_LABELS, zero_division=0)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision_weighted": precision,
        "recall_weighted": recall,
        "f1_weighted": f1_weighted,
        "f1_macro": f1_macro,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=CLASS_LABELS),
    }


def evaluate_regression(y_true, y_pred):
    return {
        "mse": mean_squared_error(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred) ** 0.5,
        "mae": mean_absolute_error(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
    }


def fit_and_select_model(model_name, base_model, X_train, y_train, X_val, y_val):
    if model_name == "ridge":
        candidates = [{"alpha": alpha} for alpha in [0.1, 0.5, 1.0, 5.0, 10.0]]
    elif model_name == "random_forest":
        candidates = [
            {"n_estimators": n, "max_depth": depth, "min_samples_leaf": leaf}
            for n, depth, leaf in product([300, 500], [None, 12], [2, 4])
        ]
    else:
        candidates = [
            {"learning_rate": lr, "max_depth": depth, "max_leaf_nodes": leaf}
            for lr, depth, leaf in product([0.03, 0.05], [3, 5], [15, 31])
        ]

    best_score = -1.0
    best_model = None
    best_params = None
    for params in candidates:
        candidate = clone(base_model)
        candidate.set_params(**params)
        candidate.fit(X_train, y_train)
        val_pred = candidate.predict(X_val)
        score = f1_score(y_val, val_pred, average="weighted", labels=CLASS_LABELS, zero_division=0)
        if score > best_score:
            best_score = score
            best_model = candidate
            best_params = params
    return best_model, best_params, best_score


def main():
    parser = argparse.ArgumentParser(description="Train the ensemble on yfinance historical market data")
    parser.add_argument("--period", default="5y", help="yfinance lookback period")
    parser.add_argument("--test-size", type=float, default=0.2, help="Latest-date fraction reserved for final evaluation")
    parser.add_argument("--val-size", type=float, default=0.15, help="Validation fraction before the final test period")
    parser.add_argument("--forecast-horizon", type=int, default=5, help="Lookahead horizon in trading days")
    parser.add_argument("--output", default=str(BACKEND_DIR / "data" / "ensemble_model.joblib"))
    args = parser.parse_args()

    if not 0 < args.test_size < 1:
        raise ValueError("--test-size must be between 0 and 1.")
    if not 0 < args.val_size < 1:
        raise ValueError("--val-size must be between 0 and 1.")
    if args.forecast_horizon < 1:
        raise ValueError("--forecast-horizon must be at least 1.")

    tickers = [f"{symbol}.NS" for symbol in STOCK_SECTORS]
    ohlcv_by_ticker, valid_tickers, _ = fetch_ohlcv_data(tickers, period=args.period, interval="1d")
    if not valid_tickers:
        raise RuntimeError("No yfinance OHLCV data were available for training.")

    benchmark_close = fetch_benchmark_data(BENCHMARK_TICKER, period=args.period)

    data = build_training_data(
        {ticker: ohlcv_by_ticker[ticker] for ticker in valid_tickers},
        benchmark_close,
        forecast_horizon=args.forecast_horizon,
    )
    train, val, test, train_end, val_end = time_split(data, val_size=args.val_size, test_size=args.test_size, forecast_horizon=args.forecast_horizon)

    print(f"Stocks used: {len(valid_tickers)}")
    print(f"Date range: train {train['date'].min()} -> {train['date'].max()} | validation {val['date'].min()} -> {val['date'].max()} | test {test['date'].min()} -> {test['date'].max()}")
    print(f"Class distribution (train):\n{train['label'].value_counts().reindex(CLASS_LABELS, fill_value=0)}")
    print(f"Baseline majority-class weighted F1 on validation: {f1_score(val['label'], np.full(len(val), 'HOLD', dtype=object), average='weighted', labels=CLASS_LABELS, zero_division=0):.6f}")

    model_specs = {
        "ridge": SimpleEnsembleModel().base_models[0],
        "random_forest": SimpleEnsembleModel().base_models[1],
        "hist_gradient_boosting": SimpleEnsembleModel().base_models[2],
    }

    trained_models = {}
    for name, base_model in model_specs.items():
        tuned_model, best_params, best_score = fit_and_select_model(
            name,
            base_model,
            train[ENSEMBLE_FEATURE_ORDER].to_numpy(),
            train["label"].to_numpy(),
            val[ENSEMBLE_FEATURE_ORDER].to_numpy(),
            val["label"].to_numpy(),
        )
        trained_models[name] = tuned_model
        print(f"{name} tuned params: {best_params} | validation weighted F1: {best_score:.6f}")

    model = SimpleEnsembleModel(model_dir=str(BACKEND_DIR / "data"))
    model.base_models = [trained_models["ridge"], trained_models["random_forest"], trained_models["hist_gradient_boosting"]]
    model.fit(
        train[ENSEMBLE_FEATURE_ORDER].to_numpy(),
        train["label"].to_numpy(),
        X_val=val[ENSEMBLE_FEATURE_ORDER].to_numpy(),
        y_val=val["label"].to_numpy(),
    )

    learned_weights = model.weights.copy()
    equal_weights = np.full(len(model.base_models), 1.0 / len(model.base_models), dtype=float)
    print("Learned ensemble weights:")
    for name, weight in zip(["ridge", "random_forest", "hist_gradient_boosting"], learned_weights):
        print(f"  {name}: {weight:.6f}")

    def ensemble_predictions_for_weights(X, weights):
        X = np.asarray(X, dtype=float)
        scaled = model.scaler.transform(model._normalize_feature_matrix(X))
        prob_stack = [model._get_model_proba(base_model, scaled) for base_model in model.base_models]
        probs = np.stack(prob_stack, axis=0)
        weighted = np.tensordot(weights, probs, axes=([0], [0]))
        weighted /= weighted.sum(axis=1, keepdims=True)
        return weighted

    val_equal = ensemble_predictions_for_weights(val[ENSEMBLE_FEATURE_ORDER].to_numpy(), equal_weights)
    val_learned = ensemble_predictions_for_weights(val[ENSEMBLE_FEATURE_ORDER].to_numpy(), learned_weights)
    val_label_equal = model.label_order[val_equal.argmax(axis=1)]
    val_label_learned = model.label_order[val_learned.argmax(axis=1)]
    print(f"Validation equal-weight F1: {f1_score(val['label'], val_label_equal, average='weighted', labels=CLASS_LABELS, zero_division=0):.6f}")
    print(f"Validation learned-weight F1: {f1_score(val['label'], val_label_learned, average='weighted', labels=CLASS_LABELS, zero_division=0):.6f}")

    test_scaled = model.scaler.transform(model._normalize_feature_matrix(test[ENSEMBLE_FEATURE_ORDER].to_numpy()))
    prob_stack = np.stack([model._get_model_proba(m, test_scaled) for m in model.base_models], axis=0)
    test_probs = np.tensordot(learned_weights, prob_stack, axes=([0], [0]))
    test_probs /= test_probs.sum(axis=1, keepdims=True)
    test_pred_labels = model.label_order[test_probs.argmax(axis=1)]
    test_pred_score = test_probs[:, np.where(model.label_order == "BUY")[0][0]] - test_probs[:, np.where(model.label_order == "SELL")[0][0]]

    class_metrics = evaluate_classification(test["label"].to_numpy(), test_pred_labels)
    regression_metrics = evaluate_regression(test["future_return"].to_numpy(), test_pred_score)
    print("\nFinal test metrics:")
    print(f"  Accuracy: {class_metrics['accuracy']:.6f}")
    print(f"  Precision (weighted): {class_metrics['precision_weighted']:.6f}")
    print(f"  Recall (weighted): {class_metrics['recall_weighted']:.6f}")
    print(f"  F1-score (weighted): {class_metrics['f1_weighted']:.6f}")
    print(f"  F1-score (macro): {class_metrics['f1_macro']:.6f}")
    print(f"  MSE: {regression_metrics['mse']:.6f} | RMSE: {regression_metrics['rmse']:.6f} | MAE: {regression_metrics['mae']:.6f} | R2: {regression_metrics['r2']:.6f}")
    print("  Confusion matrix (rows=actual SELL/HOLD/BUY, cols=pred SELL/HOLD/BUY):")
    print(class_metrics["confusion_matrix"])

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    saved_path = model.save(filename=output_path.name)
    print(f"Saved final model to: {saved_path}")


if __name__ == "__main__":
    main()
