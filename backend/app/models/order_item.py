# =============================================================================
# 智能零售用户行为分析系统 - 订单明细表 ORM 模型
# =============================================================================
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class OrderItem(Base):
    """订单明细表 ORM 模型"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="明细ID")
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, comment="订单ID")
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="商品ID")
    price = Column(DECIMAL(10, 2), nullable=False, comment="单价")
    quantity = Column(Integer, nullable=False, comment="数量")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    # 关联商品信息
    product = relationship("Product", backref="order_items", lazy="joined")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, quantity={self.quantity})>"
