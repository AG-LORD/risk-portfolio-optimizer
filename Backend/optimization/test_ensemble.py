import numpy as np
from sklearn.datasets import make_regression
from sklearn.metrics import mean_squared_error

from ensemble import SimpleEnsembleModel


def test_simple_ensemble():
    X, y = make_regression(n_samples=200, n_features=10, noise=10.0, random_state=42)
    n_train = int(0.8 * len(X))

    X_train, X_test = X[:n_train], X[n_train:]
    y_train, y_test = y[:n_train], y[n_train:]

    model = SimpleEnsembleModel()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    assert preds.shape == y_test.shape
    assert np.isfinite(preds).all()
    assert mean_squared_error(y_test, preds) < 5000


if __name__ == "__main__":
    test_simple_ensemble()
    print("Ensemble test passed.")
