# =============================================================================
# 智能零售用户行为分析系统 - 商品管理模块 Schema 定义
# =============================================================================
# API 接口规范文档对应：第四章「商品管理接口」
#   4.1 GET    /products            - 获取商品列表（分页、筛选）
#   4.2 GET    /products/{id}       - 获取商品详情
#   4.3 POST   /products            - 创建商品
#   4.4 PUT    /products/{id}       - 更新商品
#   4.5 DELETE /products/{id}       - 删除商品（软删除）
#   4.6 GET    /categories          - 获取分类列表
#   4.7 GET    /products/hot        - 获取热门商品排行（Redis缓存）
# =============================================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ======================== 请求模型 ========================

class CreateProductRequest(BaseModel):
    """创建商品请求（POST /products）"""
    product_no: str = Field(..., max_length=50, description="商品编号（唯一）")
    name: str = Field(..., max_length=200, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    price: float = Field(..., gt=0, description="价格（必须大于0）")
    stock: int = Field(default=0, ge=0, description="库存（必须>=0）")
    status: str = Field(default="on", description="状态：on=上架, off=下架")


class UpdateProductRequest(BaseModel):
    """更新商品请求（PUT /products/{id}）- 所有字段可选"""
    name: Optional[str] = Field(None, max_length=200, description="商品名称")
    description: Optional[str] = Field(None, description="商品描述")
    category_id: Optional[int] = Field(None, description="分类ID")
    price: Optional[float] = Field(None, gt=0, description="价格")
    stock: Optional[int] = Field(None, ge=0, description="库存")
    status: Optional[str] = Field(None, description="状态：on/off")
    product_no: Optional[str] = Field(None, max_length=50, description="商品编号")


# ======================== 响应模型 ========================

class ProductListItem(BaseModel):
    """商品列表项（GET /products 响应）"""
    id: int
    product_no: str
    name: str
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    price: float
    stock: int
    status: str
    sales_count: int
    rating: float
    created_at: Optional[datetime] = None


class ProductDetailResponse(BaseModel):
    """商品详情（GET /products/{id} 响应）"""
    id: int
    product_no: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    price: float
    stock: int
    status: str
    sales_count: int
    rating: float
    related_products: List[int] = Field(default_factory=list, description="关联商品ID列表")
    created_at: Optional[datetime] = None


class ProductCreateResponse(BaseModel):
    """创建商品响应（POST /products）"""
    id: int
    product_no: str
    name: str
    category_id: Optional[int] = None
    price: float
    status: str
    created_at: Optional[datetime] = None


class CategoryResponse(BaseModel):
    """分类项（GET /categories 响应）"""
    id: int
    name: str
    parent_id: Optional[int] = None


class HotProductItem(BaseModel):
    """热门商品排行项（GET /products/hot 响应）"""
    product_id: int
    name: str
    sales_count: int
    rating: float
    price: float
