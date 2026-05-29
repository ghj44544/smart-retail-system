from __future__ import annotations

import os
import random
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import torch
from torch import nn

warnings.filterwarnings("ignore", message="CUDA initialization.*", category=UserWarning)


@dataclass
class MultiBehaviorConfig:
    embedding_dim: int = 32
    epochs: int = 50
    learning_rate: float = 0.03
    weight_decay: float = 1e-4
    negative_samples: int = 3
    batch_size: int = 1024
    sequence_alpha: float = 0.35
    time_decay_days: int = 30
    seed: int = 42


class ImplicitMF(nn.Module):
    def __init__(self, num_users: int, num_items: int, dim: int) -> None:
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, dim)
        self.item_embedding = nn.Embedding(num_items, dim)
        self.user_bias = nn.Embedding(num_users, 1)
        self.item_bias = nn.Embedding(num_items, 1)
        nn.init.normal_(self.user_embedding.weight, std=0.05)
        nn.init.normal_(self.item_embedding.weight, std=0.05)
        nn.init.zeros_(self.user_bias.weight)
        nn.init.zeros_(self.item_bias.weight)

    def score(self, users: torch.Tensor, items: torch.Tensor) -> torch.Tensor:
        u = self.user_embedding(users)
        i = self.item_embedding(items)
        return (u * i).sum(dim=1) + self.user_bias(users).squeeze(1) + self.item_bias(items).squeeze(1)

    def score_all_items(self, user: int) -> torch.Tensor:
        user_tensor = torch.tensor([user], dtype=torch.long)
        u = self.user_embedding(user_tensor)
        scores = torch.matmul(self.item_embedding.weight, u.squeeze(0))
        scores = scores + self.user_bias(user_tensor).squeeze(0) + self.item_bias.weight.squeeze(1)
        return scores


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _weighted_interactions(
    behaviors: pd.DataFrame,
    behavior_weights: dict[str, float],
    reference_date: str | pd.Timestamp | None,
    time_decay_days: int,
) -> pd.DataFrame:
    df = behaviors.copy()
    df["behavior_time"] = pd.to_datetime(df["behavior_time"], errors="coerce")
    ref = pd.Timestamp(reference_date) if reference_date else df["behavior_time"].max()
    age_days = (ref - df["behavior_time"]).dt.total_seconds() / 86400
    df["weight"] = df["behavior_type"].map(behavior_weights).fillna(1.0)
    df["weight"] *= np.exp(-age_days.clip(lower=0) / max(time_decay_days, 1))
    return (
        df.groupby(["customer_id", "product_id"])
        .agg(weight=("weight", "sum"), last_time=("behavior_time", "max"))
        .reset_index()
    )


def _build_sequence_scores(behaviors: pd.DataFrame) -> dict[tuple[str, str], float]:
    if behaviors.empty:
        return {}
    df = behaviors.sort_values(["customer_id", "behavior_time"])
    transitions: dict[tuple[str, str], float] = {}
    for _, group in df.groupby("customer_id"):
        items = group["product_id"].astype(str).tolist()
        for left, right in zip(items[:-1], items[1:]):
            if left == right:
                continue
            transitions[(left, right)] = transitions.get((left, right), 0.0) + 1.0
    if not transitions:
        return {}
    max_score = max(transitions.values())
    return {key: value / max_score for key, value in transitions.items()}


