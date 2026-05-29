from __future__ import annotations

import pandas as pd


def temporal_leave_one_out(
    behaviors: pd.DataFrame,
    target_behavior: str = "purchase",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if behaviors.empty:
        return behaviors.copy(), pd.DataFrame(columns=["customer_id", "product_id"])

    if target_behavior == "any":
        target_events = behaviors.copy()
    else:
        target_events = behaviors[behaviors["behavior_type"] == target_behavior].copy()
    if target_events.empty:
        return behaviors.copy(), pd.DataFrame(columns=["customer_id", "product_id"])

    idx = target_events.sort_values("behavior_time").groupby("customer_id").tail(1).index
    test = behaviors.loc[idx, ["customer_id", "product_id"]].copy()
    train = behaviors.drop(index=idx).reset_index(drop=True)
    return train, test.reset_index(drop=True)


def evaluate_topk(
    recommendations: pd.DataFrame,
    test_targets: pd.DataFrame,
    all_products: set[str],
    k: int = 10,
) -> dict[str, float]:
    if recommendations.empty or test_targets.empty:
        return {
            f"hit_rate@{k}": 0.0,
            f"recall@{k}": 0.0,
            f"precision@{k}": 0.0,
            f"coverage@{k}": 0.0,
            "evaluated_users": 0,
        }

    targets = (
        test_targets.groupby("customer_id")["product_id"]
        .apply(lambda x: set(map(str, x)))
        .to_dict()
    )
    recs = (
        recommendations.sort_values(["customer_id", "score"], ascending=[True, False])
        .groupby("customer_id")["product_id"]
        .apply(lambda x: list(map(str, x.head(k))))
        .to_dict()
    )

    hits = 0
    recall_sum = 0.0
    precision_sum = 0.0
    recommended_items: set[str] = set()
    evaluated = 0
    for customer_id, truth in targets.items():
        if customer_id not in recs:
            continue
        top_items = recs[customer_id]
        if not top_items:
            continue
        evaluated += 1
        recommended_items.update(top_items)
        hit_items = set(top_items) & truth
        if hit_items:
            hits += 1
        recall_sum += len(hit_items) / max(len(truth), 1)
        precision_sum += len(hit_items) / max(len(top_items), 1)

    if evaluated == 0:
        return {
            f"hit_rate@{k}": 0.0,
            f"recall@{k}": 0.0,
            f"precision@{k}": 0.0,
            f"coverage@{k}": 0.0,
            "evaluated_users": 0,
        }

    coverage = len(recommended_items) / max(len(all_products), 1)
    return {
        f"hit_rate@{k}": round(hits / evaluated, 6),
        f"recall@{k}": round(recall_sum / evaluated, 6),
        f"precision@{k}": round(precision_sum / evaluated, 6),
        f"coverage@{k}": round(coverage, 6),
        "evaluated_users": evaluated,
    }
