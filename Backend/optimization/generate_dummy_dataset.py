import argparse
from pathlib import Path

from ensemble import build_dummy_ensemble_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate a dummy regression dataset")
    parser.add_argument("--output", type=str, default="Backend/data/dummy_training.csv", help="Output CSV path")
    parser.add_argument("--samples", type=int, default=100, help="Number of rows to generate")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = build_dummy_ensemble_dataset(n_samples=args.samples, random_state=args.random_state)
    df.to_csv(output_path, index=False)
    print(f"Dummy dataset saved to: {output_path}")


if __name__ == "__main__":
    main()
