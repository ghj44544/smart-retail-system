from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.user import User


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_DIR = PROJECT_ROOT / "algorithm" / "retail_algorithm" / "outputs_uci_online_retail_ii"

RFM_SEGMENT_MAP = {
    "high_value": "高价值用户",
    "key_development": "重点发展用户",
    "ordinary": "普通用户",
    "potential": "潜力用户",
    "sleeping": "流失用户",
}

CLUSTER_NAME_MAP = {
    "high_value": "高消费活跃用户",
    "growth_potential": "潜力成长用户",
    "ordinary": "普通消费用户",
    "sleeping_or_churn": "沉睡流失用户",
}


def _read_csv(name: str) -> list[dict[str, str]]:
    path = OUTPUT_DIR / name
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


@lru_cache(maxsize=16)
def _cached_csv(name: str) -> tuple[tuple[tuple[str, str], ...], ...]:
    return tuple(tuple(row.items()) for row in _read_csv(name))


def _rows(name: str) -> list[dict[str, str]]:
    return [dict(items) for items in _cached_csv(name)]


def _first(row: dict[str, str], names: Iterable[str]) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(value, 1.0))


def _find_product(db: Session, algorithm_product_id: object) -> Product | None:
    key = str(algorithm_product_id).strip()
    if not key:
        return None

    product = db.query(Product).filter(Product.product_no == key).first()
    if product:
        return product

    if key.isdigit():
        return db.query(Product).filter(Product.id == int(key)).first()
    return None


def _user_algorithm_keys(db: Session, user_id: int) -> set[str]:
    keys = {str(user_id)}
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        keys.add(str(user.id))
        if user.username:
            keys.add(str(user.username))
    return keys


def get_algorithm_hot_recommendations(db: Session, limit: int) -> list[dict]:
    rows = _rows("product_popularity.csv") or _rows("popular_recommendations.csv")
    result: list[dict] = []
    seen: set[int] = set()

    rows = sorted(
        rows,
        key=lambda r: _to_float(_first(r, ["score", "popularity", "weighted_score", "count"])),
        reverse=True,
    )
    for row in rows:
        algorithm_product_id = _first(row, ["product_id", "item_id", "product", "item"])
        product = _find_product(db, algorithm_product_id)
        if not product or product.id in seen:
            continue
        seen.add(product.id)
        result.append(
            {
                "product_id": product.id,
                "name": str(product.name),
                "price": float(product.price),
                "sales_count": product.sales_count or 0,
                "rating": float(product.rating or 0),
            }
        )
        if len(result) >= limit:
            break

    return result


def get_algorithm_association_recommendations(
    db: Session,
    product_id: int,
    limit: int,
) -> list[dict]:
    current = db.query(Product).filter(Product.id == product_id).first()
    if not current:
        return []

    keys = {str(current.id)}
    if current.product_no:
        keys.add(str(current.product_no))

    matched: list[dict] = []
    for row in _rows("association_rules.csv"):
        antecedent = _first(row, ["antecedent", "antecedents"])
        consequent = _first(row, ["consequent", "consequents"])
        if antecedent in keys:
            matched.append({**row, "target": consequent})
        elif consequent in keys:
            matched.append({**row, "target": antecedent})

    matched.sort(key=lambda r: _to_float(r.get("lift")), reverse=True)

    result: list[dict] = []
    seen: set[int] = set()
    for row in matched:
        product = _find_product(db, row["target"])
        if not product or product.id in seen or product.id == product_id:
            continue
        seen.add(product.id)
        result.append(
            {
                "product_id": product.id,
                "name": str(product.name),
                "price": float(product.price),
                "confidence": _to_float(row.get("confidence")),
                "lift": _to_float(row.get("lift"), 1.0),
            }
        )
        if len(result) >= limit:
            break

    if result:
        return result

    current_codes = {str(current.product_no or "").strip(), str(current.id)}
    scored_rows: list[dict[str, str]] = []
    for row in _rows("association_recommendations.csv"):
        reason = _first(row, ["reason"])
        if reason.startswith("association:") and reason.split(":", 1)[1].strip() in current_codes:
            scored_rows.append(row)

    scored_rows.sort(key=lambda r: _to_float(r.get("score")), reverse=True)
    for row in scored_rows:
        algorithm_product_id = _first(row, ["product_id", "item_id", "product", "item"])
        product = _find_product(db, algorithm_product_id)
        if not product or product.id in seen or product.id == product_id:
            continue
        score = _to_float(row.get("score"))
        seen.add(product.id)
        result.append(
            {
                "product_id": product.id,
                "name": str(product.name),
                "price": float(product.price),
                "confidence": round(_clamp01(score / (score + 1.0)), 4) if score > 0 else 0.0,
                "lift": round(max(score, 1.0), 2),
            }
        )
        if len(result) >= limit:
            break
    return result


