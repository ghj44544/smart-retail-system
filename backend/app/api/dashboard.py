# =============================================================================
# 智能零售用户行为分析系统 - 数据驾驶舱模块 API 路由
# =============================================================================
# 5个接口:
#   9.1 GET /dashboard/metrics         - 核心指标（Redis缓存）
#   9.2 GET /dashboard/sales-trend     - 销售趋势
#   9.3 GET /dashboard/user-behavior   - 用户行为趋势
#   9.4 GET /dashboard/product-ranking - 商品排行
#   9.5 GET /dashboard/user-segments   - 用户分群分布
# =============================================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc, distinct
from datetime import datetime, timedelta
from typing import Dict
from collections import defaultdict
import json

from app.schemas.dashboard import (
    DashboardMetrics, SalesTrendData, BehaviorTrendData,
    ProductRankingItem, ProductRankingData, UserSegmentItem, UserSegmentsData
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.models.product import Product
from app.models.behavior import Behavior
from app.models.rfm_score import RfmScore
from app.models.base import get_db
from app.utils.response_utils import success_response
from app.utils.jwt_utils import get_current_user
from app.utils.redis_utils import cache_get, cache_set


router = APIRouter(prefix="/dashboard", tags=["数据驾驶舱"])


# ======================== 9.1 核心指标 ========================

@router.get("/metrics", summary="获取核心指标")
async def get_metrics(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取驾驶舱核心指标（Redis缓存60秒）"""
    cache_key = "dashboard_metrics"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    # 销售统计（已完成订单）
    completed = db.query(Order).filter(Order.status.in_(["completed", "paid", "shipped"]))
    total_sales = db.query(sqlfunc.coalesce(sqlfunc.sum(Order.total_amount), 0)).filter(
        Order.status.in_(["completed", "paid", "shipped"])
    ).scalar() or 0
    total_orders = completed.count()
    avg_order_value = round(float(total_sales) / total_orders, 2) if total_orders > 0 else 0.0

    # 用户总数（未删除）
    total_users = db.query(User).filter(User.deleted_at == None).count()

    # 今日数据
    today = datetime.utcnow().strftime("%Y-%m-%d")
    today_orders = db.query(Order).filter(
        Order.created_at >= today, Order.status.in_(["completed", "paid", "shipped"])
    ).count()
    today_sales = db.query(sqlfunc.coalesce(sqlfunc.sum(Order.total_amount), 0)).filter(
        Order.created_at >= today, Order.status.in_(["completed", "paid", "shipped"])
    ).scalar() or 0

    # 转化率（浏览→购买）
    view_count = db.query(Behavior).filter(Behavior.behavior_type == "view").count()
    buy_count = db.query(Behavior).filter(Behavior.behavior_type == "buy").count()
    conversion_rate = round(buy_count / view_count, 4) if view_count > 0 else 0.0

    # 复购率（购买>=2次的用户占比）
    buy_users = db.query(Behavior.user_id).filter(Behavior.behavior_type == "buy").distinct().all()
    buy_user_ids = [b[0] for b in buy_users]
    repeat_count = 0
    if buy_user_ids:
        repeat_count = db.query(Behavior.user_id).filter(
            Behavior.behavior_type == "buy", Behavior.user_id.in_(buy_user_ids)
        ).group_by(Behavior.user_id).having(
            sqlfunc.count(Behavior.id) >= 2
        ).count()
    repurchase_rate = round(repeat_count / len(buy_user_ids), 2) if buy_user_ids else 0.0

    metrics = DashboardMetrics(
        total_sales=round(float(total_sales), 2), total_orders=total_orders,
        avg_order_value=avg_order_value, total_users=total_users,
        today_sales=round(float(today_sales), 2), today_orders=today_orders,
        conversion_rate=conversion_rate, repurchase_rate=repurchase_rate
    ).model_dump()

    await cache_set(cache_key, json.dumps(metrics, ensure_ascii=False), 60)
    return success_response(data=metrics)


# ======================== 9.2 销售趋势 ========================

@router.get("/sales-trend", summary="获取销售趋势")
async def get_sales_trend(
    period: str = Query(default="day", description="时间粒度: day/week/month"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取销售趋势数据（折线图）"""
    if period not in ["day", "week", "month"]:
        period = "day"

    cache_key = f"dashboard_sales_trend_{period}"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    end = db.query(sqlfunc.max(Order.created_at)).filter(
        Order.status.in_(["completed", "paid", "shipped"])
    ).scalar() or datetime.utcnow()
    days = 30 if period == "day" else 84 if period == "week" else 365
    start = end - timedelta(days=days)

    orders = db.query(Order).filter(
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status.in_(["completed", "paid", "shipped"])
    ).order_by(Order.created_at.asc()).all()

    dates, sales, order_counts, user_counts = [], [], [], []

    if period == "day":
        buckets = defaultdict(lambda: {"sales": 0.0, "orders": 0, "users": set()})
        for o in orders:
            key = o.created_at.strftime("%Y-%m-%d")
            buckets[key]["sales"] += float(o.total_amount)
            buckets[key]["orders"] += 1
            buckets[key]["users"].add(o.user_id)

        for i in range(30, -1, -1):
            key = (end - timedelta(days=i)).strftime("%Y-%m-%d")
            dates.append(key)
            sales.append(round(buckets[key]["sales"], 2))
            order_counts.append(buckets[key]["orders"])
            user_counts.append(len(buckets[key]["users"]))
    elif period == "week":
        week_starts = [(end - timedelta(days=end.weekday()) - timedelta(weeks=i)).date() for i in range(11, -1, -1)]
        buckets = {d: {"sales": 0.0, "orders": 0, "users": set()} for d in week_starts}
        for o in orders:
            week_start = (o.created_at - timedelta(days=o.created_at.weekday())).date()
            if week_start in buckets:
                buckets[week_start]["sales"] += float(o.total_amount)
                buckets[week_start]["orders"] += 1
                buckets[week_start]["users"].add(o.user_id)

        for week_start in week_starts:
            dates.append(week_start.strftime("%m-%d"))
            sales.append(round(buckets[week_start]["sales"], 2))
            order_counts.append(buckets[week_start]["orders"])
            user_counts.append(len(buckets[week_start]["users"]))
    else:
        month_keys = []
        year, month = end.year, end.month
        for _ in range(12):
            month_keys.append((year, month))
            month -= 1
            if month == 0:
                year -= 1
                month = 12
        month_keys.reverse()

        buckets = {key: {"sales": 0.0, "orders": 0, "users": set()} for key in month_keys}
        for o in orders:
            key = (o.created_at.year, o.created_at.month)
            if key in buckets:
                buckets[key]["sales"] += float(o.total_amount)
                buckets[key]["orders"] += 1
                buckets[key]["users"].add(o.user_id)

        for key in month_keys:
            dates.append(f"{key[0]}-{key[1]:02d}")
            sales.append(round(buckets[key]["sales"], 2))
            order_counts.append(buckets[key]["orders"])
            user_counts.append(len(buckets[key]["users"]))

    data = SalesTrendData(
        dates=dates, sales=sales, orders=order_counts, users=user_counts
    ).model_dump()
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)


# ======================== 9.3 用户行为趋势 ========================

@router.get("/user-behavior", summary="获取用户行为趋势")
async def get_user_behavior(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取用户行为趋势（PV/UV/新用户）"""
    cache_key = "dashboard_user_behavior"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    latest_behavior_at = db.query(sqlfunc.max(Behavior.created_at)).scalar()
    latest_user_at = db.query(sqlfunc.max(User.created_at)).filter(User.deleted_at == None).scalar()
    end = latest_behavior_at or latest_user_at or datetime.utcnow()
    start = end - timedelta(days=30)
    records = db.query(Behavior).filter(
        Behavior.created_at >= start,
        Behavior.created_at <= end,
    ).order_by(Behavior.created_at.asc()).all()
    new_users = db.query(User).filter(
        User.created_at >= start,
        User.created_at <= end,
        User.deleted_at == None,
    ).all()

    daily = defaultdict(lambda: {"pv": 0, "users": set(), "view": 0, "cart": 0, "buy": 0})
    for r in records:
        key = r.created_at.strftime("%Y-%m-%d")
        daily[key]["pv"] += 1
        daily[key]["users"].add(r.user_id)
        if r.behavior_type == "view":
            daily[key]["view"] += 1
        elif r.behavior_type == "cart":
            daily[key]["cart"] += 1
        elif r.behavior_type == "buy":
            daily[key]["buy"] += 1

    new_daily = defaultdict(int)
    for u in new_users:
        key = u.created_at.strftime("%Y-%m-%d") if u.created_at else ""
        if key:
            new_daily[key] += 1

    dates, pv, uv, view_count, cart_count, buy_count, nv = [], [], [], [], [], [], []
    for i in range(30, -1, -1):
        d = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)
        pv.append(daily[d]["pv"])
        uv.append(len(daily[d]["users"]))
        view_count.append(daily[d]["view"])
        cart_count.append(daily[d]["cart"])
        buy_count.append(daily[d]["buy"])
        nv.append(new_daily[d])

    data = BehaviorTrendData(
        dates=dates, pv=pv, uv=uv, view_count=view_count,
        cart_count=cart_count, buy_count=buy_count, new_users=nv
    ).model_dump()
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)


# ======================== 9.4 商品排行 ========================

@router.get("/product-ranking", summary="获取商品表现排行")
async def get_product_ranking(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    sort_by: str = Query(default="sales", description="排序字段: sales/revenue/rating"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取商品销售排行"""
    cache_key = f"dashboard_product_ranking_{limit}_{sort_by}"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    products = db.query(Product).filter(
        Product.deleted_at == None, Product.status == "on"
    ).all()

    ranking = []
    for p in products:
        revenue = float(p.price) * (p.sales_count or 0)
        ranking.append(ProductRankingItem(
            name=str(p.name), sales=p.sales_count or 0, revenue=round(revenue, 2)
        ))

    if sort_by == "revenue":
        ranking.sort(key=lambda x: x.revenue, reverse=True)
    elif sort_by == "rating":
        # 按数据库rating字段排序（重新从Product查询rating）
        rating_map = {p.name: float(p.rating or 0) for p in products}
        ranking.sort(key=lambda x: rating_map.get(x.name, 0), reverse=True)
    else:
        ranking.sort(key=lambda x: x.sales, reverse=True)

    data = ProductRankingData(products=ranking[:limit]).model_dump()
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)


# ======================== 9.5 用户分群分布 ========================

@router.get("/user-segments", summary="获取用户分群分布")
async def get_user_segments(
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取用户分群分布（饼图数据）
    
    如果RFM数据不存在，自动触发RFM计算
    """
    cache_key = "dashboard_user_segments"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    scores = db.query(RfmScore).all()
    if not scores:
        from app.services.analysis_service import calculate_rfm
        calculate_rfm(db)
        scores = db.query(RfmScore).all()

    seg_count = defaultdict(int)
    for s in scores:
        seg = s.segment or "流失用户"
        seg_count[seg] += 1

    total_users = db.query(User).filter(User.deleted_at == None).count()
    scored_users = sum(seg_count.values())
    if total_users > scored_users:
        seg_count["新用户"] += total_users - scored_users

    seg_labels = ["高价值用户", "忠诚用户", "潜力用户", "新用户", "流失用户"]
    segments = [UserSegmentItem(name=l, value=seg_count.get(l, 0)) for l in seg_labels]

    data = UserSegmentsData(segments=segments).model_dump()
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)
