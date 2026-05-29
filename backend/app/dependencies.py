# =============================================================================
# 智能零售用户行为分析系统 - 依赖注入模块
# =============================================================================
# 功能说明：
#   1. 分页参数依赖注入：从查询参数中提取分页信息
#   2. 权限控制依赖注入：检查用户角色
#
# 使用方式：
#   在路由函数中通过 Depends 注入：
#       @router.get("/users")
#       async def get_users(pagination: dict = Depends(get_pagination)):
#           page = pagination["page"]
#           ...
# =============================================================================

from fastapi import Query, Depends, HTTPException, status  # FastAPI 查询参数、依赖注入、异常
from typing import Optional, Dict                          # 类型注解


# =============================================================================
# 分页参数依赖注入
# =============================================================================

async def get_pagination(
    page: int = Query(default=1, ge=1, description="页码，从1开始"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量，最大100")
) -> Dict:
    """
    分页参数依赖注入
    
    从请求的查询参数中提取分页信息，提供默认值和范围限制
    
    对应 API 接口规范文档中所有分页接口的通用查询参数：
        ?page=1&page_size=10
    
    Args:
        page: 页码，默认 1，最小值为 1
        page_size: 每页数量，默认 10，范围 1-100
    
    Returns:
        Dict: {"page": int, "page_size": int, "offset": int}
            其中 offset 是 SQL 查询的偏移量（skip），计算公式：offset = (page - 1) * page_size
    
    使用示例：
        @router.get("/users")
        async def get_users(
            db: Session = Depends(get_db),
            pagination: dict = Depends(get_pagination)
        ):
            page = pagination["page"]
            page_size = pagination["page_size"]
            offset = pagination["offset"]   # SQL 的 OFFSET 值
            ...
    """
    return {
        "page": page,                              # 当前页码
        "page_size": page_size,                    # 每页数量
        "offset": (page - 1) * page_size           # SQL 偏移量
    }
