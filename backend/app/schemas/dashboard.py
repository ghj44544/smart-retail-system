# =============================================================================
# 智能零售用户行为分析系统 - 数据驾驶舱模块 Schema 定义
# =============================================================================
from pydantic import BaseModel, Field
from typing import List


class DashboardMetrics(BaseModel):
    """核心指标（9.1）"""
    total_sales: float = 0.0
    total_orders: int = 0
    avg_order_value: float = 0.0
    total_users: int = 0
    today_sales: float = 0.0
    today_orders: int = 0
    conversion_rate: float = 0.0
    repurchase_rate: float = 0.0


class SalesTrendData(BaseModel):
    """销售趋势（9.2）"""
    dates: List[str] = []
    sales: List[float] = []
    orders: List[int] = []
    users: List[int] = []


class BehaviorTrendData(BaseModel):
    """用户行为趋势（9.3）"""
    dates: List[str] = []
    pv: List[int] = []
    uv: List[int] = []
    new_users: List[int] = []


class ProductRankingItem(BaseModel):
    """商品排行项（9.4）"""
    name: str
    sales: int = 0
    revenue: float = 0.0


class ProductRankingData(BaseModel):
    """商品排行（9.4）"""
    products: List[ProductRankingItem] = []


class UserSegmentItem(BaseModel):
    """用户分群项（9.5）"""
    name: str
    value: int


class UserSegmentsData(BaseModel):
    """用户分群分布（9.5）"""
    segments: List[UserSegmentItem] = []
