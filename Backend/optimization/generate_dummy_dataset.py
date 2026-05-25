import argparse
from pathlib import Path

from ensemble import build_dummy_ensemble_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate a realistic synthetic regression dataset")
    parser.add_argument("--output", type=str, default="Backend/data/dummy_training.csv", help="Output CSV path")
    parser.add_argument("--samples", type=int, default=2000, help="Number of rows to generate")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = build_dummy_ensemble_dataset(n_samples=args.samples, random_state=args.random_state)
    df.to_csv(output_path, index=False)

    class_balance = df["label"].value_counts(normalize=True).sort_index() * 100
    print("Class balance:")
    for label, percent in class_balance.items():
        print(f"  {label}: {percent:.2f}%")

    hold_percent = float(class_balance.get("HOLD", 0.0))
    if hold_percent > 60.0:
        # Expected: financial markets are mostly HOLD because strong buy/sell signals are less common.
        print("Note: HOLD is above 60%, which is expected for market-like synthetic data.")

    print(f"Synthetic dataset saved to: {output_path}")


if __name__ == "__main__":
    main()
