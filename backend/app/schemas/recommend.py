# =============================================================================
# 智能零售用户行为分析系统 - 推荐系统模块 Schema 定义
# =============================================================================
from pydantic import BaseModel, Field
from typing import Optional


class HotRecommendItem(BaseModel):
    """热门推荐项（8.1）"""
    product_id: int
    name: str
    price: float
    sales_count: int = 0
    rating: float = 0.0


class AssociationRecommendItem(BaseModel):
    """关联推荐项（8.2）"""
    product_id: int
    name: str
    price: float
    confidence: float = 0.0
    lift: float = 0.0


class PersonalizedRecommendItem(BaseModel):
    """个性化推荐项（8.3）"""
    product_id: int
    name: str
    price: float
    score: float = 0.0
    reason: str = ""
