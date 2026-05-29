from __future__ import annotations

import pandas as pd
import numpy as np


def _score_by_quantile(series: pd.Series, higher_is_better: bool, q: int) -> pd.Series:
    if series.nunique(dropna=True) <= 1:
        return pd.Series([max(q // 2, 1)] * len(series), index=series.index)
    percentile = series.rank(method="average", pct=True)
    scored = (percentile * q).apply(np.ceil).astype(int).clip(lower=1, upper=q)
    if not higher_is_better:
        scored = q + 1 - scored
    return scored


def build_rfm(
    orders: pd.DataFrame,
    reference_date: str | pd.Timestamp | None = None,
    quantiles: int = 5,
) -> pd.DataFrame:
    if orders.empty:
        return pd.DataFrame(
            columns=[
                "customer_id",
                "recency_days",
                "frequency",
                "monetary",
                "r_score",
                "f_score",
                "m_score",
                "rfm_score",
                "segment_name",
            ]
        )

    df = orders.copy()
    df["order_time"] = pd.to_datetime(df["order_time"], errors="coerce")
    if "amount" not in df.columns:
        df["amount"] = pd.to_numeric(df["quantity"], errors="coerce") * pd.to_numeric(
            df["price"], errors="coerce"
        )
    ref = pd.Timestamp(reference_date) if reference_date else df["order_time"].max() + pd.Timedelta(days=1)

    grouped = (
        df.groupby("customer_id")
        .agg(
            last_order_time=("order_time", "max"),
            frequency=("order_id", "nunique"),
            monetary=("amount", "sum"),
        )
        .reset_index()
    )
    grouped["recency_days"] = (ref - grouped["last_order_time"]).dt.days.clip(lower=0)
    grouped["r_score"] = _score_by_quantile(grouped["recency_days"], False, quantiles)
    grouped["f_score"] = _score_by_quantile(grouped["frequency"], True, quantiles)
    grouped["m_score"] = _score_by_quantile(grouped["monetary"], True, quantiles)
    grouped["rfm_score"] = grouped[["r_score", "f_score", "m_score"]].sum(axis=1)

    def segment(row: pd.Series) -> str:
        if row["r_score"] >= 4 and row["f_score"] >= 4 and row["m_score"] >= 4:
            return "high_value"
        if row["r_score"] >= 4 and row["m_score"] >= 4:
            return "key_development"
        if row["r_score"] >= 4 and row["f_score"] <= 3:
            return "potential"
        if row["r_score"] <= 2 and row["f_score"] >= 3:
            return "sleeping"
        if row["r_score"] <= 2:
            return "churn_risk"
        return "ordinary"

    grouped["segment_name"] = grouped.apply(segment, axis=1)
    cols = [
        "customer_id",
        "last_order_time",
        "recency_days",
        "frequency",
        "monetary",
        "r_score",
        "f_score",
        "m_score",
        "rfm_score",
        "segment_name",
    ]
    return grouped[cols].sort_values(["rfm_score", "monetary"], ascending=False).reset_index(drop=True)
