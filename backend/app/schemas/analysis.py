# =============================================================================
# 智能零售用户行为分析系统 - 数据分析模块 Schema 定义
# =============================================================================
from pydantic import BaseModel, Field
from typing import Optional, List


# ======================== 请求模型 ========================

class RecalculateRequest(BaseModel):
    """触发重新计算请求（7.3）"""
    type: str = Field(default="rfm", description="计算类型: rfm / cluster / all")
    clusters: int = Field(default=5, ge=2, le=10, description="聚类数量（仅cluster时有效）")


# ======================== 响应模型 ========================

class RFMDistribution(BaseModel):
    """RFM分群分布"""
    labels: List[str] = Field(default_factory=list)
    values: List[int] = Field(default_factory=list)


class RFMScoreItem(BaseModel):
    """RFM分值项（7.1）"""
    user_id: int
    recency: int
    frequency: int
    monetary: int
    segment: str


class RFMResult(BaseModel):
    """RFM分析响应（7.1）"""
    distribution: RFMDistribution = Field(default_factory=RFMDistribution)
    scores: List[RFMScoreItem] = Field(default_factory=list)


class ClusterPoint(BaseModel):
    """聚类散点（7.2）"""
    user_id: int
    x: float
    y: float
    z: float


class ClusterItem(BaseModel):
    """单个聚类结果（7.2）"""
    label: int
    name: str
    count: int
    center: List[float] = Field(default_factory=list)
    points: List[ClusterPoint] = Field(default_factory=list)


class ClusterResultResponse(BaseModel):
    """聚类分析响应（7.2）"""
    clusters: List[ClusterItem] = Field(default_factory=list)


class AssociationRule(BaseModel):
    """关联规则（7.4）"""
    antecedents: List[str] = Field(default_factory=list)
    consequents: List[str] = Field(default_factory=list)
    antecedent_names: List[str] = Field(default_factory=list)
    consequent_names: List[str] = Field(default_factory=list)
    support: float = 0.0
    confidence: float = 0.0
    lift: float = 0.0


class AssociationResult(BaseModel):
    """关联规则响应（7.4）"""
    rules: List[AssociationRule] = Field(default_factory=list)


class PreferCategory(BaseModel):
    """偏好分类（7.5）"""
    name: str
    count: int


class UserProfileResponse(BaseModel):
    """用户画像响应（7.5）"""
    user_id: int
    nickname: str = ""
    tags: List[str] = Field(default_factory=list)
    prefer_categories: List[PreferCategory] = Field(default_factory=list)
    active_hours: List[int] = Field(default_factory=list)
    avg_order_value: float = 0.0
    total_orders: int = 0
    days_since_last_purchase: int = 0
