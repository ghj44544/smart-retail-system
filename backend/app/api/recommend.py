# =============================================================================
# 智能零售用户行为分析系统 - 推荐系统模块 API 路由
# =============================================================================
# 4个接口:
#   8.1 GET  /recommend/hot           - 热门商品推荐（Redis缓存）
#   8.2 GET  /recommend/association   - 关联规则推荐（根据商品）
#   8.3 GET  /recommend/personalized  - 个性化推荐（协同过滤）
#   8.4 POST /recommend/refresh       - 刷新推荐缓存
# =============================================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Dict, Optional
import json
from collections import defaultdict

from app.schemas.recommend import HotRecommendItem, AssociationRecommendItem, PersonalizedRecommendItem
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.behavior import Behavior
from app.models.base import get_db
from app.utils.response_utils import success_response
from app.utils.jwt_utils import get_current_user
from app.utils.redis_utils import cache_get, cache_set, cache_delete
from app.services.algorithm_outputs import (
    clear_algorithm_output_cache,
    get_algorithm_association_recommendations,
    get_algorithm_hot_recommendations,
    get_algorithm_personalized_recommendations,
)


router = APIRouter(prefix="/recommend", tags=["推荐系统"])


# ======================== 8.1 热门商品推荐 ========================

@router.get("/hot", summary="热门商品推荐")
async def get_hot_recommend(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取热门商品推荐列表
    
    优先从Redis缓存读取，缓存键: recommend_hot_{limit}
    """
    cache_key = f"recommend_hot_{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    algorithm_data = get_algorithm_hot_recommendations(db, limit)
    if algorithm_data:
        await cache_set(cache_key, json.dumps(algorithm_data, ensure_ascii=False), 300)
        return success_response(data=algorithm_data)
    
    products = db.query(Product).filter(
        Product.deleted_at == None, Product.status == "on"
    ).order_by(Product.sales_count.desc()).limit(limit).all()
    
    data = [
        HotRecommendItem(
            product_id=p.id, name=str(p.name), price=float(p.price),
            sales_count=p.sales_count or 0, rating=float(p.rating or 0)
        ).model_dump() for p in products
    ]
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)


# ======================== 8.2 关联规则推荐 ========================

@router.get("/association", summary="关联规则推荐")
async def get_association_recommend(
    product_id: int = Query(..., description="当前商品ID"),
    limit: int = Query(default=10, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    根据指定商品获取关联推荐
    
    基于订单共购关系查询关联商品。

    真实数据量较大时，实时 Apriori 会阻塞后端进程；这里改为轻量 SQL 聚合：
    1. 找出包含当前商品的订单
    2. 统计这些订单里共同出现的其他商品
    3. 无结果时用热门商品兜底
    """
    cache_key = f"recommend_association_v2_{product_id}_{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    algorithm_data = get_algorithm_association_recommendations(db, product_id, limit)
    if algorithm_data:
        await cache_set(cache_key, json.dumps(algorithm_data, ensure_ascii=False), 300)
        return success_response(data=algorithm_data)

    target_order_ids = (
        db.query(OrderItem.order_id)
        .filter(OrderItem.product_id == product_id)
        .subquery()
    )
    target_order_count = (
        db.query(func.count(func.distinct(OrderItem.order_id)))
        .filter(OrderItem.product_id == product_id)
        .scalar()
        or 0
    )
    total_order_count = db.query(func.count(Order.id)).scalar() or 1

    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.price,
            Product.sales_count,
            func.count(func.distinct(OrderItem.order_id)).label("co_count"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id.in_(target_order_ids))
        .filter(Product.id != product_id)
        .filter(Product.deleted_at == None)
        .filter(Product.status == "on")
        .group_by(Product.id, Product.name, Product.price)
        .order_by(func.count(OrderItem.id).desc(), Product.sales_count.desc())
        .limit(limit)
        .all()
    )

    row_product_ids = [row.id for row in rows]
    product_order_counts = {}
    if row_product_ids:
        product_order_counts = dict(
            db.query(
                OrderItem.product_id,
                func.count(func.distinct(OrderItem.order_id)),
            )
            .filter(OrderItem.product_id.in_(row_product_ids))
            .group_by(OrderItem.product_id)
            .all()
        )

    data = []
    for row in rows:
        confidence = float(row.co_count) / float(target_order_count) if target_order_count else 0.0
        other_order_count = product_order_counts.get(row.id, row.co_count)
        other_probability = float(other_order_count) / float(total_order_count) if total_order_count else 0.0
        lift = confidence / other_probability if other_probability else 1.0
        data.append(
            AssociationRecommendItem(
                product_id=row.id,
                name=str(row.name),
                price=float(row.price),
                confidence=round(min(confidence, 1.0), 4),
                lift=round(max(lift, 1.0), 2),
            ).model_dump()
        )

    if not data:
        hot_products = (
            db.query(Product)
            .filter(Product.deleted_at == None, Product.status == "on", Product.id != product_id)
            .order_by(Product.sales_count.desc())
            .limit(limit)
            .all()
        )
        max_sales = max([p.sales_count or 0 for p in hot_products] or [1]) or 1
        data = []
        for p in hot_products:
            confidence = float(p.sales_count or 0) / float(max_sales)
            data.append(
                AssociationRecommendItem(
                    product_id=p.id,
                    name=str(p.name),
                    price=float(p.price),
                    confidence=round(confidence, 4),
                    lift=round(1.0 + confidence, 2),
                ).model_dump()
            )

    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)


