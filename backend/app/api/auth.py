# =============================================================================
# 智能零售用户行为分析系统 - 认证模块 API 路由
# =============================================================================
# 模块功能：
#   提供用户认证相关的 RESTful API 接口，包括：
#     1. POST /auth/login  - 用户登录，获取 JWT Token
#     2. GET  /auth/me     - 获取当前登录用户信息
#     3. POST /auth/logout - 用户登出，Token 加入 Redis 黑名单
#
# 对应 API 接口规范文档：第二章「认证接口」
# Base URL: http://localhost:8000/api/v1
# =============================================================================

from fastapi import APIRouter, Depends, HTTPException, status, Request  # FastAPI 路由和依赖注入
from sqlalchemy.orm import Session                              # SQLAlchemy 数据库会话
from passlib.context import CryptContext                        # 密码哈希（bcrypt）
from datetime import timedelta                                  # 时间增量

# 自定义模块导入
from app.schemas.auth import LoginRequest, LoginResponseData, UserInfo, UserMeResponse  # Pydantic 数据模型
from app.models.user import User                                # 用户 ORM 模型
from app.models.base import get_db                              # 数据库会话依赖注入
from app.utils.response_utils import success_response, error_response  # 统一响应格式
from app.utils.jwt_utils import create_access_token, get_current_user, security  # JWT 工具 + HTTPBearer 实例
from app.utils.redis_utils import add_to_blacklist              # Redis 黑名单工具
from app.config import settings                                 # 应用配置
from typing import Dict                                         # 类型注解


# =============================================================================
# 创建路由实例
# =============================================================================
# prefix="/auth": 该路由下所有接口都以 /auth 开头
# tags=["认证"]: 在 Swagger 文档中归类到"认证"分组
router = APIRouter(
    prefix="/auth",     # 路由前缀
    tags=["认证"]       # Swagger 文档分组标签
)


