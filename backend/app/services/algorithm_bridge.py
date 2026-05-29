import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.behavior import Behavior
from app.models.cluster_result import ClusterResult
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.rfm_score import RfmScore
from app.models.user import User


ROOT = Path(__file__).resolve().parents[3]
ALGORITHM_ROOT = ROOT / "algorithm"
if str(ALGORITHM_ROOT) not in sys.path:
    sys.path.insert(0, str(ALGORITHM_ROOT))

from retail_algorithm.src.retail_algo.association import apriori_rules
from retail_algorithm.src.retail_algo.clustering import cluster_users
from retail_algorithm.src.retail_algo.popularity import product_popularity
from retail_algorithm.src.retail_algo.rfm import build_rfm


SEGMENT_MAP = {
    "high_value": "高价值用户",
    "key_development": "忠诚用户",
    "ordinary": "忠诚用户",
    "potential": "潜力用户",
    "sleeping": "流失用户",
    "churn_risk": "流失用户",
}


def _to_int(value):
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def export_orders(db: Session) -> pd.DataFrame:
    rows = []
    records = (
        db.query(Order, OrderItem)
        .join(OrderItem, Order.id == OrderItem.order_id)
        .filter(Order.status.in_(["completed", "paid", "shipped"]))
        .all()
    )
    for order, item in records:
        rows.append(
            {
                "order_id": str(order.id),
                "customer_id": str(order.user_id),
                "product_id": str(item.product_id),
                "quantity": int(item.quantity or 1),
                "price": float(item.price or 0),
                "order_time": order.created_at,
                "amount": float(item.price or 0) * int(item.quantity or 1),
            }
        )
    return pd.DataFrame(rows)


def export_behaviors(db: Session) -> pd.DataFrame:
    rows = []
    type_map = {"buy": "purchase", "view": "view", "cart": "cart", "favorite": "favorite"}
    for behavior in db.query(Behavior).all():
        rows.append(
            {
                "customer_id": str(behavior.user_id),
                "product_id": str(behavior.product_id),
                "behavior_type": type_map.get(str(behavior.behavior_type), str(behavior.behavior_type)),
                "behavior_time": behavior.created_at,
            }
        )
    return pd.DataFrame(rows)


def calculate_rfm(db: Session) -> dict | None:
    orders = export_orders(db)
    if orders.empty:
        return None

    result = build_rfm(orders, quantiles=5)
    db.query(RfmScore).delete()
    distribution = defaultdict(int)
    scores = []

    for row in result.itertuples(index=False):
        user_id = _to_int(row.customer_id)
        if user_id is None:
            continue
        segment = SEGMENT_MAP.get(str(row.segment_name), "忠诚用户")
        recency = int(row.r_score)
        frequency = int(row.f_score)
        monetary = int(row.m_score)
        distribution[segment] += 1
        db.add(RfmScore(user_id=user_id, recency=recency, frequency=frequency, monetary=monetary, segment=segment))
        scores.append({"user_id": user_id, "recency": recency, "frequency": frequency, "monetary": monetary, "segment": segment})

    scored_users = {item["user_id"] for item in scores}
    for user in db.query(User).filter(User.deleted_at == None).all():
        if user.id in scored_users:
            continue
        segment = "流失用户"
        distribution[segment] += 1
        db.add(RfmScore(user_id=user.id, recency=1, frequency=1, monetary=1, segment=segment))
        scores.append({"user_id": user.id, "recency": 1, "frequency": 1, "monetary": 1, "segment": segment})

    db.commit()
    labels = ["高价值用户", "忠诚用户", "潜力用户", "流失用户"]
    return {"distribution": {"labels": labels, "values": [distribution.get(label, 0) for label in labels]}, "scores": scores}


