# =============================================================================
# 智能零售用户行为分析系统 - RFM分析结果表 ORM 模型
# =============================================================================
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class RfmScore(Base):
    """RFM分析结果表 - 按用户ID为主键，存储R/F/M分值和分群标签"""
    __tablename__ = "rfm_scores"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="用户ID")
    recency = Column(Integer, comment="最近购买分值（1-5）")
    frequency = Column(Integer, comment="购买频率分值（1-5）")
    monetary = Column(Integer, comment="消费金额分值（1-5）")
    segment = Column(String(50), comment="用户分群标签")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<RfmScore(user_id={self.user_id}, segment='{self.segment}')>"
