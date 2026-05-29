from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


BEHAVIOR_ALIASES = {
    "visitorid": "customer_id",
    "visitor_id": "customer_id",
    "user_id": "customer_id",
    "userid": "customer_id",
    "itemid": "product_id",
    "item_id": "product_id",
    "sku_id": "product_id",
    "event": "behavior_type",
    "timestamp": "behavior_time",
}

ORDER_ALIASES = {
    "InvoiceNo": "order_id",
    "Invoice": "order_id",
    "invoice_no": "order_id",
    "CustomerID": "customer_id",
    "Customer ID": "customer_id",
    "customer": "customer_id",
    "StockCode": "product_id",
    "stock_code": "product_id",
    "Quantity": "quantity",
    "UnitPrice": "price",
    "Price": "price",
    "InvoiceDate": "order_time",
}

BEHAVIOR_TYPE_ALIASES = {
    "view": "view",
    "views": "view",
    "click": "view",
    "favorite": "favorite",
    "fav": "favorite",
    "collect": "favorite",
    "cart": "cart",
    "addtocart": "cart",
    "add_to_cart": "cart",
    "purchase": "purchase",
    "buy": "purchase",
    "transaction": "purchase",
    "transactions": "purchase",
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_output_dir(path: str | Path) -> Path:
    out = Path(path)
    out.mkdir(parents=True, exist_ok=True)
    return out


def _read_table(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input file not found: {p}")
    suffix = p.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(p)
    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(p, sheet_name=None)
        return pd.concat(sheets.values(), ignore_index=True)
    if suffix == ".parquet":
        return pd.read_parquet(p)
    raise ValueError(f"Unsupported file type: {suffix}")


def _rename_aliases(df: pd.DataFrame, aliases: dict[str, str]) -> pd.DataFrame:
    rename_map = {}
    lowered = {c.lower(): c for c in df.columns}
    for raw, standard in aliases.items():
        if raw in df.columns:
            rename_map[raw] = standard
        elif raw.lower() in lowered:
            rename_map[lowered[raw.lower()]] = standard
    return df.rename(columns=rename_map)


def _parse_datetime(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        # RetailRocket timestamps are milliseconds since epoch.
        median = series.dropna().median() if not series.dropna().empty else 0
        unit = "ms" if median > 10_000_000_000 else "s"
        return pd.to_datetime(series, unit=unit, errors="coerce")
    return pd.to_datetime(series, errors="coerce")


def load_behaviors(path: str | Path) -> pd.DataFrame:
    if not path:
        return pd.DataFrame(columns=["customer_id", "product_id", "behavior_type", "behavior_time"])
    df = _read_table(path)
    df = _rename_aliases(df, BEHAVIOR_ALIASES)
    required = {"customer_id", "product_id", "behavior_type", "behavior_time"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Behavior data missing columns: {sorted(missing)}")

    df = df[list(required)].copy()
    df = df.dropna(subset=["customer_id", "product_id", "behavior_type", "behavior_time"])
    df["customer_id"] = df["customer_id"].map(_clean_id)
    df["product_id"] = df["product_id"].map(_clean_id)
    df["behavior_type"] = (
        df["behavior_type"].astype(str).str.strip().str.lower().map(BEHAVIOR_TYPE_ALIASES)
    )
    df["behavior_time"] = _parse_datetime(df["behavior_time"])
    df = df.dropna(subset=["customer_id", "product_id", "behavior_type", "behavior_time"])
    df = df.sort_values(["customer_id", "behavior_time"]).reset_index(drop=True)
    return df


def load_orders(path: str | Path | None) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    df = _read_table(path)
    df = _rename_aliases(df, ORDER_ALIASES)
    required = {"order_id", "customer_id", "product_id", "quantity", "price", "order_time"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Order data missing columns: {sorted(missing)}")

    df = df[list(required)].copy()
    df = df.dropna(subset=["order_id", "customer_id", "product_id", "order_time"])
    df["order_id"] = df["order_id"].map(_clean_id)
    df["customer_id"] = df["customer_id"].map(_clean_id)
    df["product_id"] = df["product_id"].map(_clean_id)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["order_time"] = _parse_datetime(df["order_time"])
    df = df.dropna(subset=["order_id", "customer_id", "product_id", "order_time"])
    df = df[(df["quantity"] > 0) & (df["price"] >= 0)].copy()
    df["amount"] = df["quantity"] * df["price"]
    return df.sort_values(["customer_id", "order_time"]).reset_index(drop=True)


def _clean_id(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def derive_orders_from_behaviors(behaviors: pd.DataFrame) -> pd.DataFrame:
    purchases = behaviors[behaviors["behavior_type"] == "purchase"].copy()
    if purchases.empty:
        return pd.DataFrame(
            columns=["order_id", "customer_id", "product_id", "quantity", "price", "order_time", "amount"]
        )
    purchases["order_id"] = (
        purchases["customer_id"]
        + "_"
        + purchases["behavior_time"].dt.strftime("%Y%m%d%H%M%S")
    )
    purchases["quantity"] = 1
    purchases["price"] = 1.0
    purchases["order_time"] = purchases["behavior_time"]
    purchases["amount"] = 1.0
    return purchases[
        ["order_id", "customer_id", "product_id", "quantity", "price", "order_time", "amount"]
    ].reset_index(drop=True)


def derive_behaviors_from_orders(orders: pd.DataFrame) -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame(columns=["customer_id", "product_id", "behavior_type", "behavior_time"])
    behaviors = orders[["customer_id", "product_id", "order_time"]].copy()
    behaviors = behaviors.rename(columns={"order_time": "behavior_time"})
    behaviors["behavior_type"] = "purchase"
    return behaviors[["customer_id", "product_id", "behavior_type", "behavior_time"]].reset_index(drop=True)


def save_csv(df: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def save_json(data: dict[str, Any], path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
