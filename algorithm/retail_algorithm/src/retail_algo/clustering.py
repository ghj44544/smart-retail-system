from __future__ import annotations

import os

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "4")

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def build_behavior_features(behaviors: pd.DataFrame) -> pd.DataFrame:
    if behaviors.empty:
        return pd.DataFrame(columns=["customer_id"])

    counts = (
        behaviors.pivot_table(
            index="customer_id",
            columns="behavior_type",
            values="product_id",
            aggfunc="count",
            fill_value=0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for col in ["view", "favorite", "cart", "purchase"]:
        if col not in counts.columns:
            counts[col] = 0
    product_count = (
        behaviors.groupby("customer_id")["product_id"]
        .nunique()
        .reset_index(name="unique_product_count")
    )
    features = counts.merge(product_count, on="customer_id", how="left")
    features["conversion_rate"] = features["purchase"] / features["view"].replace(0, np.nan)
    features["conversion_rate"] = features["conversion_rate"].fillna(0)
    return features


def cluster_users(
    rfm: pd.DataFrame,
    behaviors: pd.DataFrame,
    n_clusters: int = 4,
    random_state: int = 42,
) -> pd.DataFrame:
    behavior_features = build_behavior_features(behaviors)
    if rfm.empty and behavior_features.empty:
        return pd.DataFrame()

    if rfm.empty:
        base = behavior_features.copy()
        for col in ["recency_days", "frequency", "monetary", "rfm_score"]:
            base[col] = 0
    else:
        base = rfm.merge(behavior_features, on="customer_id", how="outer")

    numeric_cols = [
        "recency_days",
        "frequency",
        "monetary",
        "rfm_score",
        "view",
        "favorite",
        "cart",
        "purchase",
        "unique_product_count",
        "conversion_rate",
    ]
    for col in numeric_cols:
        if col not in base.columns:
            base[col] = 0
    base[numeric_cols] = base[numeric_cols].fillna(0)

    usable_clusters = min(n_clusters, len(base))
    if usable_clusters <= 1:
        base["cluster_id"] = 0
        base["cluster_name"] = "single_group"
        return base

    scaled = StandardScaler().fit_transform(base[numeric_cols])
    model = KMeans(n_clusters=usable_clusters, random_state=random_state, n_init=10)
    base["cluster_id"] = model.fit_predict(scaled)

    centers = (
        base.groupby("cluster_id")
        .agg(
            monetary=("monetary", "mean"),
            rfm_score=("rfm_score", "mean"),
            recency_days=("recency_days", "mean"),
            purchase=("purchase", "mean"),
            conversion_rate=("conversion_rate", "mean"),
        )
        .reset_index()
    )
    centers["value_rank"] = (
        centers["monetary"].rank(ascending=False, method="dense")
        + centers["rfm_score"].rank(ascending=False, method="dense")
        + centers["recency_days"].rank(ascending=True, method="dense")
    )
    ordered = centers.sort_values("value_rank")["cluster_id"].tolist()
    names = ["high_value", "growth_potential", "ordinary", "sleeping_or_churn"]
    name_map = {cluster_id: names[min(i, len(names) - 1)] for i, cluster_id in enumerate(ordered)}
    base["cluster_name"] = base["cluster_id"].map(name_map)
    return base.sort_values(["cluster_name", "rfm_score"], ascending=[True, False]).reset_index(drop=True)
