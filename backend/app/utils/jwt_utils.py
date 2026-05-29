# =============================================================================
# 智能零售用户行为分析系统 - JWT 认证工具模块
# =============================================================================
# 功能说明：
#   1. JWT Token 的创建（用户登录成功后生成 Token）
#   2. JWT Token 的解码（提取 Token 中的用户信息）
#   3. 获取当前登录用户（FastAPI 依赖注入，用于路由保护）
#   4. Token 黑名单验证（检查 Token 是否已被登出）
#
# API 接口规范文档要求：
#   - 登录后获取 access_token，后续请求在 Header 中携带：
#     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
#   - Token 有效期：24 小时
#   - 使用 Redis 存储 Token 黑名单（登出时加入）
#
# JWT Token 结构：
#   Header:  {"alg": "HS256", "typ": "JWT"}
#   Payload: {"user_id": 1, "role": "admin", "exp": 1716912000}
#   Signature: 使用 JWT_SECRET_KEY 对 Header + Payload 的签名
# =============================================================================

from datetime import datetime, timedelta          # 日期时间处理
from jose import JWTError, jwt                     # JWT 创建和验证
from fastapi import HTTPException, status          # FastAPI HTTP 异常和状态码
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials  # HTTP Bearer 认证方案
from fastapi import Depends                        # FastAPI 依赖注入
from typing import Optional, Dict                  # 类型注解
from app.config import settings                    # 应用配置


# =============================================================================
# 创建 HTTP Bearer 认证方案实例
# =============================================================================
# HTTPBearer 是 FastAPI 提供的安全方案，用于从请求头提取 Bearer Token
# 它会自动从 Authorization: Bearer <token> 头中提取 Token
# 
# auto_error=False: 当请求没有提供 Token 时，不自动报错
# 手动在 get_current_user 中返回 401 错误（与 API 文档一致）
# 注意：auto_error=True 时 FastAPI 默认返回 403，不符合 API 文档的 401 要求
security = HTTPBearer(auto_error=False)


# ======================== Token 创建与解码 ========================

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌（Access Token）
    
    Token 中包含的数据（Payload）：
        - user_id: 用户 ID（用于后续识别用户）
        - role: 用户角色（admin/user，用于权限控制）
        - exp: Token 过期时间戳（Unix 时间戳，秒）
    
    Args:
        data: 要编码到 Token 中的数据字典
              必须包含 "user_id" 和 "role" 字段
        expires_delta: 自定义过期时间增量，如果为 None 则使用配置的默认值（24小时）
    
    Returns:
        str: 编码后的 JWT Token 字符串（三段式：Header.Payload.Signature）
    
    示例：
        >>> create_access_token({"user_id": 1, "role": "admin"})
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ..."
    """
    # 复制数据字典，避免修改原始数据
    to_encode = data.copy()
    
    # 计算 Token 过期时间
    if expires_delta:
        # 使用自定义过期时间
        expire = datetime.utcnow() + expires_delta
    else:
        # 使用配置的默认过期时间（默认 24 小时）
        expire = datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    
    # 将过期时间添加到 Payload 中（"exp" 是 JWT 标准声明，表示过期时间）
    to_encode.update({"exp": expire})
    
    # 使用 JWT 密钥和算法签名并编码 Token
    encoded_jwt = jwt.encode(
        to_encode,                    # Payload 数据
        settings.JWT_SECRET_KEY,      # 签名密钥
        algorithm=settings.JWT_ALGORITHM  # 签名算法（HS256）
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict:
    """
    解码 JWT Token，提取其中的 Payload 数据
    
    验证过程：
    1. 使用相同的密钥和算法验证签名（确保 Token 未被篡改）
    2. 检查 "exp" 过期时间（确保 Token 未过期）
    3. 返回 Payload 中的数据
    
    Args:
        token: JWT Token 字符串
    
    Returns:
        Dict: Token 的 Payload 数据字典
    
    Raises:
        JWTError: Token 签名无效、已过期或格式错误时抛出
    
    示例：
        >>> payload = decode_access_token("eyJhbGciOiJIUzI1NiIs...")
        >>> print(payload)
        {"user_id": 1, "role": "admin", "exp": 1716912000}
    """
    try:
        # 解码并验证 Token
        payload = jwt.decode(
            token,                       # Token 字符串
            settings.JWT_SECRET_KEY,     # 签名密钥（必须与编码时相同）
            algorithms=[settings.JWT_ALGORITHM]  # 算法列表
        )
        return payload
    except JWTError as e:
        # JWTError 包含所有 JWT 相关错误：
        # - ExpiredSignatureError: Token 已过期
        # - JWTClaimsError: Claims 验证失败
        # - JWTError: 签名验证失败或格式错误
        raise JWTError(f"Token 解码失败: {str(e)}")


# ======================== 依赖注入：获取当前用户 ========================

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict:
    """
    获取当前登录用户信息（FastAPI 依赖注入）
    
    使用方式：
        在路由函数中注入此依赖，FastAPI 会自动：
        1. 从 Authorization: Bearer <token> 头中提取 Token
        2. 解码并验证 Token
        3. 检查 Token 是否在黑名单中
        4. 返回用户信息 {user_id, role}
    
    Args:
        credentials: HTTP 认证凭证（由 HTTPBearer 自动解析），无Token时为None
    
    Returns:
        Dict: 当前用户信息
            {
                "user_id": int,   # 用户 ID
                "role": str       # 用户角色（admin/user）
            }
    
    Raises:
        HTTPException(401): 未提供Token、Token无效、过期或在黑名单中
    
    使用示例（在路由函数中）：
        @router.get("/auth/me")
        async def get_me(current_user: dict = Depends(get_current_user)):
            # current_user 包含 {"user_id": 1, "role": "admin"}
            user_id = current_user["user_id"]
            ...
    """
    # 步骤0：检查是否提供了 Token（auto_error=False 时 credentials 可能为 None）
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401 未认证
            detail="未提供认证Token，请先登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 从 HTTP 凭证中获取 Token 字符串
    token = credentials.credentials
    
    try:
        # 步骤1：解码并验证 Token（检查签名和过期时间）
        payload = decode_access_token(token)
        
        # 步骤2：从 Payload 中提取用户 ID
        user_id: int = payload.get("user_id")
        if user_id is None:
            # Token 中没有 user_id，视为无效 Token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,  # 401 未认证
                detail="无效的Token：缺少用户标识",
                headers={"WWW-Authenticate": "Bearer"},    # 提示客户端应使用 Bearer 认证
            )
        
        # 步骤3：检查 Token 是否在 Redis 黑名单中（用户是否已登出）
        # 延迟导入避免循环依赖
        from app.utils.redis_utils import is_token_blacklisted
        if await is_token_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,  # 401 未认证
                detail="Token已失效，请重新登录",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 步骤4：返回用户信息（供路由函数使用）
        return {
            "user_id": user_id,
            "role": payload.get("role", "user")  # 默认角色为 user
        }
        
    except JWTError:
        # Token 解码失败（签名无效或已过期）
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401 未认证
            detail="Token已过期或无效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )
