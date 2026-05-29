from __future__ import annotations

from pathlib import Path
from typing import Any

from .association import apriori_rules, recommend_by_rules
from .clustering import cluster_users
from .data_io import (
    derive_orders_from_behaviors,
    derive_behaviors_from_orders,
    ensure_output_dir,
    load_behaviors,
    load_orders,
    save_csv,
    save_json,
)
from .evaluation import evaluate_topk, temporal_leave_one_out
from .multibehavior import MultiBehaviorConfig, train_multibehavior_recommender
from .popularity import product_popularity, recommend_popular
from .rfm import build_rfm


def _sample_order_lines_by_order(
    orders,
    max_lines: int,
    random_state: int,
):
    if orders.empty or len(orders) <= max_lines or "order_id" not in orders.columns:
        return orders
    order_sizes = (
        orders.groupby("order_id")
        .size()
        .sample(frac=1.0, random_state=random_state)
        .reset_index(name="line_count")
    )
    order_sizes["cum_lines"] = order_sizes["line_count"].cumsum()
    selected = order_sizes[order_sizes["cum_lines"] <= max_lines]["order_id"]
    if selected.empty:
        selected = order_sizes.head(1)["order_id"]
    return orders[orders["order_id"].isin(set(selected))].reset_index(drop=True)