# ======================== 8.3 个性化推荐 ========================

@router.get("/personalized", summary="个性化推荐")
async def get_personalized_recommend(
    user_id: int = Query(..., description="用户ID"),
    limit: int = Query(default=10, ge=1, le=20, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取个性化推荐（轻量规则版）
    
    推荐策略：
    1. 找出用户购买过的商品分类
    2. 在同分类中推荐高销量商品（排除已购买）
    3. 如果不够，补充全局热门商品
    4. 附加推荐理由
    """
    cache_key = f"recommend_personalized_v2_{user_id}_{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))

    algorithm_data = get_algorithm_personalized_recommendations(db, user_id, limit)
    if algorithm_data:
        await cache_set(cache_key, json.dumps(algorithm_data, ensure_ascii=False), 300)
        return success_response(data=algorithm_data)

    # 1. 获取用户已购商品
    bought = set()
    orders = db.query(Order).filter(
        Order.user_id == user_id, Order.status.in_(["completed", "paid", "shipped"])
    ).all()
    for o in orders:
        for item in o.items:
            bought.add(item.product_id)
    
    # 2. 获取用户偏好分类
    cat_ids = set()
    for pid in bought:
        p = db.query(Product).filter(Product.id == pid).first()
        if p and p.category_id:
            cat_ids.add(p.category_id)
    
    # 3. 在偏好分类中推荐
    result = []
    seen = set(bought)
    
    for cid in cat_ids:
        candidates = db.query(Product).filter(
            Product.category_id == cid, Product.deleted_at == None,
            Product.status == "on", ~Product.id.in_(bought)
        ).order_by(Product.sales_count.desc()).limit(3).all()
        for p in candidates:
            if p.id not in seen:
                seen.add(p.id)
                result.append(PersonalizedRecommendItem(
                    product_id=p.id, name=str(p.name), price=float(p.price),
                    score=round(float(p.sales_count or 0) / 10000, 2),
                    reason="根据您的购买偏好推荐"
                ).model_dump())
    
    # 4. 补充热门商品
    if len(result) < limit:
        hot = db.query(Product).filter(
            Product.deleted_at == None, Product.status == "on",
            ~Product.id.in_(seen)
        ).order_by(Product.sales_count.desc()).limit(limit - len(result)).all()
        for p in hot:
            seen.add(p.id)
            result.append(PersonalizedRecommendItem(
                product_id=p.id, name=str(p.name), price=float(p.price),
                score=round(float(p.sales_count or 0) / 10000, 2),
                reason="热门商品推荐"
            ).model_dump())
    
    data = result[:limit]
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), 300)
    return success_response(data=data)


# ======================== 8.4 刷新推荐结果 ========================

@router.post("/refresh", summary="刷新推荐结果")
async def refresh_recommend(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    清除推荐相关Redis缓存，下次访问时自动重新计算
    
    清除的缓存键前缀: recommend_*, hot_products_*
    """
    # 清除热门推荐缓存
    for i in [5, 10, 20, 50]:
        await cache_delete(f"recommend_hot_{i}")
        await cache_delete(f"hot_products_sales_{i}")
        await cache_delete(f"hot_products_rating_{i}")
    
    # 清除常见推荐缓存。Redis 工具当前只支持精确 key，这里清理常用数量的缓存。
    # 个性化/关联推荐的其他 key 会在 300 秒后自动过期。
    for i in [5, 10, 20]:
        await cache_delete(f"recommend_association_1_{i}")

    clear_algorithm_output_cache()
    
    return success_response(data={"refreshed": True}, message="推荐缓存已刷新")
