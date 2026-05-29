from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from retail_algorithm.src.retail_algo.data_io import load_orders, save_csv


DEFAULT_INPUT = r"E:\EdgeDownload\online+retail+ii\online_retail_II.xlsx"
DEFAULT_OUTPUT = "retail_algorithm/data/uci_online_retail_ii/orders.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare UCI Online Retail II dataset.")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Path to online_retail_II.xlsx")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output normalized CSV path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(input_path)

    orders = load_orders(input_path)
    save_csv(orders, args.output)
    print(f"Input: {input_path}")
    print(f"Output: {Path(args.output).resolve()}")
    print(f"Rows: {len(orders)}")
    print(f"Customers: {orders['customer_id'].nunique()}")
    print(f"Products: {orders['product_id'].nunique()}")
    print("Run:")
    print(
        "  conda run -n rtdetr python -m retail_algorithm.src.retail_algo.cli "
        "--config retail_algorithm/configs/uci_online_retail_ii.json"
    )


if __name__ == "__main__":
    main()
