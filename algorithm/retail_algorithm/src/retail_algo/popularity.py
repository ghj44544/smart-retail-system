from __future__ import annotations

import numpy as np
import pandas as pd


def product_popularity(
    behaviors: pd.DataFrame,
    behavior_weights: dict[str, float],
    reference_date: str | pd.Timestamp | None = None,
    time_decay_days: int = 30,
) -> pd.DataFrame:
    if behaviors.empty:
        return pd.DataFrame(columns=["product_id", "popular_score", "behavior_count"])

    df = behaviors.copy()
    df["behavior_time"] = pd.to_datetime(df["behavior_time"], errors="coerce")
    ref = pd.Timestamp(reference_date) if reference_date else df["behavior_time"].max()
    df["base_weight"] = df["behavior_type"].map(behavior_weights).fillna(1.0)
    age_days = (ref - df["behavior_time"]).dt.total_seconds() / 86400
    df["time_weight"] = np.exp(-age_days.clip(lower=0) / max(time_decay_days, 1))
    df["score"] = df["base_weight"] * df["time_weight"]
    result = (
        df.groupby("product_id")
        .agg(popular_score=("score", "sum"), behavior_count=("behavior_type", "count"))
        .reset_index()
        .sort_values("popular_score", ascending=False)
        .reset_index(drop=True)
    )
    result["popular_score"] = result["popular_score"].round(6)
    return result


def recommend_popular(
    behaviors: pd.DataFrame,
    popularity: pd.DataFrame,
    top_n: int = 10,
    filter_seen: bool = True,
) -> pd.DataFrame:
    if behaviors.empty or popularity.empty:
        return pd.DataFrame(columns=["customer_id", "product_id", "score", "reason"])

    interacted = (
        behaviors.groupby("customer_id")["product_id"]
        .apply(lambda x: set(map(str, x)))
        .to_dict()
    )
    rows = []
    ranked = popularity[["product_id", "popular_score"]].itertuples(index=False)
    ranked_items = [(str(row.product_id), float(row.popular_score)) for row in ranked]
    for customer_id, seen in interacted.items():
        count = 0
        for product_id, score in ranked_items:
            if filter_seen and product_id in seen:
                continue
            rows.append(
                {
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "score": round(score, 6),
                    "reason": "popular_item",
                }
            )
            count += 1
            if count >= top_n:
                break
    return pd.DataFrame(rows)
