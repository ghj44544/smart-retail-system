from __future__ import annotations

from collections import Counter
from itertools import combinations

import pandas as pd


def build_baskets(orders: pd.DataFrame) -> list[set[str]]:
    if orders.empty:
        return []
    baskets = (
        orders.groupby("order_id")["product_id"]
        .apply(lambda x: set(map(str, x.dropna())))
        .tolist()
    )
    return [basket for basket in baskets if len(basket) >= 2]


def apriori_rules(
    orders: pd.DataFrame,
    min_support: float = 0.02,
    min_confidence: float = 0.2,
    max_len: int = 3,
    max_rules: int | None = None,
) -> pd.DataFrame:
    baskets = build_baskets(orders)
    if not baskets:
        return pd.DataFrame(
            columns=["antecedent", "consequent", "support", "confidence", "lift", "support_count"]
        )

    basket_count = len(baskets)
    support_counts: Counter[tuple[str, ...]] = Counter()
    for basket in baskets:
        ordered = sorted(basket)
        for size in range(1, min(max_len, len(ordered)) + 1):
            for itemset in combinations(ordered, size):
                support_counts[itemset] += 1

    frequent = {
        itemset: count
        for itemset, count in support_counts.items()
        if count / basket_count >= min_support
    }
    rows = []
    for itemset, count in frequent.items():
        if len(itemset) < 2:
            continue
        itemset_set = set(itemset)
        for left_size in range(1, len(itemset)):
            for antecedent in combinations(itemset, left_size):
                antecedent = tuple(sorted(antecedent))
                consequent = tuple(sorted(itemset_set - set(antecedent)))
                antecedent_count = frequent.get(antecedent, support_counts.get(antecedent, 0))
                consequent_count = frequent.get(consequent, support_counts.get(consequent, 0))
                if antecedent_count == 0 or consequent_count == 0:
                    continue
                support = count / basket_count
                confidence = count / antecedent_count
                lift = confidence / (consequent_count / basket_count)
                if confidence >= min_confidence:
                    rows.append(
                        {
                            "antecedent": ";".join(antecedent),
                            "consequent": ";".join(consequent),
                            "support": round(support, 6),
                            "confidence": round(confidence, 6),
                            "lift": round(lift, 6),
                            "support_count": count,
                        }
                    )

    if not rows:
        return pd.DataFrame(
            columns=["antecedent", "consequent", "support", "confidence", "lift", "support_count"]
        )
    result = pd.DataFrame(rows).sort_values(
        ["lift", "confidence", "support"], ascending=False
    )
    if max_rules:
        result = result.head(int(max_rules))
    return result.reset_index(drop=True)


def recommend_by_rules(
    behaviors: pd.DataFrame,
    rules: pd.DataFrame,
    top_n: int = 10,
) -> pd.DataFrame:
    if behaviors.empty or rules.empty:
        return pd.DataFrame(columns=["customer_id", "product_id", "score", "reason"])

    interacted = (
        behaviors.groupby("customer_id")["product_id"]
        .apply(lambda x: set(map(str, x)))
        .to_dict()
    )
    rule_rows = []
    for row in rules.itertuples(index=False):
        antecedent = set(str(row.antecedent).split(";"))
        consequent = set(str(row.consequent).split(";"))
        rule_rows.append((antecedent, consequent, float(row.confidence) * float(row.lift)))

    recs = []
    for customer_id, items in interacted.items():
        scores: dict[str, float] = {}
        reasons: dict[str, str] = {}
        for antecedent, consequent, rule_score in rule_rows:
            if antecedent.issubset(items):
                for item in consequent:
                    if item in items:
                        continue
                    scores[item] = scores.get(item, 0.0) + rule_score
                    reasons[item] = f"association:{','.join(sorted(antecedent))}"
        for item, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]:
            recs.append(
                {
                    "customer_id": customer_id,
                    "product_id": item,
                    "score": round(score, 6),
                    "reason": reasons.get(item, "association_rule"),
                }
            )
    return pd.DataFrame(recs)
