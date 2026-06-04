# =============================================================================
# 智能零售用户行为分析系统 - 订单管理模块 API 路由
# =============================================================================
# 5个接口:
#   5.1 GET  /orders                  - 分页获取订单列表
#   5.2 GET  /orders/{order_id}       - 获取订单详情
#   5.3 POST /orders                  - 创建订单
#   5.4 PUT  /orders/{order_id}/status - 更新订单状态
#   5.5 GET  /orders/trend            - 获取销售趋势
#
# 注意: /trend 必须在 /{order_id} 之前定义，避免路由冲突
# =============================================================================

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Optional
from sqlalchemy import func as sqlfunc

from app.schemas.order import (
    CreateOrderRequest, CreateOrderItemRequest, UpdateOrderStatusRequest,
    OrderListItem, OrderDetailResponse, OrderItemResponse, OrderCreateResponse, TrendResponse
)
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from app.models.base import get_db
from app.utils.response_utils import success_response, error_response, paginated_response
from app.utils.jwt_utils import get_current_user
import random


router = APIRouter(prefix="/orders", tags=["订单管理"])


# ======================== 辅助函数 ========================

def generate_order_no() -> str:
    """生成唯一订单编号: ORD + 日期 + 随机4位"""
    now = datetime.utcnow()
    return f"ORD{now.strftime('%Y%m%d')}{random.randint(1000, 9999)}"


# ======================== 5.5 销售趋势（必须放在/{order_id}之前） ========================

