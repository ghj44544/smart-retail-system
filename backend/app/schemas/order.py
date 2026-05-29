# =============================================================================
# 智能零售用户行为分析系统 - 订单管理模块 Schema 定义
# =============================================================================
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ======================== 请求模型 ========================

class CreateOrderItemRequest(BaseModel):
    """创建订单的商品项"""
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(..., ge=1, description="数量（>=1）")


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    user_id: int = Field(..., description="用户ID")
    items: List[CreateOrderItemRequest] = Field(..., min_length=1, description="订单商品列表（至少1项）")


class UpdateOrderStatusRequest(BaseModel):
    """更新订单状态请求"""
    status: str = Field(..., description="新状态: paid/shipped/completed/cancelled")


# ======================== 响应模型 ========================

class OrderListItem(BaseModel):
    """订单列表项（5.1 响应）"""
    id: int
    order_no: str
    user_id: int
    user_name: str = ""
    total_amount: float
    status: str
    item_count: int = 0
    created_at: Optional[datetime] = None


class OrderItemResponse(BaseModel):
    """订单明细项（5.2 响应）"""
    product_id: int
    product_name: str = ""
    price: float
    quantity: int


class OrderDetailResponse(BaseModel):
    """订单详情（5.2 响应）"""
    id: int
    order_no: str
    user_id: int
    user_name: str = ""
    total_amount: float
    status: str
    items: List[OrderItemResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class OrderCreateResponse(BaseModel):
    """创建订单响应（5.3）"""
    id: int
    order_no: str
    total_amount: float
    status: str
    created_at: Optional[datetime] = None


class TrendResponse(BaseModel):
    """销售趋势响应（5.5）"""
    dates: List[str] = Field(default_factory=list)
    sales: List[float] = Field(default_factory=list)
    orders: List[int] = Field(default_factory=list)
