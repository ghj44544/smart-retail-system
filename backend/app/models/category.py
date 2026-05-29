# =============================================================================
# 智能零售用户行为分析系统 - 商品分类表 ORM 模型
# =============================================================================
# 对应数据库表：categories（商品分类表）
#
# 表结构（来自 API 接口规范文档和计划文档）：
#   id         INT           自增主键
#   name       VARCHAR(100)   分类名称
#   parent_id  INT            父分类ID（NULL表示顶级分类）
#   created_at DATETIME       创建时间
# =============================================================================

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey  # SQLAlchemy字段
from sqlalchemy.orm import relationship                               # ORM关系映射
from sqlalchemy.sql import func                                      # SQL函数
from app.models.base import Base                                     # ORM基类


class Category(Base):
    """
    商品分类表 ORM 模型
    
    支持树形分类结构（通过 parent_id 自引用实现父子层级）
    例如：服装(顶级) → 男装(子分类) → T恤(孙子分类)
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="分类ID")
    name = Column(String(100), nullable=False, comment="分类名称")
    parent_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="SET NULL"),  # 父分类删除时，子分类的parent_id设为NULL
        nullable=True,
        comment="父分类ID（NULL=顶级分类）"
    )
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 自引用关系：获取子分类列表
    children = relationship("Category", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"