def train_multibehavior_recommender(
    behaviors: pd.DataFrame,
    behavior_weights: dict[str, float],
    reference_date: str | pd.Timestamp | None = None,
    config: MultiBehaviorConfig | None = None,
    top_n: int = 10,
    filter_seen: bool = True,
) -> tuple[pd.DataFrame, dict[str, float]]:
    cfg = config or MultiBehaviorConfig()
    _set_seed(cfg.seed)

    if behaviors.empty:
        return pd.DataFrame(columns=["customer_id", "product_id", "score", "reason"]), {}

    interactions = _weighted_interactions(
        behaviors, behavior_weights, reference_date, cfg.time_decay_days
    )
    users = sorted(interactions["customer_id"].astype(str).unique())
    items = sorted(interactions["product_id"].astype(str).unique())
    user_to_idx = {u: i for i, u in enumerate(users)}
    item_to_idx = {it: i for i, it in enumerate(items)}
    idx_to_item = {i: it for it, i in item_to_idx.items()}

    interactions["u"] = interactions["customer_id"].map(user_to_idx)
    interactions["i"] = interactions["product_id"].map(item_to_idx)
    positives = list(interactions[["u", "i", "weight"]].itertuples(index=False, name=None))
    user_pos: dict[int, set[int]] = {}
    for u, i, _ in positives:
        user_pos.setdefault(int(u), set()).add(int(i))

    if len(items) < 2 or not positives:
        return pd.DataFrame(columns=["customer_id", "product_id", "score", "reason"]), {
            "loss": 0.0,
            "num_users": len(users),
            "num_items": len(items),
            "num_interactions": len(positives),
        }

    model = ImplicitMF(len(users), len(items), cfg.embedding_dim)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay
    )
    all_items = list(range(len(items)))
    neg_candidates_by_user = {
        u: [i for i in all_items if i not in pos_items] for u, pos_items in user_pos.items()
    }
    last_loss = 0.0

    positives_array = np.array(positives, dtype=float)
    for _epoch in range(cfg.epochs):
        np.random.shuffle(positives_array)
        epoch_losses = []
        for start in range(0, len(positives_array), max(cfg.batch_size, 1)):
            batch = positives_array[start : start + max(cfg.batch_size, 1)]
            if batch.size == 0:
                continue
            users_batch = batch[:, 0].astype(int)
            pos_batch = batch[:, 1].astype(int)
            weight_batch = batch[:, 2].astype(float)
            expanded_users = []
            expanded_pos = []
            expanded_neg = []
            expanded_weights = []
            for u, pos_i, weight in zip(users_batch, pos_batch, weight_batch):
                neg_candidates = neg_candidates_by_user.get(int(u), [])
                if not neg_candidates:
                    continue
                for _ in range(max(cfg.negative_samples, 1)):
                    expanded_users.append(int(u))
                    expanded_pos.append(int(pos_i))
                    expanded_neg.append(random.choice(neg_candidates))
                    expanded_weights.append(float(weight))
            if not expanded_users:
                continue
            u_tensor = torch.tensor(expanded_users, dtype=torch.long)
            pos_tensor = torch.tensor(expanded_pos, dtype=torch.long)
            neg_tensor = torch.tensor(expanded_neg, dtype=torch.long)
            weight_tensor = torch.tensor(expanded_weights, dtype=torch.float32)
            pos_score = model.score(u_tensor, pos_tensor)
            neg_score = model.score(u_tensor, neg_tensor)
            loss = -torch.log(torch.sigmoid(pos_score - neg_score) + 1e-8)
            loss = (loss * weight_tensor).mean()
            optimizer.zero_grad()
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="CUDA initialization.*", category=UserWarning)
                warnings.filterwarnings("ignore", category=UserWarning, module="torch.autograd.graph")
                loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.detach()))
        last_loss = float(np.mean(epoch_losses)) if epoch_losses else 0.0

    sequence_scores = _build_sequence_scores(behaviors)
    recent_items = (
        behaviors.sort_values("behavior_time")
        .groupby("customer_id")["product_id"]
        .apply(lambda x: list(map(str, x.tail(5))))
        .to_dict()
    )

    rows = []
    model.eval()
    with torch.no_grad():
        for customer_id in users:
            u = user_to_idx[customer_id]
            scores = model.score_all_items(u).cpu().numpy()
            seen = user_pos.get(u, set())
            seq_boost = np.zeros(len(items), dtype=float)
            for recent_item in recent_items.get(customer_id, []):
                for item_idx, item_id in idx_to_item.items():
                    seq_boost[item_idx] += sequence_scores.get((recent_item, item_id), 0.0)
            if seq_boost.max() > 0:
                seq_boost = seq_boost / seq_boost.max()
            final_scores = scores + cfg.sequence_alpha * seq_boost
            if filter_seen:
                for item_idx in seen:
                    final_scores[item_idx] = -np.inf
            ranked = np.argsort(final_scores)[::-1][:top_n]
            for item_idx in ranked:
                if not np.isfinite(final_scores[item_idx]):
                    continue
                rows.append(
                    {
                        "customer_id": customer_id,
                        "product_id": idx_to_item[int(item_idx)],
                        "score": round(float(final_scores[item_idx]), 6),
                        "reason": "multi_behavior_sequence",
                    }
                )

    metrics = {
        "loss": round(last_loss, 6),
        "num_users": len(users),
        "num_items": len(items),
        "num_interactions": len(positives),
        "embedding_dim": cfg.embedding_dim,
        "epochs": cfg.epochs,
        "batch_size": cfg.batch_size,
    }
    return pd.DataFrame(rows), metrics
