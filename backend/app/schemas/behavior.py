# =============================================================================
# 智能零售用户行为分析系统 - 行为数据模块 Schema 定义
# =============================================================================
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ======================== 响应模型 ========================

class BehaviorItem(BaseModel):
    """行为记录列表项（6.2 响应）"""
    id: int
    user_id: int
    product_id: int
    behavior_type: str
    created_at: Optional[datetime] = None


class ImportResult(BaseModel):
    """导入结果（6.1 响应）"""
    imported_count: int = 0
    skipped_count: int = 0


class FunnelStep(BaseModel):
    """转化漏斗步骤（6.3 响应）"""
    name: str
    count: int
    rate: float


class FunnelData(BaseModel):
    """转化漏斗数据（6.3 响应）"""
    steps: List[FunnelStep] = []


class TrendData(BaseModel):
    """行为趋势数据（6.4 响应）"""
    dates: List[str] = []
    pv: List[int] = []
    uv: List[int] = []
    view_count: List[int] = []
    cart_count: List[int] = []
    buy_count: List[int] = []