def get_algorithm_personalized_recommendations(
    db: Session,
    user_id: int,
    limit: int,
) -> list[dict]:
    keys = _user_algorithm_keys(db, user_id)
    matched = [
        row for row in _rows("multibehavior_recommendations.csv")
        if _first(row, ["customer_id", "user_id"]) in keys
    ]
    matched.sort(key=lambda r: _to_float(r.get("score")), reverse=True)

    result: list[dict] = []
    seen: set[int] = set()
    for row in matched:
        algorithm_product_id = _first(row, ["product_id", "item_id", "product", "item"])
        product = _find_product(db, algorithm_product_id)
        if not product or product.id in seen:
            continue
        seen.add(product.id)
        result.append(
            {
                "product_id": product.id,
                "name": str(product.name),
                "price": float(product.price),
                "score": round(_clamp01(_to_float(row.get("score"))), 4),
                "reason": row.get("reason") or "算法个性化推荐",
            }
        )
        if len(result) >= limit:
            break
    return result


def get_algorithm_rfm_result(db: Session) -> dict | None:
    rows = _rows("rfm_segments.csv")
    if not rows:
        return None

    user_ids = {
        int(row["customer_id"])
        for row in rows
        if str(row.get("customer_id", "")).isdigit()
    }
    existing_users = {
        int(user_id)
        for (user_id,) in db.query(User.id).filter(User.id.in_(user_ids)).all()
    }

    labels = ["高价值用户", "重点发展用户", "普通用户", "潜力用户", "流失用户"]
    distribution = {label: 0 for label in labels}
    scores: list[dict] = []

    for row in rows:
        customer_id = _first(row, ["customer_id", "user_id"])
        if not customer_id.isdigit():
            continue
        user_id = int(customer_id)
        if existing_users and user_id not in existing_users:
            continue

        segment = RFM_SEGMENT_MAP.get(_first(row, ["segment_name", "segment"]), "普通用户")
        distribution[segment] = distribution.get(segment, 0) + 1
        scores.append(
            {
                "user_id": user_id,
                "recency": int(_to_float(_first(row, ["r_score", "recency"]), 1)),
                "frequency": int(_to_float(_first(row, ["f_score", "frequency"]), 1)),
                "monetary": int(_to_float(_first(row, ["m_score", "monetary"]), 1)),
                "segment": segment,
            }
        )

    if not scores:
        return None

    return {
        "distribution": {
            "labels": labels,
            "values": [distribution.get(label, 0) for label in labels],
        },
        "scores": scores,
    }


def get_algorithm_cluster_result(db: Session) -> dict | None:
    rows = _rows("cluster_segments.csv")
    if not rows:
        return None

    user_ids = {
        int(row["customer_id"])
        for row in rows
        if str(row.get("customer_id", "")).isdigit()
    }
    existing_users = {
        int(user_id)
        for (user_id,) in db.query(User.id).filter(User.id.in_(user_ids)).all()
    }

    groups: dict[int, dict] = {}
    for row in rows:
        customer_id = _first(row, ["customer_id", "user_id"])
        if not customer_id.isdigit():
            continue
        user_id = int(customer_id)
        if existing_users and user_id not in existing_users:
            continue

        label = int(_to_float(_first(row, ["cluster_id", "label"]), 0))
        name = CLUSTER_NAME_MAP.get(_first(row, ["cluster_name", "name"]), f"用户群{label}")
        point = {
            "user_id": user_id,
            "x": _to_float(_first(row, ["r_score", "recency_days"]), 0),
            "y": _to_float(_first(row, ["f_score", "frequency"]), 0),
            "z": _to_float(_first(row, ["m_score", "monetary"]), 0),
        }
        group = groups.setdefault(label, {"label": label, "name": name, "points": []})
        group["points"].append(point)

    clusters: list[dict] = []
    for label, group in sorted(groups.items()):
        points = group["points"]
        if not points:
            continue
        center = [
            round(sum(p["x"] for p in points) / len(points), 1),
            round(sum(p["y"] for p in points) / len(points), 1),
            round(sum(p["z"] for p in points) / len(points), 1),
        ]
        clusters.append(
            {
                "label": label,
                "name": group["name"],
                "count": len(points),
                "center": center,
                "points": points,
            }
        )

    return {"clusters": clusters} if clusters else None


def get_algorithm_user_rfm(user_id: int) -> dict | None:
    key = str(user_id)
    for row in _rows("rfm_segments.csv"):
        if _first(row, ["customer_id", "user_id"]) != key:
            continue
        return {
            "recency": int(_to_float(_first(row, ["r_score", "recency"]), 1)),
            "frequency": int(_to_float(_first(row, ["f_score", "frequency"]), 1)),
            "monetary": int(_to_float(_first(row, ["m_score", "monetary"]), 1)),
        }
    return None


def get_algorithm_user_cluster(user_id: int) -> int | None:
    key = str(user_id)
    for row in _rows("cluster_segments.csv"):
        if _first(row, ["customer_id", "user_id"]) != key:
            continue
        return int(_to_float(_first(row, ["cluster_id", "label"]), 0))
    return None


def clear_algorithm_output_cache() -> None:
    _cached_csv.cache_clear()
