# =============================================================================
# 智能零售用户行为分析系统 - 行为数据表 ORM 模型
# =============================================================================
from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from app.models.base import Base


class Behavior(Base):
    """用户行为数据表 ORM 模型"""
    __tablename__ = "behaviors"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="行为ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="商品ID")
    behavior_type = Column(
        SQLEnum("view", "cart", "favorite", "buy", name="behavior_type_enum"),
        nullable=False,
        comment="行为类型: view=浏览, cart=加购, favorite=收藏, buy=购买"
    )
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="行为时间")

    def __repr__(self):
        return f"<Behavior(id={self.id}, type='{self.behavior_type}')>"
