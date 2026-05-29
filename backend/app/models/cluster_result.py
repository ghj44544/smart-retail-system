# =============================================================================
# 智能零售用户行为分析系统 - 聚类结果表 ORM 模型
# =============================================================================
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class ClusterResult(Base):
    """K-Means聚类结果表"""
    __tablename__ = "cluster_results"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="用户ID")
    cluster_label = Column(Integer, comment="聚类标签（0-4）")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ClusterResult(user_id={self.user_id}, label={self.cluster_label})>"
