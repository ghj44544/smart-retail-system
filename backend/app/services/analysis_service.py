# =============================================================================
# 智能零售用户行为分析系统 - 数据分析业务逻辑层
# =============================================================================
# 包含RFM分析、K-Means聚类、Apriori关联规则的核心算法
# =============================================================================

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.models.product import Product
from app.models.rfm_score import RfmScore
from app.models.cluster_result import ClusterResult


# ======================== RFM 分析 ========================

def calculate_rfm(db: Session) -> dict:
    """
    计算所有用户的RFM分值并存储到数据库
    
    R (Recency): 最近购买天数，越近分越高（1-5分）
    F (Frequency): 购买频率（订单数），越多分越高（1-5分）
    M (Monetary): 消费总金额，越高分越高（1-5分）
    
    分群规则：
      543-555: 高价值用户
      3xx,4xx: 忠诚用户
      2xx: 潜力用户
      1xx: 新用户/流失用户
    """
    try:
        from app.services import algorithm_bridge
        result = algorithm_bridge.calculate_rfm(db)
        if result is not None:
            return result
    except Exception:
        db.rollback()

    now = datetime.utcnow()
    users = db.query(User).filter(User.deleted_at == None).all()
    if not users:
        return {"distribution": {"labels": [], "values": []}, "scores": []}
    
    user_data = []
    for u in users:
        orders = db.query(Order).filter(
            Order.user_id == u.id,
            Order.status.in_(["completed", "paid", "shipped"])
        ).all()
        if orders:
            last_date = max(o.created_at for o in orders if o.created_at)
            recency_days = (now - last_date).days
            frequency = len(orders)
            monetary = sum(float(o.total_amount) for o in orders)
        else:
            recency_days = 999
            frequency = 0
            monetary = 0.0
        user_data.append({"user_id": u.id, "recency_days": recency_days, "frequency": frequency, "monetary": monetary})
    
    df = pd.DataFrame(user_data)
    
    # 分位数打分（5分最佳，1分最差）- recency是反向的
    for col, reverse in [("recency_days", True), ("frequency", False), ("monetary", False)]:
        if df[col].max() == df[col].min():
            df[f"{col.split('_')[0]}_score"] = 3
        else:
            labels = [1, 2, 3, 4, 5]
            try:
                bins = pd.qcut(df[col], 5, duplicates="drop")
                codes = bins.cat.codes + 1
                if reverse:
                    codes = 6 - codes
                df[f"{col.split('_')[0]}_score"] = codes
            except Exception:
                df[f"{col.split('_')[0]}_score"] = 3
    
    def get_segment(r, f, m):
        total = r + f + m
        if total >= 13: return "高价值用户"
        if total >= 9: return "忠诚用户"
        if total >= 6: return "潜力用户"
        return "流失用户"
    
    # 存储到数据库
    db.query(RfmScore).delete()
    segments_count = defaultdict(int)
    scores_list = []
    
    for _, row in df.iterrows():
        uid = int(row["user_id"])
        r, f, m = int(row["recency_score"]), int(row.get("frequency_score", 3)), int(row.get("monetary_score", 3))
        seg = get_segment(r, f, m)
        segments_count[seg] += 1
        
        db.add(RfmScore(user_id=uid, recency=r, frequency=f, monetary=m, segment=seg))
        scores_list.append({"user_id": uid, "recency": r, "frequency": f, "monetary": m, "segment": seg})
    
    db.commit()
    
    seg_labels = ["高价值用户", "忠诚用户", "潜力用户", "流失用户"]
    return {
        "distribution": {
            "labels": seg_labels,
            "values": [segments_count.get(l, 0) for l in seg_labels]
        },
        "scores": scores_list
    }


# ======================== K-Means 聚类 ========================

def calculate_cluster(db: Session, n_clusters: int = 5) -> dict:
    """K-Means聚类分析，基于RFM分值进行用户分群"""
    try:
        from app.services import algorithm_bridge
        result = algorithm_bridge.calculate_cluster(db, n_clusters=n_clusters)
        if result is not None:
            return result
    except Exception:
        db.rollback()

    from sklearn.cluster import KMeans
    
    rfm_records = db.query(RfmScore).all()
    if len(rfm_records) < n_clusters:
        return {"clusters": []}
    
    X = np.array([[s.recency or 1, s.frequency or 1, s.monetary or 1] for s in rfm_records])
    user_ids = [s.user_id for s in rfm_records]
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)
    
    # 存储聚类结果
    db.query(ClusterResult).delete()
    cluster_data = defaultdict(lambda: {"count": 0, "points": [], "center": []})
    
    cluster_names = ["高消费活跃用户", "中等消费用户", "潜力用户", "低频用户", "流失用户"]
    
    for i, label in enumerate(labels):
        db.add(ClusterResult(user_id=user_ids[i], cluster_label=int(label)))
        point = {"user_id": user_ids[i], "x": float(X[i][0]), "y": float(X[i][1]), "z": float(X[i][2])}
        cluster_data[int(label)]["points"].append(point)
        cluster_data[int(label)]["count"] += 1
    
    db.commit()
    
    # 构建中心点
    for label in range(n_clusters):
        if label in cluster_data:
            pts = cluster_data[label]["points"]
            if pts:
                cx = sum(p["x"] for p in pts) / len(pts)
                cy = sum(p["y"] for p in pts) / len(pts)
                cz = sum(p["z"] for p in pts) / len(pts)
                cluster_data[label]["center"] = [round(cx, 1), round(cy, 1), round(cz, 1)]
                cluster_data[label]["name"] = cluster_names[label] if label < len(cluster_names) else f"用户群{label}"
    
    return {"clusters": [{"label": k, **v} for k, v in sorted(cluster_data.items())]}


