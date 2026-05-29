# =============================================================================
# 智能零售用户行为分析系统 - 订单表 ORM 模型
# =============================================================================
from sqlalchemy import Column, Integer, String, DateTime, DECIMAL, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Order(Base):
    """订单表 ORM 模型"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="订单ID")
    order_no = Column(String(50), unique=True, nullable=False, comment="订单编号")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    total_amount = Column(DECIMAL(10, 2), nullable=False, comment="总金额")
    status = Column(
        SQLEnum("pending", "paid", "shipped", "completed", "cancelled", name="order_status_enum"),
        default="pending", nullable=False,
        comment="订单状态: pending=待支付, paid=已支付, shipped=已发货, completed=已完成, cancelled=已取消"
    )
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    paid_at = Column(DateTime, nullable=True, comment="支付时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    # 关联关系
    items = relationship("OrderItem", backref="order", lazy="joined")
    user = relationship("User", backref="orders", lazy="joined")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}')>"
