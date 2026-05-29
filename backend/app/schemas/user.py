# =============================================================================
# 智能零售用户行为分析系统 - 用户管理模块 Schema 定义
# =============================================================================
# 功能说明：
#   使用 Pydantic v2 定义用户管理模块的请求参数和响应数据的验证模型
#
# API 接口规范文档对应：第三章「用户管理接口」
#   3.1 GET   /users          - 获取用户列表（分页、搜索、筛选）
#   3.2 GET   /users/{id}     - 获取用户详情
#   3.3 POST  /users          - 创建用户
#   3.4 PUT   /users/{id}     - 更新用户信息
#   3.5 DELETE /users/{id}    - 删除用户（软删除）
# =============================================================================

from pydantic import BaseModel, Field                    # Pydantic 基类和字段描述
from typing import Optional, Dict                         # 可选字段和字典类型
from datetime import datetime                             # 日期时间类型


# ======================== 请求模型（前端 → 后端） ========================

class CreateUserRequest(BaseModel):
    """
    创建用户请求参数模型
    
    对应 API 接口：POST /users（3.3 创建用户）
    
    请求 JSON 格式：
        {
            "username": "user002",       // 用户名（必填）
            "nickname": "李四",           // 昵称（必填）
            "email": "lisi@example.com", // 邮箱（必填）
            "phone": "13900001111",      // 手机号（必填）
            "password": "123456",        // 密码（必填）
            "role": "user"               // 角色（选填，默认 user）
        }
    """
    # 用户名：必填，全局唯一
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    # 昵称：必填
    nickname: str = Field(..., min_length=1, max_length=100, description="昵称")
    # 邮箱：必填
    email: str = Field(..., max_length=100, description="邮箱")
    # 手机号：必填
    phone: str = Field(..., max_length=20, description="手机号")
    # 密码：必填（存储时使用 bcrypt 加密）
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    # 角色：选填，默认 user
    role: str = Field(default="user", description="角色：admin 或 user")


class UpdateUserRequest(BaseModel):
    """
    更新用户信息请求参数模型
    
    对应 API 接口：PUT /users/{user_id}（3.4 更新用户）
    
    注意：所有字段都是可选的，只更新传入的字段
    密码字段可单独提供，如果不提供则不修改密码
    """
    # 昵称：可选更新
    nickname: Optional[str] = Field(None, max_length=100, description="昵称")
    # 邮箱：可选更新
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    # 手机号：可选更新
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    # 密码：可选更新（如果提供则会重新加密）
    password: Optional[str] = Field(None, min_length=6, max_length=128, description="新密码")
    # 角色：可选更新
    role: Optional[str] = Field(None, description="角色：admin 或 user")
    # 头像：可选更新
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")


# ======================== 响应模型（后端 → 前端） ========================

class UserListItem(BaseModel):
    """
    用户列表项响应模型
    
    对应 API 接口：GET /users 响应中 items 数组的每个元素（3.1 获取用户列表）
    
    响应 JSON 格式：
        {
            "id": 1,
            "username": "user001",
            "nickname": "张三",
            "email": "zhangsan@example.com",
            "phone": "138****1234",
            "role": "user",
            "total_consumption": 1250.50,
            "order_count": 8,
            "last_login": "2026-05-20T10:30:00",
            "created_at": "2025-01-15T08:00:00"
        }
    """
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: str = Field(..., description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    role: str = Field(..., description="角色")
    # 消费总额（来自订单表统计，订单模块开发后填充）
    total_consumption: float = Field(default=0.0, description="消费总额")
    # 订单数量（来自订单表统计，订单模块开发后填充）
    order_count: int = Field(default=0, description="订单数量")
    # 最后登录时间
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    # 创建时间
    created_at: Optional[datetime] = Field(None, description="创建时间")


class RFMScoreInfo(BaseModel):
    """
    RFM 分值信息响应模型
    
    对应 API 接口：GET /users/{user_id} 响应中的 rfm_score 字段（3.2 获取用户详情）
    
    注意：RFM 分析模块开发后，此数据从 rfm_scores 表实时计算
    当前返回 null 占位
    
    响应 JSON 格式：
        {
            "recency": 2,     // 最近购买天数分值（1-5分）
            "frequency": 3,   // 购买频率分值（1-5分）
            "monetary": 4     // 消费金额分值（1-5分）
        }
    """
    recency: int = Field(..., description="最近购买分值（1-5）")
    frequency: int = Field(..., description="购买频率分值（1-5）")
    monetary: int = Field(..., description="消费金额分值（1-5）")


class UserDetailResponse(BaseModel):
    """
    用户详情响应模型
    
    对应 API 接口：GET /users/{user_id} 响应中的 data 字段（3.2 获取用户详情）
    
    响应 JSON 格式：
        {
            "id": 1,
            "username": "user001",
            "nickname": "张三",
            "email": "zhangsan@example.com",
            "phone": "138****1234",
            "role": "user",
            "total_consumption": 1250.50,
            "order_count": 8,
            "avg_order_value": 156.31,
            "last_purchase": "2026-05-18T14:20:00",
            "rfm_score": {"recency": 2, "frequency": 3, "monetary": 4},
            "cluster_label": 2,
            "created_at": "2025-01-15T08:00:00"
        }
    
    注意：
        - total_consumption, order_count, avg_order_value, last_purchase 
          来自订单表统计，当前订单模块未开发，返回默认值 0/null
        - rfm_score 来自 RFM 分析结果表，当前返回 null
        - cluster_label 来自聚类结果表，当前返回 null
    """
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: str = Field(..., description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    role: str = Field(..., description="角色")
    # 消费总额（订单模块开发后填充）
    total_consumption: float = Field(default=0.0, description="消费总额")
    # 订单数量（订单模块开发后填充）
    order_count: int = Field(default=0, description="订单数量")
    # 平均订单金额 = total_consumption / order_count（订单模块开发后填充）
    avg_order_value: float = Field(default=0.0, description="平均订单金额")
    # 最近购买时间（订单模块开发后填充）
    last_purchase: Optional[datetime] = Field(None, description="最近购买时间")
    # RFM 分值（RFM分析模块开发后填充）
    rfm_score: Optional[RFMScoreInfo] = Field(None, description="RFM分值")
    # 聚类标签（聚类分析模块开发后填充）
    cluster_label: Optional[int] = Field(None, description="聚类标签（0-4）")
    # 最后登录时间
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    # 创建时间
    created_at: Optional[datetime] = Field(None, description="创建时间")
    # 头像
    avatar: Optional[str] = Field(None, description="头像URL")


class UserCreateResponse(BaseModel):
    """
    创建用户成功响应模型
    
    对应 API 接口：POST /users 响应中的 data 字段（3.3 创建用户）
    
    返回新创建用户的基本信息（不含密码）
    """
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    nickname: str = Field(..., description="昵称")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    role: str = Field(..., description="角色")
    created_at: Optional[datetime] = Field(None, description="创建时间")
