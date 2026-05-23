import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split

from ensemble import ENSEMBLE_FEATURE_ORDER, SimpleEnsembleModel


def load_csv_data(path: str, target_column: str = "target"):
    df = pd.read_csv(path)
    missing = [col for col in ENSEMBLE_FEATURE_ORDER + [target_column] if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in dataset: {', '.join(missing)}")

    X = df[ENSEMBLE_FEATURE_ORDER]
    y = df[target_column]
    return X, y


def main():
    parser = argparse.ArgumentParser(description="Train the simple ensemble model")
    parser.add_argument("--dataset", type=str, required=True, help="Path to training CSV file")
    parser.add_argument("--target", type=str, default="target", help="Target column name")
    parser.add_argument("--output", type=str, default="ensemble_model.joblib", help="Output model filename")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test size fraction")
    parser.add_argument("--random-state", type=int, default=42, help="Random state for train/test split")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    X, y = load_csv_data(str(dataset_path), target_column=args.target)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=args.random_state
    )

    model = SimpleEnsembleModel(model_dir=str(dataset_path.parent))
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    mse = mean_squared_error(y_test, predictions)
    print(f"Test MSE: {mse:.4f}")

    model_path = model.save(filename=args.output)
    print(f"Saved ensemble model to: {model_path}")


if __name__ == "__main__":
    main()