@router.get("/trend", summary="获取销售趋势")
async def get_order_trend(
    period: str = Query(default="day", description="时间粒度: day/week/month"),
    days: int = Query(default=30, ge=1, le=365, description="查询天数"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    获取销售趋势数据（用于图表展示）
    
    对应API: 5.5 GET /orders/trend
    返回: {dates: [...], sales: [...], orders: [...]}
    """
    end = db.query(sqlfunc.max(Order.created_at)).filter(
        Order.status.in_(["completed", "paid", "shipped"])
    ).scalar() or datetime.utcnow()
    start_date = end - timedelta(days=days)
    
    # 查询日期范围内的已完成订单
    orders = db.query(Order).filter(
        Order.created_at >= start_date,
        Order.created_at <= end,
        Order.status.in_(["completed", "paid", "shipped"])
    ).order_by(Order.created_at.asc()).all()
    
    # 按天聚合
    from collections import defaultdict
    daily = defaultdict(lambda: {"sales": 0.0, "count": 0})
    for o in orders:
        key = o.created_at.strftime("%Y-%m-%d")
        daily[key]["sales"] += float(o.total_amount)
        daily[key]["count"] += 1
    
    # 生成日期序列
    dates, sales_list, orders_list = [], [], []
    for i in range(days, -1, -1):
        d = (end - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(d)
        sales_list.append(round(daily[d]["sales"], 2))
        orders_list.append(daily[d]["count"])
    
    return success_response(data=TrendResponse(
        dates=dates, sales=sales_list, orders=orders_list
    ).model_dump())


# ======================== 5.1 获取订单列表 ========================

@router.get("", summary="获取订单列表")
async def get_orders(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(default=None, description="用户ID筛选"),
    status: Optional[str] = Query(default=None, description="订单状态"),
    start_date: Optional[str] = Query(default=None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(default=None, description="结束日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """分页获取订单列表，支持用户、状态、日期筛选"""
    query = db.query(Order)
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    if status:
        query = query.filter(Order.status == status)
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    if end_date:
        query = query.filter(Order.created_at <= end_date + " 23:59:59")
    
    total = query.count()
    stats_subquery = query.with_entities(Order.id).subquery()
    stats_query = db.query(Order).join(stats_subquery, Order.id == stats_subquery.c.id)
    stats = {
        "total": total,
        "sales_amount": float(stats_query.filter(
            Order.status.in_(["completed", "paid", "shipped"])
        ).with_entities(sqlfunc.coalesce(sqlfunc.sum(Order.total_amount), 0)).scalar() or 0),
        "completed": stats_query.filter(Order.status == "completed").count(),
        "pending": stats_query.filter(Order.status == "pending").count(),
        "cancelled": stats_query.filter(Order.status == "cancelled").count(),
    }
    orders = query.with_entities(
        Order.id, Order.order_no, Order.user_id, Order.total_amount, Order.status, Order.created_at
    ).order_by(Order.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    order_ids = [o.id for o in orders]
    user_ids = [o.user_id for o in orders if o.user_id]
    user_map = {}
    if user_ids:
        user_map = {
            u.id: (u.nickname or u.username or "")
            for u in db.query(User.id, User.nickname, User.username).filter(User.id.in_(user_ids)).all()
        }
    item_count_map = {}
    if order_ids:
        item_count_map = dict(
            db.query(OrderItem.order_id, sqlfunc.coalesce(sqlfunc.sum(OrderItem.quantity), 0))
            .filter(OrderItem.order_id.in_(order_ids))
            .group_by(OrderItem.order_id)
            .all()
        )

    items = []
    for o in orders:
        user_name = user_map.get(o.user_id, "")
        item_count = int(item_count_map.get(o.id, 0))
        items.append(OrderListItem(
            id=o.id, order_no=str(o.order_no), user_id=o.user_id,
            user_name=user_name, total_amount=float(o.total_amount),
            status=str(o.status), item_count=item_count, created_at=o.created_at
        ).model_dump())
    
    response = paginated_response(items=items, total=total, page=page, page_size=page_size)
    response["data"]["stats"] = stats
    return response


# ======================== 5.2 获取订单详情 ========================

@router.get("/{order_id}", summary="获取订单详情")
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """获取订单详情，包含订单商品明细"""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return error_response(code=status.HTTP_404_NOT_FOUND, message="订单不存在")
    
    user_name = ""
    if order.user_id:
        u = db.query(User).filter(User.id == order.user_id).first()
        user_name = u.nickname if u else ""
    
    item_list = []
    for item in order.items:
        pname = ""
        if item.product_id:
            p = db.query(Product).filter(Product.id == item.product_id).first()
            pname = p.name if p else ""
        item_list.append(OrderItemResponse(
            product_id=item.product_id, product_name=pname,
            price=float(item.price), quantity=item.quantity
        ).model_dump())
    
    detail = OrderDetailResponse(
        id=order.id, order_no=str(order.order_no), user_id=order.user_id,
        user_name=user_name, total_amount=float(order.total_amount),
        status=str(order.status), items=item_list,
        created_at=order.created_at, paid_at=order.paid_at,
        completed_at=order.completed_at
    )
    return success_response(data=detail.model_dump())


# ======================== 5.3 创建订单 ========================

@router.post("", summary="创建订单")
async def create_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """创建新订单，生成唯一订单编号，计算总金额，创建订单明细"""
    # 验证用户存在
    user = db.query(User).filter(User.id == request.user_id, User.deleted_at == None).first()
    if not user:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="用户不存在")
    
    # 验证并计算总金额
    total = 0.0
    order_items_data = []
    for item in request.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.deleted_at == None).first()
        if not product:
            return error_response(code=status.HTTP_400_BAD_REQUEST, message=f"商品 {item.product_id} 不存在")
        if product.stock < item.quantity:
            return error_response(code=status.HTTP_400_BAD_REQUEST, message=f"商品 '{product.name}' 库存不足")
        # 扣减库存
        product.stock -= item.quantity
        line_total = float(product.price) * item.quantity
        total += line_total
        order_items_data.append({"product": product, "quantity": item.quantity, "price": float(product.price)})
    
    # 创建订单
    order_no = generate_order_no()
    order = Order(order_no=order_no, user_id=request.user_id, total_amount=total, status="pending")
    db.add(order)
    db.flush()  # 获取order.id
    
    # 创建订单明细
    for od in order_items_data:
        oi = OrderItem(order_id=order.id, product_id=od["product"].id, price=od["price"], quantity=od["quantity"])
        db.add(oi)
    
    db.commit()
    db.refresh(order)
    
    resp = OrderCreateResponse(
        id=order.id, order_no=str(order.order_no),
        total_amount=float(order.total_amount), status=str(order.status),
        created_at=order.created_at
    )
    return success_response(data=resp.model_dump(), message="订单创建成功")


# ======================== 5.4 更新订单状态 ========================

@router.put("/{order_id}/status", summary="更新订单状态")
async def update_order_status(
    order_id: int,
    request: UpdateOrderStatusRequest,
    db: Session = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    更新订单状态
    
    状态流转规则:
      pending → paid → shipped → completed
      pending → cancelled
    当状态变为 completed 时，更新商品销量
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        return error_response(code=status.HTTP_404_NOT_FOUND, message="订单不存在")
    
    valid_statuses = ["pending", "paid", "shipped", "completed", "cancelled"]
    if request.status not in valid_statuses:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message=f"无效状态，允许: {', '.join(valid_statuses)}")
    
    old_status = order.status
    order.status = request.status
    
    # 根据新状态更新时间戳
    if request.status == "paid":
        order.paid_at = datetime.utcnow()
    elif request.status == "completed":
        order.completed_at = datetime.utcnow()
        # 更新商品销量（订单完成时）
        for item in order.items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.sales_count = (product.sales_count or 0) + item.quantity
    
    db.commit()
    db.refresh(order)
    
    return success_response(
        data={"id": order.id, "order_no": str(order.order_no), "status": str(order.status), "old_status": str(old_status)},
        message="订单状态更新成功"
    )
