# =============================================================================
# 智能零售用户行为分析系统 - Redis 缓存工具模块
# =============================================================================
# 功能说明：
#   1. Token 黑名单管理：用户登出时将 Token 加入 Redis 黑名单，防止被恶意复用
#   2. 缓存管理：提供通用的缓存读写删除功能，用于缓存热门商品、推荐结果等
#
# API 接口规范文档要求：
#   - 使用 Redis 存储 Token 黑名单（登出时加入）
#   - Redis 缓存热门商品、推荐结果、驾驶舱核心指标
#
# Token 黑名单工作原理：
#   - 用户登出时，将 Token 存入 Redis，Key 格式为 "blacklist:{token}"
#   - 设置过期时间与 Token 剩余有效期相同（确保 Token 到期后自动清理）
#   - 每次请求认证时检查 Token 是否在黑名单中
# =============================================================================

import redis.asyncio as aioredis    # 异步 Redis 客户端（FastAPI 使用异步）
from app.config import settings     # 应用配置
from typing import Optional, Any     # 类型注解
import json                         # JSON 序列化/反序列化


# =============================================================================
# 创建 Redis 异步连接客户端
# =============================================================================
# 使用 decode_responses=True 自动将 Redis 返回的字节数据解码为字符串
# 注意：此处使用异步 Redis 客户端以支持 FastAPI 的异步处理
redis_client = aioredis.Redis(
    host=settings.REDIS_HOST,          # Redis 主机地址（如 localhost）
    port=settings.REDIS_PORT,          # Redis 端口（如 6379）
    db=settings.REDIS_DB,              # Redis 数据库编号（默认 0）
    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,  # 密码（无密码时传 None）
    decode_responses=True,             # 自动将响应解码为字符串（而非bytes）
)


# ======================== Token 黑名单管理 ========================

async def add_to_blacklist(token: str, expires_in: int = 86400) -> None:
    """
    将 Token 加入 Redis 黑名单（用户登出时调用）
    
    黑名单 Key 格式：blacklist:{token}
    设置过期时间与 Token 有效期相同，到期后 Redis 自动删除，无需手动清理
    
    Args:
        token: 要加入黑名单的 JWT Token 字符串
        expires_in: 过期时间（秒），默认 86400（24小时），
                    应与 JWT Token 的有效期保持一致
    
    示例：
        >>> await add_to_blacklist("eyJhbGciOiJIUzI1NiIs...", 86400)
        # Token 将在 Redis 中存储 24 小时后自动过期删除
    """
    # 使用 setex 设置带有过期时间的键值对
    # Key: blacklist:{token}，Value: "1"（只需标记存在即可）
    await redis_client.setex(
        f"blacklist:{token}",  # Key: 黑名单前缀 + Token
        expires_in,            # 过期时间（秒）
        "1"                    # 值：只需标记存在
    )


async def is_token_blacklisted(token: str) -> bool:
    """
    检查 Token 是否在 Redis 黑名单中（认证时调用）
    
    Args:
        token: 要检查的 JWT Token 字符串
    
    Returns:
        bool: True 表示 Token 已在黑名单中（已登出），False 表示不在黑名单中（合法）
    
    示例：
        >>> await is_token_blacklisted("eyJhbGciOiJIUzI1NiIs...")
        True   # Token 已被加入黑名单，用户已登出
    """
    # 检查 Redis 中是否存在该 Key
    result = await redis_client.exists(f"blacklist:{token}")
    # exists 返回存在的 Key 数量，大于 0 表示在黑名单中
    return result > 0


# ======================== 通用缓存管理 ========================

async def cache_set(key: str, value: Any, expires_in: int = 300) -> None:
    """
    设置缓存（带过期时间）
    
    用于缓存热门商品、推荐结果、驾驶舱指标等数据，减少数据库查询压力
    
    Args:
        key: 缓存键（建议使用有意义的前缀，如 "hot_products"）
        value: 缓存值，可以是字符串、字典、列表等（自动 JSON 序列化）
        expires_in: 过期时间（秒），默认 300 秒（5分钟）
    
    示例：
        >>> await cache_set("hot_products", [{"id": 1, "name": "蓝牙耳机"}], 600)
        >>> await cache_set("dashboard_metrics", {"total_sales": 125000}, 120)
    """
    # 如果值不是字符串，先序列化为 JSON 字符串
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    # 设置带有过期时间的缓存
    await redis_client.setex(key, expires_in, value)


async def cache_get(key: str) -> Optional[str]:
    """
    获取缓存数据
    
    注意：返回的是字符串，如果缓存的是 JSON 数据，需要调用方自行反序列化
    
    Args:
        key: 缓存键
    
    Returns:
        Optional[str]: 缓存值（字符串格式），如果 Key 不存在则返回 None
    
    示例：
        >>> result = await cache_get("hot_products")
        >>> if result:
        >>>     products = json.loads(result)  # JSON 字符串反序列化
    """
    return await redis_client.get(key)


async def cache_delete(key: str) -> None:
    """
    删除缓存数据
    
    当源数据更新时调用此函数清除缓存，确保下次请求获取最新数据
    
    Args:
        key: 缓存键
    
    示例：
        >>> await cache_delete("hot_products")  # 清空热门商品缓存
    """
    await redis_client.delete(key)


async def cache_exists(key: str) -> bool:
    """
    检查缓存是否存在
    
    Args:
        key: 缓存键
    
    Returns:
        bool: True 表示缓存存在，False 表示不存在
    """
    result = await redis_client.exists(key)
    return result > 0
