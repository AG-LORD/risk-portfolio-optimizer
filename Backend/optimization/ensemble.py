import os
from typing import Any, Dict, List, Optional, Sequence

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

    recent_return = float(prices.pct_change(periods=5).iloc[-1]) if len(prices) >= 6 else float(returns.iloc[-1])
    volatility = float(returns.rolling(window=20).std().iloc[-1]) if len(returns) >= 20 else float(returns.std())
    momentum = float(prices.pct_change(periods=20).iloc[-1]) if len(prices) >= 21 else float(returns.tail(5).sum())

    if np.isnan(recent_return):
        recent_return = 0.0
    if np.isnan(volatility) or volatility == 0.0:
        volatility = float(returns.std()) if not returns.empty else 0.0
    if np.isnan(momentum):
        momentum = 0.0

    if risk_score is None:
        risk_score = -volatility

    feature_vector = [
        recent_return,
        volatility,
        momentum,
        float(sector_exposure),
        float(risk_score),
    ]
    return np.asarray(feature_vector, dtype=float).reshape(1, -1)


def build_dummy_ensemble_dataset(n_samples: int = 100, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)
    data: Dict[str, Any] = {}

    for key in ENSEMBLE_FEATURE_ORDER:
        if key == "recent_return":
            data[key] = rng.normal(0.02, 0.05, size=n_samples)
        elif key == "volatility":
            data[key] = np.abs(rng.normal(0.15, 0.05, size=n_samples))
        elif key == "momentum":
            data[key] = rng.normal(0.05, 0.15, size=n_samples)
        elif key == "sector_exposure":
            data[key] = rng.normal(0.5, 0.3, size=n_samples)
        elif key == "risk_score":
            data[key] = rng.normal(-0.1, 0.25, size=n_samples)

    df = pd.DataFrame(data)
    df["target"] = (
        0.5 * df["recent_return"]
        - 1.2 * df["volatility"]
        + 1.4 * df["momentum"]
        + 0.8 * df["sector_exposure"]
        + 0.6 * df["risk_score"]
        + rng.normal(0.0, 0.1, size=n_samples)
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
        X = np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X)

        predictions = np.column_stack([model.predict(X_scaled) for model in self.base_models])
        return np.average(predictions, axis=1, weights=self.weights)

    def get_base_predictions(self, X):
        X = np.asarray(X, dtype=float)
        X_scaled = self.scaler.transform(X)
        return [model.predict(X_scaled) for model in self.base_models]

    def save(self, filename: str = "ensemble_model.joblib"):
        path = os.path.join(self.model_dir, filename)
        joblib.dump({
            "scaler": self.scaler,
            "models": self.base_models,
            "weights": self.weights,
        }, path)
        return path

    def load(self, filename: str = "ensemble_model.joblib"):
        path = os.path.join(self.model_dir, filename)
        data = joblib.load(path)
        self.scaler = data["scaler"]
        self.base_models = data["models"]
        self.weights = np.asarray(data["weights"], dtype=float)
        return self
