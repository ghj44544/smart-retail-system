# =============================================================================
# 智能零售用户行为分析系统 - 认证模块 Schema 定义
# =============================================================================
# 功能说明：
#   使用 Pydantic v2 定义认证模块的请求参数和响应数据的验证模型
#
# Pydantic 模型的作用：
#   1. 自动验证请求数据格式（类型、必填、长度等）
#   2. 自动生成 Swagger/OpenAPI 文档中的请求/响应示例
#   3. 数据序列化和反序列化（Python 对象 ↔ JSON）
#
# API 接口规范文档要求：
#   - POST /auth/login: 接收 username + password，返回 access_token + user 信息
#   - GET  /auth/me:    返回当前用户信息（id, username, role, nickname, avatar, created_at）
#   - POST /auth/logout: 无请求参数，返回 null
# =============================================================================

from pydantic import BaseModel, Field     # Pydantic 基类和字段描述
from typing import Optional                # 可选字段类型
from datetime import datetime              # 日期时间类型


# ======================== 请求模型（前端 → 后端） ========================

class LoginRequest(BaseModel):
    """
    用户登录请求参数模型
    
    对应 API 接口：POST /auth/login
    
    请求 JSON 格式：
        {
            "username": "string",   // 用户名（必填）
            "password": "string"    // 密码（必填）
        }
    
    验证规则：
        - username: 字符串，不能为空
        - password: 字符串，不能为空
    """
    # 用户名：必填字符串
    # Field 的 description 会显示在 Swagger 文档中
    username: str = Field(
        ...,
        min_length=1,
        description="用户名",
        examples=["admin"]
    )
    # 密码：必填字符串（前端传输时是明文，后端加密后与数据库对比）
    password: str = Field(
        ...,
        min_length=1,
        description="密码",
        examples=["admin123"]
    )


# ======================== 响应模型（后端 → 前端） ========================

class UserInfo(BaseModel):
    """
    用户基本信息响应模型（登录成功后返回的用户简要信息）
    
    对应 API 接口：POST /auth/login 响应中的 user 字段
    
    响应 JSON 格式：
        {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "nickname": "系统管理员"
        }
    
    注意：此模型不包含密码、邮箱等敏感/详细字段，
          仅返回登录后前端需要的简要信息
    """
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="角色：admin 或 user")
    nickname: str = Field(..., description="昵称")


class LoginResponseData(BaseModel):
    """
    登录成功响应数据模型
    
    对应 API 接口：POST /auth/login 响应中的 data 字段
    
    响应 JSON 格式：
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 86400,
            "user": {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "nickname": "系统管理员"
            }
        }
    """
    # JWT Token 字符串
    access_token: str = Field(
        ...,
        description="JWT 访问令牌，后续请求在 Authorization 头中携带"
    )
    # Token 类型（固定为 "bearer"）
    token_type: str = Field(
        default="bearer",
        description="Token 类型，固定为 bearer"
    )
    # Token 过期时间（秒），86400 = 24小时
    expires_in: int = Field(
        ...,
        description="Token 有效期（秒），86400 表示 24 小时"
    )
    # 登录用户的基本信息
    user: UserInfo = Field(
        ...,
        description="当前登录用户的基本信息"
    )


class UserMeResponse(BaseModel):
    """
    获取当前用户信息响应模型
    
    对应 API 接口：GET /auth/me 响应中的 data 字段
    
    响应 JSON 格式：
        {
            "id": 1,
            "username": "admin",
            "role": "admin",
            "nickname": "系统管理员",
            "avatar": "",
            "created_at": "2026-01-01T00:00:00"
        }
    
    注意：返回比 LoginResponse 更多的用户详情字段
    """
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="角色")
    nickname: str = Field(..., description="昵称")
    avatar: Optional[str] = Field(None, description="头像URL")
    email: Optional[str] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    created_at: Optional[datetime] = Field(None, description="创建时间")