# ======================== Apriori 关联规则 ========================

def calculate_association(db: Session, min_support: float = 0.01, min_confidence: float = 0.5, limit: int = 20) -> list:
    """
    基于订单数据挖掘商品关联规则
    
    简化版Apriori：从订单中找出经常一起购买的商品对
    使用订单中的商品组合计算支持度和置信度
    """
    try:
        from app.services import algorithm_bridge
        result = algorithm_bridge.calculate_association(db, min_support=min_support, min_confidence=min_confidence, limit=limit)
        if result is not None:
            return result
    except Exception:
        db.rollback()

    from itertools import combinations
    
    # 获取所有订单的商品列表
    orders = db.query(OrderItem.order_id).distinct().all()
    order_product_map = defaultdict(set)
    for (oid,) in orders:
        items = db.query(OrderItem.product_id).filter(OrderItem.order_id == oid).all()
        order_product_map[oid] = {pid for (pid,) in items}
    
    total_orders = len(order_product_map)
    if total_orders < 2:
        return []
    
    # 统计商品对共现频率
    pair_count = defaultdict(int)
    product_single = defaultdict(int)
    
    for oid, products in order_product_map.items():
        for p in products:
            product_single[p] += 1
        for a, b in combinations(sorted(products), 2):
            pair_count[(a, b)] += 1
            pair_count[(b, a)] += 1  # 双向统计
    
    # 计算支持度和置信度
    rules = []
    for (a, b), count in pair_count.items():
        support = count / total_orders
        confidence = count / product_single[a] if product_single[a] > 0 else 0
        if support >= min_support and confidence >= min_confidence:
            # 计算提升度
            lift = confidence / (product_single[b] / total_orders) if product_single[b] > 0 else 0
            rules.append({
                "antecedents": [str(a)], "consequents": [str(b)],
                "support": round(support, 4), "confidence": round(confidence, 4), "lift": round(lift, 2)
            })
    
    # 按提升度排序
    rules.sort(key=lambda x: x["lift"], reverse=True)
    rules = rules[:limit]
    
    # 填充商品名称
    for rule in rules:
        a_id = int(rule["antecedents"][0])
        b_id = int(rule["consequents"][0])
        pa = db.query(Product).filter(Product.id == a_id).first()
        pb = db.query(Product).filter(Product.id == b_id).first()
        rule["antecedent_names"] = [pa.name if pa else ""]
        rule["consequent_names"] = [pb.name if pb else ""]
    
    return rules


# ======================== 用户画像 ========================

def get_user_profile(db: Session, user_id: int) -> dict:
    """生成用户画像数据"""
    user = db.query(User).filter(User.id == user_id, User.deleted_at == None).first()
    if not user:
        return None
    
    # 订单统计
    orders = db.query(Order).filter(Order.user_id == user_id, Order.status.in_(["completed", "paid", "shipped"])).all()
    total_orders = len(orders)
    avg_order_value = sum(float(o.total_amount) for o in orders) / total_orders if total_orders > 0 else 0.0
    
    # 最近购买天数
    if orders:
        last_date = max(o.created_at for o in orders if o.created_at)
        days_since = (datetime.utcnow() - last_date).days
    else:
        days_since = 0
    
    # 偏好分类（从购买的商品关联分类）
    cat_count = defaultdict(int)
    for o in orders:
        for item in o.items:
            if item.product and item.product.category:
                cat_count[item.product.category.name] += item.quantity
    
    prefer_categories = sorted(
        [{"name": k, "count": v} for k, v in cat_count.items()],
        key=lambda x: x["count"], reverse=True
    )[:5]
    
    # 活跃时段（从行为数据的created_at提取小时）
    from app.models.behavior import Behavior
    behaviors = db.query(Behavior.created_at).filter(Behavior.user_id == user_id).all()
    hour_count = defaultdict(int)
    for (ct,) in behaviors:
        if ct:
            hour_count[ct.hour] += 1
    active_hours = sorted(hour_count, key=hour_count.get, reverse=True)[:5] if hour_count else []
    
    # 标签
    tags = []
    rfm = db.query(RfmScore).filter(RfmScore.user_id == user_id).first()
    if rfm:
        tags.append(rfm.segment)
    if prefer_categories:
        tags.append(f"{prefer_categories[0]['name']}爱好者")
    
    return {
        "user_id": user_id, "nickname": user.nickname or "",
        "tags": tags, "prefer_categories": prefer_categories,
        "active_hours": active_hours, "avg_order_value": round(avg_order_value, 2),
        "total_orders": total_orders, "days_since_last_purchase": days_since
    }
