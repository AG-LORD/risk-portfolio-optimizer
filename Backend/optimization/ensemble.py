import logging
import os
from typing import Optional, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import StandardScaler


CLASS_LABELS = np.array(["SELL", "HOLD", "BUY"], dtype=object)

ENSEMBLE_FEATURE_METADATA = [
    {"key": "recent_return", "label": "Recent Return", "description": "1-day price return."},
    {"key": "volatility", "label": "Volatility", "description": "20-day daily volatility."},
    {"key": "momentum", "label": "Momentum", "description": "Trend direction over a 20-day horizon."},
    {"key": "sma_ratio", "label": "SMA Ratio", "description": "Price relative to 20-day moving average."},
    {"key": "ema_ratio", "label": "EMA Ratio", "description": "Price relative to 20-day EMA trend."},
    {"key": "rsi", "label": "RSI", "description": "Relative Strength Index."},
    {"key": "macd", "label": "MACD", "description": "Moving average convergence divergence."},
    {"key": "macd_signal", "label": "MACD Signal", "description": "MACD signal line."},
    {"key": "volume_change", "label": "Volume Change", "description": "5-day volume expansion or contraction."},
    {"key": "market_return", "label": "Market Return", "description": "Recent benchmark (NIFTY 50) 5-day return."},
    {"key": "sector_return", "label": "Sector Return", "description": "Average 5-day return of same-sector peers."},
    {"key": "sector_exposure", "label": "Sector Exposure", "description": "Sector representation in the universe/portfolio."},
    {"key": "risk_score", "label": "Risk Score", "description": "Risk signal derived from volatility."},
]
ENSEMBLE_FEATURE_ORDER = [feature["key"] for feature in ENSEMBLE_FEATURE_METADATA]
VOLATILITY_FEATURE_INDEX = ENSEMBLE_FEATURE_ORDER.index("volatility")
logger = logging.getLogger(__name__)


def _safe_float(value, default=0.0):
    value = float(value) if pd.notna(value) else default
    return value if np.isfinite(value) else default


def _compute_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(50.0)
    return rsi


def extract_ensemble_features_from_price_series(
    price_series: pd.Series,
    sector_exposure: float = 0.0,
    risk_score: Optional[float] = None,
    market_return: float = 0.0,
    sector_return: float = 0.0,
    volume_series: Optional[pd.Series] = None,
) -> np.ndarray:
    """Build one live/inference feature row for a single stock.

    This mirrors the feature engineering done in bulk over historical data by
    optimization/train_ensemble.py (build_training_data) as closely as
    possible, so a model trained on real market data sees the same kind of
    inputs at inference time (no train/serve skew). `market_return` and
    `sector_return` are computed by the caller (they depend on data this
    function doesn't have access to -- the benchmark index and sector
    peers) and simply passed through here.
    """
    prices = pd.Series(price_series).dropna().astype(float)
    if prices.empty:
        raise ValueError("Price series is empty.")

    returns = prices.pct_change().dropna()
    if returns.empty:
        raise ValueError("Not enough price history to calculate features.")

    recent_1d = _safe_float(prices.pct_change().iloc[-1]) if len(prices) >= 2 else 0.0
    recent_20d = _safe_float((prices.iloc[-1] / prices.iloc[-20] - 1.0)) if len(prices) >= 20 else recent_1d
    volatility = _safe_float(returns.tail(20).std(ddof=0))
    momentum = recent_20d

    sma_20 = prices.rolling(20, min_periods=5).mean()
    ema_20 = prices.ewm(span=20, adjust=False).mean()
    sma_ratio = _safe_float((prices.iloc[-1] / sma_20.iloc[-1]) - 1.0) if len(sma_20) else 0.0
    ema_ratio = _safe_float((prices.iloc[-1] / ema_20.iloc[-1]) - 1.0) if len(ema_20) else 0.0

    rsi = _compute_rsi(prices, 14).iloc[-1]
    ema_short = prices.ewm(span=12, adjust=False).mean()
    ema_long = prices.ewm(span=26, adjust=False).mean()
    macd = _safe_float((ema_short.iloc[-1] - ema_long.iloc[-1]))
    signal_line = (ema_short - ema_long).ewm(span=9, adjust=False).mean()
    macd_signal = _safe_float(signal_line.iloc[-1])

    volume = pd.Series(volume_series).dropna().astype(float) if volume_series is not None else pd.Series(dtype=float)
    if volume.empty or len(volume) < 6:
        volume_change = 0.0
    else:
        volume_change = _safe_float(volume.pct_change(5).iloc[-1])

    if risk_score is None:
        risk_score = 1.0 - min(max(volatility, 0.0), 1.0)

    feature_vector = [
        recent_1d,
        volatility,
        momentum,
        sma_ratio,
        ema_ratio,
        float(rsi),
        macd,
        macd_signal,
        volume_change,
        _safe_float(market_return),
        _safe_float(sector_return),
        _safe_float(sector_exposure),
        _safe_float(risk_score),
    ]
    return np.asarray(feature_vector, dtype=float).reshape(1, -1)


