from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "retailrocket"
CONFIG_PATH = ROOT / "configs" / "retailrocket.json"


def main() -> None:
    try:
        import kagglesdk.kaggle_env as kaggle_env

        if not hasattr(kaggle_env, "get_web_endpoint") and hasattr(kaggle_env, "get_endpoint"):
            kaggle_env.get_web_endpoint = kaggle_env.get_endpoint
        import kagglehub
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "kagglehub is not installed. Install it first:\n"
            "conda run -n rtdetr python -m pip install kagglehub"
        ) from exc

    dataset_path = Path(kagglehub.dataset_download("retailrocket/ecommerce-dataset"))
    print(f"Downloaded dataset path: {dataset_path}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in ["events.csv", "item_properties_part1.csv", "item_properties_part2.csv", "category_tree.csv"]:
        src = dataset_path / name
        if src.exists():
            dst = DATA_DIR / name
            shutil.copy2(src, dst)
            copied.append(str(dst))

    events_path = DATA_DIR / "events.csv"
    if not events_path.exists():
        raise FileNotFoundError(f"events.csv not found in {dataset_path}")

    template_path = ROOT / "configs" / "retailrocket.template.json"
    with template_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    config["behaviors_path"] = str(events_path.as_posix())
    config["orders_path"] = ""
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print("Copied files:")
    for path in copied:
        print(f"  {path}")
    print(f"Generated config: {CONFIG_PATH}")
    print("Run:")
    print(f"  conda run -n rtdetr python -m retail_algorithm.src.retail_algo.cli --config {CONFIG_PATH}")


if __name__ == "__main__":
    main()