def run_pipeline(config: dict[str, Any]) -> dict[str, Any]:
    out_dir = ensure_output_dir(config.get("output_dir", "retail_algorithm/outputs"))
    behaviors = load_behaviors(config.get("behaviors_path", ""))
    orders = load_orders(config.get("orders_path"))

    sampling = config.get("sampling", {})
    random_state = int(sampling.get("random_state", 42))
    min_events_per_user = sampling.get("min_events_per_user")
    max_users = sampling.get("max_users")
    if not behaviors.empty and (min_events_per_user or max_users):
        user_counts = behaviors["customer_id"].value_counts()
        if min_events_per_user:
            user_counts = user_counts[user_counts >= int(min_events_per_user)]
        if max_users:
            user_counts = user_counts.head(int(max_users))
        selected_users = set(user_counts.index.astype(str))
        behaviors = behaviors[behaviors["customer_id"].astype(str).isin(selected_users)].reset_index(drop=True)
        if not orders.empty:
            orders = orders[orders["customer_id"].astype(str).isin(selected_users)].reset_index(drop=True)

    if orders.empty:
        orders = derive_orders_from_behaviors(behaviors)
    if behaviors.empty:
        behaviors = derive_behaviors_from_orders(orders)

    max_orders = sampling.get("max_orders")
    max_order_lines = sampling.get("max_order_lines")
    max_events = sampling.get("max_events")
    if max_order_lines and len(orders) > int(max_order_lines):
        orders = _sample_order_lines_by_order(orders, int(max_order_lines), random_state)
        if config.get("behaviors_path"):
            valid_customers = set(orders["customer_id"].astype(str))
            behaviors = behaviors[behaviors["customer_id"].astype(str).isin(valid_customers)].reset_index(drop=True)
        else:
            behaviors = derive_behaviors_from_orders(orders)
    if max_orders and len(orders) > int(max_orders):
        orders = _sample_order_lines_by_order(orders, int(max_orders), random_state)
        if config.get("behaviors_path"):
            valid_customers = set(orders["customer_id"].astype(str))
            behaviors = behaviors[behaviors["customer_id"].astype(str).isin(valid_customers)].reset_index(drop=True)
        else:
            behaviors = derive_behaviors_from_orders(orders)
    if max_events and len(behaviors) > int(max_events):
        behaviors = behaviors.sample(n=int(max_events), random_state=random_state).reset_index(drop=True)
        if not config.get("orders_path"):
            orders = derive_orders_from_behaviors(behaviors)

    reference_date = config.get("reference_date")
    top_n = int(config.get("top_n", 10))
    behavior_weights = config.get(
        "behavior_weights",
        {"view": 1.0, "favorite": 2.0, "cart": 3.0, "purchase": 5.0},
    )

    rfm = build_rfm(
        orders,
        reference_date=reference_date,
        quantiles=int(config.get("rfm", {}).get("quantiles", 5)),
    )
    save_csv(rfm, out_dir / "rfm_segments.csv")

    kmeans_cfg = config.get("kmeans", {})
    clusters = cluster_users(
        rfm,
        behaviors,
        n_clusters=int(kmeans_cfg.get("n_clusters", 4)),
        random_state=int(kmeans_cfg.get("random_state", 42)),
    )
    save_csv(clusters, out_dir / "cluster_segments.csv")

    apriori_cfg = config.get("apriori", {})
    rules = apriori_rules(
        orders,
        min_support=float(apriori_cfg.get("min_support", 0.02)),
        min_confidence=float(apriori_cfg.get("min_confidence", 0.2)),
        max_len=int(apriori_cfg.get("max_len", 3)),
        max_rules=apriori_cfg.get("max_rules"),
    )
    save_csv(rules, out_dir / "association_rules.csv")

    assoc_recs = recommend_by_rules(behaviors, rules, top_n=top_n)
    save_csv(assoc_recs, out_dir / "association_recommendations.csv")

    mb_cfg = config.get("multibehavior", {})
    popularity = product_popularity(
        behaviors,
        behavior_weights=behavior_weights,
        reference_date=reference_date,
        time_decay_days=int(mb_cfg.get("time_decay_days", 30)),
    )
    save_csv(popularity, out_dir / "product_popularity.csv")
    popular_recs = recommend_popular(behaviors, popularity, top_n=top_n)
    save_csv(popular_recs, out_dir / "popular_recommendations.csv")

    multi_recs, multi_metrics = train_multibehavior_recommender(
        behaviors,
        behavior_weights=behavior_weights,
        reference_date=reference_date,
        config=MultiBehaviorConfig(
            embedding_dim=int(mb_cfg.get("embedding_dim", 32)),
            epochs=int(mb_cfg.get("epochs", 50)),
            learning_rate=float(mb_cfg.get("learning_rate", 0.03)),
            weight_decay=float(mb_cfg.get("weight_decay", 1e-4)),
            negative_samples=int(mb_cfg.get("negative_samples", 3)),
            batch_size=int(mb_cfg.get("batch_size", 1024)),
            sequence_alpha=float(mb_cfg.get("sequence_alpha", 0.35)),
            time_decay_days=int(mb_cfg.get("time_decay_days", 30)),
            seed=int(mb_cfg.get("seed", 42)),
        ),
        top_n=top_n,
    )
    save_csv(multi_recs, out_dir / "multibehavior_recommendations.csv")

    evaluation = {}
    eval_cfg = config.get("evaluation", {})
    if eval_cfg.get("enabled", True):
        eval_k_values = eval_cfg.get("k_values", [top_n])
        eval_filter_seen = bool(eval_cfg.get("filter_seen", False))
        target_behavior = str(eval_cfg.get("target_behavior", "purchase"))
        train_behaviors, test_targets = temporal_leave_one_out(
            behaviors, target_behavior=target_behavior
        )
        eval_popularity = product_popularity(
            train_behaviors,
            behavior_weights=behavior_weights,
            reference_date=reference_date,
            time_decay_days=int(mb_cfg.get("time_decay_days", 30)),
        )
        eval_top_n = max(int(k) for k in eval_k_values)
        eval_popular_recs = recommend_popular(
            train_behaviors,
            eval_popularity,
            top_n=eval_top_n,
            filter_seen=eval_filter_seen,
        )
        eval_multi_recs, _ = train_multibehavior_recommender(
            train_behaviors,
            behavior_weights=behavior_weights,
            reference_date=reference_date,
            config=MultiBehaviorConfig(
                embedding_dim=int(mb_cfg.get("embedding_dim", 32)),
                epochs=max(5, int(mb_cfg.get("epochs", 50)) // 2),
                learning_rate=float(mb_cfg.get("learning_rate", 0.03)),
                weight_decay=float(mb_cfg.get("weight_decay", 1e-4)),
                negative_samples=int(mb_cfg.get("negative_samples", 3)),
                batch_size=int(mb_cfg.get("batch_size", 1024)),
                sequence_alpha=float(mb_cfg.get("sequence_alpha", 0.35)),
                time_decay_days=int(mb_cfg.get("time_decay_days", 30)),
                seed=int(mb_cfg.get("seed", 42)),
            ),
            top_n=eval_top_n,
            filter_seen=eval_filter_seen,
        )
        all_products = set(behaviors["product_id"].astype(str).unique())
        evaluation = {
            "target_behavior": target_behavior,
            "filter_seen": eval_filter_seen,
            "popular": {
                f"k={int(k)}": evaluate_topk(eval_popular_recs, test_targets, all_products, k=int(k))
                for k in eval_k_values
            },
            "multibehavior": {
                f"k={int(k)}": evaluate_topk(eval_multi_recs, test_targets, all_products, k=int(k))
                for k in eval_k_values
            },
        }
        save_json(evaluation, out_dir / "evaluation_metrics.json")

    summary = {
        "behaviors": int(len(behaviors)),
        "orders": int(len(orders)),
        "customers": int(behaviors["customer_id"].nunique()),
        "products": int(behaviors["product_id"].nunique()),
        "rfm_rows": int(len(rfm)),
        "cluster_rows": int(len(clusters)),
        "association_rules": int(len(rules)),
        "popular_recommendations": int(len(popular_recs)),
        "association_recommendations": int(len(assoc_recs)),
        "multibehavior_recommendations": int(len(multi_recs)),
        "multibehavior_metrics": multi_metrics,
        "evaluation": evaluation,
        "output_dir": str(Path(out_dir).resolve()),
    }
    save_json(summary, out_dir / "metrics_summary.json")
    return summary
