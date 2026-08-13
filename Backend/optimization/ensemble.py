import os
import logging
from typing import Optional, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ENSEMBLE_FEATURE_METADATA = [
    {"key": "recent_return", "label": "Recent Return", "description": "Latest price return change."},
    {"key": "volatility", "label": "Volatility", "description": "Short-term price movement size."},
    {"key": "momentum", "label": "Momentum", "description": "Direction and speed of trend."},
    {"key": "sector_exposure", "label": "Sector Exposure", "description": "Industry weight signal."},
    {"key": "risk_score", "label": "Risk Score", "description": "Risk signal for the asset mix."},
]
ENSEMBLE_FEATURE_ORDER = [feature["key"] for feature in ENSEMBLE_FEATURE_METADATA]
VOLATILITY_FEATURE_INDEX = ENSEMBLE_FEATURE_ORDER.index("volatility")
logger = logging.getLogger(__name__)


def extract_ensemble_features_from_price_series(
    price_series: pd.Series,
    sector_exposure: float = 0.0,
    risk_score: Optional[float] = None,
) -> np.ndarray:
    prices = price_series.dropna().astype(float)
    if prices.empty:
        raise ValueError("Price series is empty.")

    returns = prices.pct_change().dropna()
    if returns.empty:
        raise ValueError("Not enough price history to calculate features.")

    recent_return = (
        float((prices.iloc[-1] - prices.iloc[-7]) / prices.iloc[-7])
        if len(prices) >= 7
        else float(returns.iloc[-1])
    )
    volatility = float(returns.std())
    momentum = (
        float((prices.iloc[-1] - prices.iloc[-30]) / prices.iloc[-30])
        if len(prices) >= 30
        else float(returns.tail(5).sum())
    )

    if np.isnan(recent_return):
        recent_return = 0.0
    if np.isnan(volatility) or volatility == 0.0:
        volatility = float(returns.std()) if not returns.empty else 0.0
    if np.isnan(momentum):
        momentum = 0.0

    if risk_score is None:
        risk_score = 1 - volatility

    feature_vector = [
        recent_return,
        volatility,
        momentum,
        float(sector_exposure),
        float(risk_score),
    ]
    return np.asarray(feature_vector, dtype=float).reshape(1, -1)


def build_dummy_ensemble_dataset(n_samples: int = 2000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    recent_return = rng.uniform(-0.15, 0.20, size=n_samples)
    volatility = np.abs(rng.normal(0.18, 0.07, size=n_samples))
    momentum = rng.uniform(-0.20, 0.25, size=n_samples)
    sector_exposure = rng.uniform(0.1, 1.5, size=n_samples)
    risk_score = -0.6 * volatility + 0.4 * momentum + rng.normal(0.0, 0.05, size=n_samples)

    target = (
        0.6 * recent_return
        - 0.8 * volatility
        + 1.2 * momentum
        + 0.3 * sector_exposure
        + 0.5 * risk_score
        + rng.normal(0.0, 0.03, size=n_samples)
    )
    target = np.clip(target, -0.3, 0.4)

    df = pd.DataFrame({
        "recent_return": recent_return,
        "volatility": volatility,
        "momentum": momentum,
        "sector_exposure": sector_exposure,
        "risk_score": risk_score,
        "target": target,
    })
    df["label"] = np.select(
        [df["target"] > 0.05, df["target"] < -0.05],
        ["BUY", "SELL"],
        default="HOLD",
    )
    return df


class SimpleEnsembleModel:
    """Simple ensemble model for regression predictions.

    This ensemble fits three base regressors and averages their predictions.
    It is intentionally simple so the ML part is easy to extend later.
    """

    def __init__(self, model_dir: Optional[str] = None, weights: Optional[Sequence[float]] = None):
        self.model_dir = model_dir or os.getcwd()
        self.scaler = StandardScaler()
        self.base_models = [
            Ridge(alpha=1.0, random_state=42),
            RandomForestRegressor(n_estimators=100, random_state=42),
            HistGradientBoostingRegressor(random_state=42),
        ]
        self.weights = np.array(weights if weights is not None else [1.0, 1.0, 1.0], dtype=float)
        self.classifier = None

    def _prepare_inference_features(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if X.shape[1] > VOLATILITY_FEATURE_INDEX:
            negative_volatility = X[:, VOLATILITY_FEATURE_INDEX] < 0
            if np.any(negative_volatility):
                logger.warning("Negative volatility feature received during inference; clipping to 0.0.")
                X = X.copy()
                X[negative_volatility, VOLATILITY_FEATURE_INDEX] = 0.0

        return X

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)

        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        for model in self.base_models:
            model.fit(X_scaled, y)

        self.weights = self.weights / np.sum(self.weights)
        return self

    def predict(self, X):
        X = self._prepare_inference_features(X)
        X_scaled = self.scaler.transform(X)

        predictions = np.column_stack([model.predict(X_scaled) for model in self.base_models])
        return np.average(predictions, axis=1, weights=self.weights)

    def get_base_predictions(self, X):
        X = self._prepare_inference_features(X)
        X_scaled = self.scaler.transform(X)
        return [model.predict(X_scaled) for model in self.base_models]

    def predict_with_confidence(self, X):
        X = self._prepare_inference_features(X)
        X_scaled = self.scaler.transform(X)
        predicted_return = float(self.predict(X)[0])

        if self.classifier is not None and hasattr(self.classifier, "predict_proba"):
            probabilities = self.classifier.predict_proba(X_scaled)[0]
            classes = [str(label) for label in self.classifier.classes_]
            probability_by_label = {
                label: float(probability)
                for label, probability in zip(classes, probabilities)
            }
            signal = max(probability_by_label, key=probability_by_label.get)
            confidence = float(probability_by_label[signal])
            for label in ("BUY", "HOLD", "SELL"):
                probability_by_label.setdefault(label, 0.0)
            return predicted_return, signal, confidence, probability_by_label

        base_predictions = np.asarray(self.get_base_predictions(X), dtype=float).reshape(len(self.base_models), -1)[:, 0]
        if predicted_return > 0.05:
            signal = "BUY"
        elif predicted_return < -0.05:
            signal = "SELL"
        else:
            signal = "HOLD"

        disagreement = float(np.std(base_predictions))
        confidence = float(np.clip(1.0 - disagreement / 0.20, 0.0, 1.0))
        probability_by_label = {"BUY": 0.0, "HOLD": 0.0, "SELL": 0.0}
        probability_by_label[signal] = confidence
        remaining = (1.0 - confidence) / 2.0
        for label in probability_by_label:
            if label != signal:
                probability_by_label[label] = remaining

        return predicted_return, signal, confidence, probability_by_label

    def explain(self, X):
        X = self._prepare_inference_features(X)
        prediction = float(self.predict(X)[0])

        if hasattr(self.scaler, "mean_"):
            baseline = np.asarray(self.scaler.mean_, dtype=float)
        else:
            baseline = np.zeros(X.shape[1], dtype=float)

        contributions = {}
        for i, feature_name in enumerate(ENSEMBLE_FEATURE_ORDER):
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
        joblib.dump({
            "scaler": self.scaler,
            "models": self.base_models,
            "weights": self.weights,
            "classifier": self.classifier,
        }, path)
        return path

    def load(self, filename: str = "ensemble_model.joblib"):
        path = os.path.join(self.model_dir, filename)
        data = joblib.load(path)
        self.scaler = data["scaler"]
        self.base_models = data["models"]
        self.weights = np.asarray(data["weights"], dtype=float)
        self.classifier = data.get("classifier")
        return self
