# =============================================================================
# 智能零售用户行为分析系统 - 商品表 ORM 模型
# =============================================================================
# 对应数据库表：products（商品表）
#
# 表结构（来自 API 接口规范文档和计划文档）：
#   id           INT             自增主键
#   product_no   VARCHAR(50)     商品编号（唯一）
#   name         VARCHAR(200)    商品名称
#   description  TEXT            商品描述
#   category_id  INT             分类ID（外键）
#   price        DECIMAL(10,2)   价格
#   stock        INT             库存
#   status       ENUM            状态（on=上架 / off=下架）
#   sales_count  INT             销量
#   rating       DECIMAL(2,1)    评分
#   created_at   DATETIME        创建时间
#   deleted_at   DATETIME        软删除时间
# =============================================================================

from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL
from sqlalchemy import ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class Product(Base):
    """
    商品表 ORM 模型
    
    映射到数据库中的 products 表
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="商品ID")
    product_no = Column(String(50), unique=True, nullable=False, comment="商品编号")
    name = Column(String(200), nullable=False, comment="商品名称")
    description = Column(Text, comment="商品描述")
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        comment="分类ID"
    )
    price = Column(DECIMAL(10, 2), nullable=False, comment="价格")
    stock = Column(Integer, default=0, comment="库存")
    status = Column(
        SQLEnum("on", "off", name="product_status_enum"),
        default="on",
        nullable=False,
        comment="状态：on=上架, off=下架"
    )
    sales_count = Column(Integer, default=0, comment="销量")
    rating = Column(DECIMAL(2, 1), default=0, comment="评分（0-5）")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    deleted_at = Column(DateTime, nullable=True, default=None, comment="软删除时间")

    # 关联关系：商品所属分类
    category = relationship("Category", backref="products")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"
