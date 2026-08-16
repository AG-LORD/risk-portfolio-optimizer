import sys
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from optimization.ensemble import (
    CLASS_LABELS,
    ENSEMBLE_FEATURE_ORDER,
    SimpleEnsembleModel,
)


def _make_test_data(n_samples=150):
    rng = np.random.default_rng(42)
    n_features = len(ENSEMBLE_FEATURE_ORDER)
    X = rng.normal(size=(n_samples, n_features))
    y = np.array(["SELL", "HOLD", "BUY"] * (n_samples // 3))
    return X, y


def test_classification_ensemble():
    X, y = _make_test_data(150)
    model = SimpleEnsembleModel()
    model.fit(X, y)
    predicted = model.predict_labels(X[:20])
    assert predicted.shape == (20,)
    assert np.all(np.isin(predicted, CLASS_LABELS))


def test_classification_predictions():
    X, y = _make_test_data(150)
    model = SimpleEnsembleModel()
    model.fit(X, y)
    scores = model.predict(X[:20])
    assert scores.shape == (20,)
    assert np.isfinite(scores).all()
    assert np.isfinite(model.weights).all()
    assert np.isclose(model.weights.sum(), 1.0, atol=1e-6)
    assert np.all(model.weights >= 0.0)
    base_predictions = model.get_base_predictions(X[:20])
    assert len(base_predictions) == 3
    for prediction in base_predictions:
        assert prediction.shape == (20,)
        assert np.isfinite(prediction).all()


def test_predict_with_confidence_and_explain():
    X, y = _make_test_data(150)
    model = SimpleEnsembleModel()
    model.fit(X, y)
    score, signal, confidence, probabilities = model.predict_with_confidence(X[:1])
    assert signal in ("BUY", "HOLD", "SELL")
    assert 0.0 <= confidence <= 1.0
    assert set(probabilities.keys()) == {"BUY", "HOLD", "SELL"}
    assert np.isclose(sum(probabilities.values()), 1.0, atol=1e-6)

    explanation = model.explain(X[:1])
    assert set(explanation["contributions"].keys()) == set(ENSEMBLE_FEATURE_ORDER)


def test_saved_model_loads():
    model_dir = BACKEND_DIR / "data"
    model_path = model_dir / "ensemble_model.joblib"
    if not model_path.exists():
        raise AssertionError(
            f"Trained model not found at {model_path}. "
            "Run train_ensemble.py first."
        )
    model = SimpleEnsembleModel(model_dir=str(model_dir)).load()
    assert model is not None
    assert len(ENSEMBLE_FEATURE_ORDER) > 0
    assert len(model.base_models) == 3
    assert list(model.feature_names) == list(ENSEMBLE_FEATURE_ORDER)
    X = np.zeros((2, len(ENSEMBLE_FEATURE_ORDER)), dtype=float)
    predictions = model.predict_labels(X)
    assert predictions.shape == (2,)
    assert np.all(np.isin(predictions, CLASS_LABELS))


if __name__ == "__main__":
    test_classification_ensemble()
    test_classification_predictions()
    test_predict_with_confidence_and_explain()
    test_saved_model_loads()
    print("Ensemble classification tests passed.")