def calculate_cluster(db: Session, n_clusters: int = 5) -> dict | None:
    orders = export_orders(db)
    behaviors = export_behaviors(db)
    if orders.empty and behaviors.empty:
        return None

    rfm = build_rfm(orders, quantiles=5) if not orders.empty else pd.DataFrame()
    clusters = cluster_users(rfm, behaviors, n_clusters=n_clusters, random_state=42)
    if clusters.empty:
        return None

    db.query(ClusterResult).delete()
    groups = defaultdict(list)
    for row in clusters.itertuples(index=False):
        user_id = _to_int(row.customer_id)
        if user_id is None:
            continue
        label = int(row.cluster_id)
        db.add(ClusterResult(user_id=user_id, cluster_label=label))
        point = {
            "user_id": user_id,
            "x": float(getattr(row, "r_score", 0) or 0),
            "y": float(getattr(row, "f_score", 0) or 0),
            "z": float(getattr(row, "m_score", 0) or 0),
        }
        groups[label].append(point)

    clustered_users = {point["user_id"] for points in groups.values() for point in points}
    fallback_label = max(groups.keys(), default=0)
    for user in db.query(User).filter(User.deleted_at == None).all():
        if user.id in clustered_users:
            continue
        db.add(ClusterResult(user_id=user.id, cluster_label=fallback_label))
        groups[fallback_label].append({"user_id": user.id, "x": 1.0, "y": 1.0, "z": 1.0})

    db.commit()
    names = ["高价值活跃用户", "增长潜力用户", "普通稳定用户", "沉睡流失用户", "低频观望用户"]
    payload = []
    for label, points in sorted(groups.items()):
        center = [
            round(sum(p["x"] for p in points) / len(points), 1),
            round(sum(p["y"] for p in points) / len(points), 1),
            round(sum(p["z"] for p in points) / len(points), 1),
        ]
        payload.append({"label": label, "name": names[label] if label < len(names) else f"用户群{label}", "count": len(points), "center": center, "points": points})
    return {"clusters": payload}


def calculate_association(db: Session, min_support: float = 0.01, min_confidence: float = 0.5, limit: int = 20) -> list[dict] | None:
    orders = export_orders(db)
    if orders.empty:
        return None

    rules = apriori_rules(orders, min_support=min_support, min_confidence=min_confidence, max_len=3, max_rules=limit)
    if rules.empty:
        return []

    product_names = {str(p.id): str(p.name) for p in db.query(Product).all()}
    result = []
    for row in rules.itertuples(index=False):
        antecedents = [item for item in str(row.antecedent).split(";") if item]
        consequents = [item for item in str(row.consequent).split(";") if item]
        result.append(
            {
                "antecedents": antecedents,
                "consequents": consequents,
                "antecedent_names": [product_names.get(item, "") for item in antecedents],
                "consequent_names": [product_names.get(item, "") for item in consequents],
                "support": round(float(row.support), 4),
                "confidence": round(float(row.confidence), 4),
                "lift": round(float(row.lift), 2),
            }
        )
    return result


def recommend_for_user(db: Session, user_id: int, limit: int = 10) -> list[dict]:
    behaviors = export_behaviors(db)
    if behaviors.empty:
        return []

    weights = {"view": 1.0, "favorite": 2.0, "cart": 3.0, "purchase": 5.0}
    popularity = product_popularity(behaviors, weights, time_decay_days=30)
    seen = set(
        behaviors.loc[behaviors["customer_id"] == str(user_id), "product_id"].astype(str).tolist()
    )
    product_map = {str(p.id): p for p in db.query(Product).filter(Product.deleted_at == None, Product.status == "on").all()}

    rows = []
    for row in popularity.itertuples(index=False):
        product_id = str(row.product_id)
        if product_id in seen or product_id not in product_map:
            continue
        product = product_map[product_id]
        rows.append(
            {
                "product_id": int(product_id),
                "name": str(product.name),
                "price": float(product.price),
                "score": round(float(row.popular_score), 2),
                "reason": "基于多行为权重与近期热度推荐",
            }
        )
        if len(rows) >= limit:
            break
    return rows