class SimpleEnsembleModel:
    """Leakage-safe three-model BUY/HOLD/SELL ensemble for real market data."""

    def __init__(self, model_dir: Optional[str] = None, weights: Optional[Sequence[float]] = None):
        self.model_dir = model_dir or os.getcwd()
        self.scaler = StandardScaler()
        self.base_models = [
            RidgeClassifier(class_weight="balanced", alpha=1.0),
            RandomForestClassifier(
                n_estimators=500,
                max_depth=12,
                min_samples_leaf=4,
                class_weight="balanced_subsample",
                random_state=42,
            ),
            HistGradientBoostingClassifier(
                learning_rate=0.05,
                max_depth=5,
                max_leaf_nodes=31,
                max_iter=500,
                random_state=42,
                class_weight="balanced",
            ),
        ]
        self.label_order = np.array(CLASS_LABELS, dtype=object)
        self.weights = np.array(weights if weights is not None else [1.0, 1.0, 1.0], dtype=float)
        self.feature_names = list(ENSEMBLE_FEATURE_ORDER)

    def _normalize_feature_matrix(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        expected = len(self.feature_names)
        if X.shape[1] < expected:
            pad = np.zeros((X.shape[0], expected - X.shape[1]), dtype=float)
            X = np.hstack([X, pad])
        elif X.shape[1] > expected:
            X = X[:, :expected]

        negative_volatility = X[:, VOLATILITY_FEATURE_INDEX] < 0
        if np.any(negative_volatility):
            X = X.copy()
            X[negative_volatility, VOLATILITY_FEATURE_INDEX] = 0.0
        return X

    def _sort_probability_matrix(self, proba, model):
        if proba.ndim == 1:
            proba = proba.reshape(1, -1)
        classes = np.asarray(model.classes_, dtype=object)
        ordered = np.zeros((proba.shape[0], len(self.label_order)), dtype=float)
        for idx, label in enumerate(self.label_order):
            if label in classes:
                class_index = np.where(classes == label)[0][0]
                ordered[:, idx] = proba[:, class_index]
        if ordered.sum(axis=1).sum() == 0:
            ordered = np.full((proba.shape[0], len(self.label_order)), 1.0 / len(self.label_order), dtype=float)
        ordered /= ordered.sum(axis=1, keepdims=True)
        return ordered

    def _get_model_proba(self, model, X_scaled):
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_scaled)
            return self._sort_probability_matrix(proba, model)
        if hasattr(model, "decision_function"):
            scores = model.decision_function(X_scaled)
            if scores.ndim == 1:
                scores = scores[:, np.newaxis]
            scores = scores - scores.max(axis=1, keepdims=True)
            exp_scores = np.exp(scores)
            proba = exp_scores / exp_scores.sum(axis=1, keepdims=True)
            if proba.shape[1] != len(self.label_order):
                classes = np.asarray(model.classes_, dtype=object)
                ordered = np.zeros((proba.shape[0], len(self.label_order)), dtype=float)
                for idx, label in enumerate(self.label_order):
                    if label in classes:
                        class_index = np.where(classes == label)[0][0]
                        if class_index < proba.shape[1]:
                            ordered[:, idx] = proba[:, class_index]
                if ordered.sum(axis=1).sum() == 0:
                    ordered = np.full((proba.shape[0], len(self.label_order)), 1.0 / len(self.label_order), dtype=float)
                else:
                    ordered /= ordered.sum(axis=1, keepdims=True)
                return ordered
            return self._sort_probability_matrix(proba, model)
        raise AttributeError(f"Model {type(model).__name__} does not expose predict_proba or decision_function.")

    def _weighted_probabilities(self, X_scaled):
        probability_stack = np.stack([self._get_model_proba(model, X_scaled) for model in self.base_models], axis=0)
        weighted_proba = np.tensordot(self.weights, probability_stack, axes=([0], [0]))
        weighted_proba /= weighted_proba.sum(axis=1, keepdims=True)
        return weighted_proba

    def fit(self, X, y, X_val=None, y_val=None):
        X = self._normalize_feature_matrix(X)
        y = np.asarray(y, dtype=object)
        y = np.char.upper(np.asarray([str(v) for v in y]))
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        for model in self.base_models:
            model.fit(X_scaled, y)

        if X_val is not None and y_val is not None:
            X_val = self._normalize_feature_matrix(X_val)
            y_val = np.char.upper(np.asarray([str(v) for v in y_val]))
            val_scaled = self.scaler.transform(X_val)
            scores = []
            for model in self.base_models:
                pred = model.predict(val_scaled)
                score = f1_score(y_val, pred, average="weighted", labels=self.label_order)
                scores.append(max(score, 1e-6))
            self.weights = np.asarray(scores, dtype=float)
            self.weights = self.weights / self.weights.sum()
        else:
            self.weights = np.full(len(self.base_models), 1.0 / len(self.base_models), dtype=float)
        return self

    def predict(self, X):
        """Continuous BUY-SELL conviction score in roughly [-1, 1]."""
        X = self._normalize_feature_matrix(X)
        X_scaled = self.scaler.transform(X)
        weighted_proba = self._weighted_probabilities(X_scaled)
        buy = weighted_proba[:, np.where(self.label_order == "BUY")[0][0]]
        sell = weighted_proba[:, np.where(self.label_order == "SELL")[0][0]]
        return buy - sell

    def predict_labels(self, X):
        X = self._normalize_feature_matrix(X)
        X_scaled = self.scaler.transform(X)
        weighted_proba = self._weighted_probabilities(X_scaled)
        predicted_index = weighted_proba.argmax(axis=1)
        return self.label_order[predicted_index]

    def predict_with_confidence(self, X):
        """Kept for compatibility with signals/composite_score.py and app.py,
        which were written against the older regression-style API. Returns
        (predicted_score, signal, confidence, probability_by_label) where
        predicted_score is the same BUY-SELL conviction score as predict()."""
        X = self._normalize_feature_matrix(X)
        X_scaled = self.scaler.transform(X)
        weighted_proba = self._weighted_probabilities(X_scaled)

        buy_idx = int(np.where(self.label_order == "BUY")[0][0])
        sell_idx = int(np.where(self.label_order == "SELL")[0][0])
        predicted_score = float(weighted_proba[0, buy_idx] - weighted_proba[0, sell_idx])

        signal_idx = int(weighted_proba[0].argmax())
        signal = str(self.label_order[signal_idx])
        confidence = float(weighted_proba[0, signal_idx])
        probability_by_label = {str(label): float(weighted_proba[0, i]) for i, label in enumerate(self.label_order)}

        return predicted_score, signal, confidence, probability_by_label

    def get_base_predictions(self, X):
        X = self._normalize_feature_matrix(X)
        X_scaled = self.scaler.transform(X)
        results = []
        for model in self.base_models:
            proba = self._get_model_proba(model, X_scaled)
            buy = proba[:, np.where(self.label_order == "BUY")[0][0]]
            sell = proba[:, np.where(self.label_order == "SELL")[0][0]]
            results.append(buy - sell)
        return results

    def explain(self, X):
        """Simple feature-ablation explanation on the BUY-SELL conviction
        score, matching the semantics of the pre-refactor regression model's
        explain() so app.py's /ensemble/explain route keeps working."""
        X = self._normalize_feature_matrix(X)
        prediction = float(self.predict(X)[0])

        if hasattr(self.scaler, "mean_"):
            baseline = np.asarray(self.scaler.mean_, dtype=float)
        else:
            baseline = np.zeros(X.shape[1], dtype=float)

        contributions = {}
        for i, feature_name in enumerate(self.feature_names):
            X_ablated = np.array(X, copy=True)
            X_ablated[:, i] = baseline[i]
            ablated_prediction = float(self.predict(X_ablated)[0])
            contributions[feature_name] = prediction - ablated_prediction

        return {
            "prediction": prediction,
            "contributions": dict(
                sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)
            ),
            "method": "feature_ablation",
        }

    def save(self, filename: str = "ensemble_model.joblib"):
        path = os.path.join(self.model_dir, filename)
        joblib.dump(
            {
                "scaler": self.scaler,
                "models": self.base_models,
                "weights": self.weights,
                "feature_names": self.feature_names,
                "label_order": self.label_order,
            },
            path,
        )
        return path

    def load(self, filename: str = "ensemble_model.joblib"):
        path = os.path.join(self.model_dir, filename)
        data = joblib.load(path)
        self.scaler = data["scaler"]
        self.base_models = data["models"]
        self.weights = np.asarray(data["weights"], dtype=float)
        self.feature_names = list(data.get("feature_names", ENSEMBLE_FEATURE_ORDER))
        self.label_order = np.asarray(data.get("label_order", CLASS_LABELS), dtype=object)
        return self