# =============================================================================
# 密码加密上下文
# =============================================================================
# CryptContext 是 passlib 库的核心类，用于管理密码哈希方案
# 
# schemes=["bcrypt"]: 使用 bcrypt 算法加密密码
#   - bcrypt 是业界标准的密码哈希算法，具有以下特点：
#     1. 内置盐值（Salt）：每次加密自动生成随机盐值，相同密码产生不同哈希
#     2. 计算成本可调：通过 rounds 参数控制加密复杂度（默认 12）
#     3. 抗彩虹表攻击：盐值使预计算的彩虹表失效
#
# deprecated="auto": 自动标记过时的哈希算法（当有更安全的算法可用时）
# =============================================================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ======================== 辅助函数 ========================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与加密密码匹配
    
    使用 bcrypt 的 verify 方法：
    1. 从 hashed_password 中提取盐值
    2. 使用相同的盐值加密 plain_password
    3. 比较两次加密结果是否一致
    
    Args:
        plain_password: 用户输入的明文密码（从请求中获取）
        hashed_password: 数据库中存储的加密密码（bcrypt 哈希值）
    
    Returns:
        bool: True 表示密码匹配，False 表示密码错误
    
    示例：
        >>> verify_password("admin123", "$2b$12$LJ3m4ys3GAx2k1Vz6K0z9...")
        True
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    将明文密码加密为 bcrypt 哈希值
    
    使用 bcrypt 算法加密，自动生成随机盐值
    
    Args:
        password: 明文密码
    
    Returns:
        str: bcrypt 加密后的哈希字符串（60 字符）
    
    示例：
        >>> hash_password("admin123")
        "$2b$12$LJ3m4ys3GAx2k1Vz6K0z9eXqY5wF8jH7rT2vB1nM4pQ6sU8tA0..."
    
    安全提示：
        绝不要在日志中打印明文密码或哈希值！
    """
    return pwd_context.hash(password)


# ======================== 接口 1：用户登录 ========================

@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,              # 请求体：username + password（Pydantic 自动验证）
    db: Session = Depends(get_db)       # 数据库会话（FastAPI 依赖注入）
) -> Dict:
    """
    用户登录接口
    
    对应 API 接口规范文档：2.1 用户登录
    
    功能说明：
        1. 接收用户名和密码
        2. 在数据库中查找用户
        3. 验证密码是否正确
        4. 生成 JWT Token 并返回用户信息
    
    请求格式（POST /auth/login）：
        {
            "username": "admin",
            "password": "admin123"
        }
    
    成功响应格式：
        {
            "code": 200,
            "message": "登录成功",
            "data": {
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
        }
    
    错误响应：
        - 401: 用户名或密码错误
    """
    
    # 步骤1：在数据库中查找用户
    # filter 相当于 SQL 的 WHERE 子句
    # first() 返回第一条匹配记录，如果不存在则返回 None
    user = db.query(User).filter(User.username == request.username).first()
    
    # 步骤2：验证用户是否存在且密码是否正确
    # 注意：使用统一错误消息防止用户名枚举攻击
    # （不区分"用户不存在"和"密码错误"，统一返回"用户名或密码错误"）
    if not user or not verify_password(request.password, user.password):
        # 密码验证失败，返回 401 未认证错误
        # 使用 error_response 统一格式
        return error_response(
            code=status.HTTP_401_UNAUTHORIZED,   # 401 状态码
            message="用户名或密码错误"               # 错误消息
        )
    
    # 步骤3：创建 JWT Token
    # Token 的 Payload 中包含用户 ID 和角色，用于后续请求的身份识别和权限控制
    access_token = create_access_token(
        data={
            "user_id": user.id,        # 用户 ID
            "role": user.role           # 用户角色（admin 或 user）
        }
    )
    
    # 步骤4：计算 Token 过期时间（秒）
    # ACCESS_TOKEN_EXPIRE_HOURS 默认 24 小时
    # timedelta(hours=24).total_seconds() = 86400
    expires_in = int(timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS).total_seconds())
    
    # 步骤5：构建登录响应数据
    login_data = LoginResponseData(
        access_token=access_token,                      # JWT Token
        token_type="bearer",                            # Token 类型
        expires_in=expires_in,                          # 过期时间（秒）
        user=UserInfo(                                  # 用户基本信息
            id=user.id,                                 # 用户 ID
            username=str(user.username),                # 用户名
            role=str(user.role),                         # 角色
            nickname=str(user.nickname or "")             # 昵称
        )
    )
    
    # 步骤6：返回成功响应
    # 使用 model_dump() 将 Pydantic 模型转为字典
    return success_response(
        data=login_data.model_dump(),   # 登录数据
        message="登录成功"               # 自定义成功消息
    )


# ======================== 接口 2：获取当前用户信息 ========================

@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user: Dict = Depends(get_current_user),  # JWT 认证依赖注入
    db: Session = Depends(get_db)                    # 数据库会话
) -> Dict:
    """
    获取当前登录用户信息
    
    对应 API 接口规范文档：2.2 获取当前用户信息
    
    功能说明：
        1. 从 JWT Token 中提取用户 ID
        2. 从数据库查询用户详细信息
        3. 返回用户信息（不含密码）
    
    请求头：
        Authorization: Bearer <access_token>
    
    成功响应格式：
        {
            "code": 200,
            "message": "success",
            "data": {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "nickname": "系统管理员",
                "avatar": "",
                "created_at": "2026-01-01T00:00:00"
            }
        }
    
    错误响应：
        - 401: Token 无效或已过期（由 get_current_user 依赖自动返回）
        - 404: 用户不存在
    """
    
    # 步骤1：从 Token 中获取用户 ID
    # current_user 由 get_current_user 依赖注入提供
    # 如果 Token 无效或过期，get_current_user 会直接抛出 401 错误，不会执行到这里
    user_id = current_user["user_id"]
    
    # 步骤2：从数据库查询用户信息
    user = db.query(User).filter(User.id == user_id).first()
    
    # 步骤3：验证用户是否存在
    if not user:
        return error_response(
            code=status.HTTP_404_NOT_FOUND,  # 404 资源不存在
            message="用户不存在"
        )
    
    # 步骤4：构建用户信息响应（使用 Schema 管理字段和类型）
    user_data = UserMeResponse(
        id=user.id,
        username=str(user.username),
        role=str(user.role),
        nickname=str(user.nickname or ""),
        avatar=user.avatar,
        email=user.email,
        phone=user.phone,
        created_at=user.created_at
    )
    
    # 步骤5：返回成功响应
    return success_response(data=user_data.model_dump())


# ======================== 接口 3：用户登出 ========================

@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,                                           # FastAPI Request 对象，用于获取原始请求头
    current_user: Dict = Depends(get_current_user)              # JWT 认证依赖注入
) -> Dict:
    """
    用户登出接口
    
    对应 API 接口规范文档：2.3 用户登出
    
    功能说明：
        1. 从请求头中提取当前 JWT Token
        2. 将 Token 加入 Redis 黑名单
        3. Token 被加入黑名单后，后续使用该 Token 的请求将被拒绝（401）
    
    请求头：
        Authorization: Bearer <access_token>
    
    成功响应格式：
        {
            "code": 200,
            "message": "登出成功",
            "data": null
        }
    
    工作原理：
        - 从 Authorization 头中提取 Bearer Token
        - 将 Token 存入 Redis，Key 格式：blacklist:{token}
        - 设置过期时间，与 Token 剩余有效时间相同
        - Token 自然过期后，Redis 会自动删除对应的黑名单条目
        - 后续请求在 get_current_user 中检查黑名单，发现 Token 被标记则返回 401
    """
    
    # 步骤1：从请求头中提取 Token
    # Authorization 头的格式为 "Bearer eyJhbGciOiJIUzI1NiIs..."
    auth_header = request.headers.get("Authorization", "")
    
    # 步骤2：解析 Bearer Token
    # 去除 "Bearer " 前缀，获取纯 Token 字符串
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]  # "Bearer " 长度为 7，截取之后的 Token 部分
    else:
        # 如果 Authorization 头格式不正确，仍返回成功
        # （这种情况不应该发生，因为 get_current_user 依赖已通过验证）
        token = ""
    
    # 步骤3：将 Token 加入 Redis 黑名单
    if token:
        # 计算 Token 剩余有效时间（秒）
        # 使用配置的默认过期时间作为黑名单过期时间
        # 这样能确保黑名单条目在 Token 自然过期时一起被清理
        expires_in = int(timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS).total_seconds())
        
        # 加入 Redis 黑名单
        # blacklist:{token} -> "1"，过期时间为 86400 秒（24小时）
        await add_to_blacklist(token, expires_in)
    
    # 步骤4：返回登出成功响应
    return success_response(
        data=None,            # 登出不需要返回数据
        message="登出成功"
    )
