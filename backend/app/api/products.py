# =============================================================================
# 智能零售用户行为分析系统 - 商品管理模块 API 路由
# =============================================================================
# 模块功能：7个接口
#   4.1 GET    /products            - 分页获取商品列表（分类筛选、搜索）
#   4.2 GET    /products/{id}       - 获取商品详情（含关联商品）
#   4.3 POST   /products            - 创建商品
#   4.4 PUT    /products/{id}       - 更新商品信息
#   4.5 DELETE /products/{id}       - 软删除商品
#   4.6 GET    /categories          - 获取分类列表
#   4.7 GET    /products/hot        - 热门商品排行（Redis缓存）
#
# 对应 API 接口规范文档：第四章「商品管理接口」
# =============================================================================

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Optional, List
import json

from app.schemas.product import (
    CreateProductRequest, UpdateProductRequest, ProductListItem,
    ProductDetailResponse, ProductCreateResponse, CategoryResponse, HotProductItem
)
from app.models.product import Product
from app.models.category import Category
from app.models.base import get_db
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.jwt_utils import get_current_user
from app.utils.redis_utils import cache_get, cache_set


router = APIRouter(prefix="/products", tags=["商品管理"])


# ======================== 4.1 获取商品列表 ========================

@router.get("", summary="获取商品列表")
async def get_products(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
    category_id: Optional[int] = Query(default=None, description="分类ID"),
    status: Optional[str] = Query(default=None, description="状态（on/off）"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """分页获取商品列表，支持分类筛选、关键词搜索、状态下架过滤"""
    # 默认排除已删除商品
    query = db.query(Product).filter(Product.deleted_at == None)
    
    # 关键词搜索（商品名称或商品编号）
    if keyword:
        query = query.filter(
            (Product.name.like(f"%{keyword}%")) |
            (Product.product_no.like(f"%{keyword}%"))
        )
    
    # 分类筛选
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # 状态筛选
    if status in ["on", "off"]:
        query = query.filter(Product.status == status)
    
    total = query.count()
    products = query.order_by(Product.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 构建响应列表，关联查询分类名称
    items = []
    for p in products:
        category_name = None
        if p.category_id:
            cat = db.query(Category).filter(Category.id == p.category_id).first()
            category_name = cat.name if cat else None
        
        items.append(ProductListItem(
            id=p.id, product_no=str(p.product_no), name=str(p.name),
            category_id=p.category_id, category_name=category_name,
            price=float(p.price), stock=p.stock, status=str(p.status),
            sales_count=p.sales_count or 0, rating=float(p.rating or 0),
            created_at=p.created_at
        ).model_dump())
    
    return paginated_response(items=items, total=total, page=page, page_size=page_size)


# ======================== 4.7 热门商品排行 ========================
# 注意：/hot 必须在 /{product_id} 之前定义，否则 FastAPI 会把 "hot" 当做 product_id 参数

@router.get("/hot", summary="获取热门商品排行")
async def get_hot_products(
    limit: int = Query(default=10, ge=1, le=50, description="返回数量"),
    sort_by: str = Query(default="sales", description="排序字段：sales/rating"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取热门商品排行
    
    优先从 Redis 缓存读取，缓存失效则查询数据库并更新缓存
    缓存键: hot_products_{sort_by}_{limit}
    过期时间: 300秒（5分钟）
    """
    cache_key = f"hot_products_{sort_by}_{limit}"
    cached = await cache_get(cache_key)
    if cached:
        return success_response(data=json.loads(cached))
    
    if sort_by == "rating":
        products = db.query(Product).filter(
            Product.deleted_at == None, Product.status == "on"
        ).order_by(Product.rating.desc()).limit(limit).all()
    else:
        products = db.query(Product).filter(
            Product.deleted_at == None, Product.status == "on"
        ).order_by(Product.sales_count.desc()).limit(limit).all()
    
    data = [
        HotProductItem(
            product_id=p.id, name=str(p.name),
            sales_count=p.sales_count or 0, rating=float(p.rating or 0),
            price=float(p.price)
        ).model_dump() for p in products
    ]
    await cache_set(cache_key, json.dumps(data, ensure_ascii=False), expires_in=300)
    return success_response(data=data)


# ======================== 4.2 获取商品详情 ========================

@router.get("/{product_id}", summary="获取商品详情")
async def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取商品详情，包含关联商品列表（同分类下其他商品ID）"""
    product = db.query(Product).filter(
        Product.id == product_id, Product.deleted_at == None
    ).first()
    
    if not product:
        return error_response(code=status.HTTP_404_NOT_FOUND, message="商品不存在")
    
    # 分类名称
    category_name = None
    if product.category_id:
        cat = db.query(Category).filter(Category.id == product.category_id).first()
        category_name = cat.name if cat else None
    
    # 关联商品：同分类下的其他商品（最多5个）
    related_ids = []
    if product.category_id:
        related = db.query(Product.id).filter(
            Product.category_id == product.category_id,
            Product.id != product.id,
            Product.deleted_at == None,
            Product.status == "on"
        ).limit(5).all()
        related_ids = [r[0] for r in related]
    
    detail = ProductDetailResponse(
        id=product.id, product_no=str(product.product_no), name=str(product.name),
        description=product.description, category_id=product.category_id,
        category_name=category_name, price=float(product.price),
        stock=product.stock or 0, status=str(product.status),
        sales_count=product.sales_count or 0, rating=float(product.rating or 0),
        related_products=related_ids, created_at=product.created_at
    )
    return success_response(data=detail.model_dump())


# ======================== 4.3 创建商品 ========================

@router.post("", summary="创建商品")
async def create_product(
    request: CreateProductRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """创建新商品，商品编号全局唯一"""
    # 检查商品编号唯一性
    exist = db.query(Product).filter(Product.product_no == request.product_no).first()
    if exist:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message=f"商品编号 '{request.product_no}' 已存在")
    
    # 校验状态
    if request.status not in ["on", "off"]:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="状态必须为 on 或 off")
    
    # 校验分类（如果提供）
    if request.category_id:
        cat = db.query(Category).filter(Category.id == request.category_id).first()
        if not cat:
            return error_response(code=status.HTTP_400_BAD_REQUEST, message="指定的分类不存在")
    
    product = Product(
        product_no=request.product_no, name=request.name,
        description=request.description, category_id=request.category_id,
        price=request.price, stock=request.stock, status=request.status
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    resp = ProductCreateResponse(
        id=product.id, product_no=str(product.product_no), name=str(product.name),
        category_id=product.category_id, price=float(product.price),
        status=str(product.status), created_at=product.created_at
    )
    return success_response(data=resp.model_dump(), message="商品创建成功")


# ======================== 4.4 更新商品 ========================

@router.put("/{product_id}", summary="更新商品信息")
async def update_product(
    product_id: int,
    request: UpdateProductRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """更新商品信息，只更新传入的字段"""
    product = db.query(Product).filter(
        Product.id == product_id, Product.deleted_at == None
    ).first()
    if not product:
        return error_response(code=status.HTTP_404_NOT_FOUND, message="商品不存在")
    
    update_data = request.model_dump(exclude_unset=True)
    
    # 如果修改商品编号，检查唯一性
    if "product_no" in update_data and update_data["product_no"]:
        exist = db.query(Product).filter(
            Product.product_no == update_data["product_no"],
            Product.id != product_id
        ).first()
        if exist:
            return error_response(code=status.HTTP_400_BAD_REQUEST, message="商品编号已存在")
    
    for field, value in update_data.items():
        if value is not None:
            setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # 清除热门商品缓存（数据变更后缓存失效）
    from app.utils.redis_utils import cache_delete
    await cache_delete("hot_products")
    
    return success_response(
        data={"id": product.id, "name": str(product.name), "updated": True},
        message="商品更新成功"
    )


# ======================== 4.5 删除商品（软删除） ========================

@router.delete("/{product_id}", summary="删除商品")
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """软删除商品，设置deleted_at时间戳"""
    product = db.query(Product).filter(
        Product.id == product_id, Product.deleted_at == None
    ).first()
    if not product:
        return error_response(code=status.HTTP_404_NOT_FOUND, message="商品不存在或已被删除")
    
    product.deleted_at = datetime.utcnow()
    db.commit()
    
    # 清除缓存
    from app.utils.redis_utils import cache_delete
    await cache_delete("hot_products")
    
    return success_response(data=None, message="商品已删除")
