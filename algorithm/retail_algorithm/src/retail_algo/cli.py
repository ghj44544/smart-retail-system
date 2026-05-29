from __future__ import annotations

import argparse
from pathlib import Path

from .data_io import load_json
from .pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retail behavior algorithm pipeline.")
    parser.add_argument(
        "--config",
        default="retail_algorithm/configs/default.json",
        help="Path to JSON config.",
    )
    parser.add_argument("--behaviors", help="Override behavior data path.")
    parser.add_argument("--orders", help="Override order data path.")
    parser.add_argument("--output-dir", help="Override output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_json(args.config)
    if args.behaviors:
        config["behaviors_path"] = args.behaviors
    if args.orders:
        config["orders_path"] = args.orders
    if args.output_dir:
        config["output_dir"] = args.output_dir

    summary = run_pipeline(config)
    print("Retail algorithm pipeline finished.")
    print(f"Output directory: {summary['output_dir']}")
    print(f"Customers: {summary['customers']}, Products: {summary['products']}")
    print(f"Association rules: {summary['association_rules']}")
    print(f"Multi-behavior recommendations: {summary['multibehavior_recommendations']}")


if __name__ == "__main__":
    main()

