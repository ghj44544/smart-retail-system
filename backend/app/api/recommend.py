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
from app.services.analysis_service import calculate_association


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
    
    基于Apriori关联规则，找出与当前商品最相关的其他商品
    """
    # 获取所有关联规则
    rules = calculate_association(db, min_support=0.001, min_confidence=0.1, limit=100)
    
    # 筛选以当前商品为前件的规则
    matched = []
    for r in rules:
        ant = r["antecedents"]
        con = r["consequents"]
        # 检查当前商品是否在前件或后件中
        if str(product_id) in ant:
            matched.append({
                "product_id": int(con[0]),
                "name": r["consequent_names"][0] if r["consequent_names"] else "",
                "confidence": r["confidence"],
                "lift": r["lift"]
            })
        elif str(product_id) in con:
            matched.append({
                "product_id": int(ant[0]),
                "name": r["antecedent_names"][0] if r["antecedent_names"] else "",
                "confidence": r["confidence"],
                "lift": r["lift"]
            })
    
    # 去重并排序
    seen = set()
    unique = []
    for m in sorted(matched, key=lambda x: x["lift"], reverse=True):
        if m["product_id"] not in seen:
            seen.add(m["product_id"])
            # 补充价格
            p = db.query(Product).filter(Product.id == m["product_id"]).first()
            m["price"] = float(p.price) if p else 0.0
            unique.append(m)
    
    data = [
        AssociationRecommendItem(**u).model_dump()
        for u in unique[:limit]
    ]
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
    获取个性化推荐（基于协同过滤思想）
    
    推荐策略：
    1. 找出用户购买过的商品分类
    2. 在同分类中推荐高销量商品（排除已购买）
    3. 如果不够，补充全局热门商品
    4. 附加推荐理由
    """
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
    
    return success_response(data=result[:limit])


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
    
    return success_response(data={"refreshed": True}, message="推荐缓存已刷新")
