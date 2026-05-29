# =============================================================================
# 智能零售用户行为分析系统 - 统一响应格式工具
# =============================================================================
# 功能说明：
#   为整个后端提供统一的 API 响应格式，确保所有接口返回格式一致
#
# 响应格式规范（来自 API 接口规范文档）：
#   成功响应：{"code": 200, "message": "success", "data": {...}}
#   分页响应：{"code": 200, "message": "success", "data": {"items": [...], "total": 100, "page": 1, "page_size": 10}}
#   错误响应：{"code": 400, "message": "错误描述", "data": null}
#
# 错误码定义：
#   200 - 成功
#   400 - 请求参数错误
#   401 - 未认证 / Token 过期
#   403 - 无权限
#   404 - 资源不存在
#   500 - 服务器内部错误
# =============================================================================

from typing import Any, Optional, Dict, List   # 类型注解


def success_response(data: Any = None, message: str = "success") -> Dict:
    """
    构建成功响应（HTTP 200）
    
    对应 API 接口规范文档中的：
    {
      "code": 200,
      "message": "success",
      "data": { ... }
    }
    
    Args:
        data: 响应数据，可以是字典、列表、None 等任意类型
        message: 响应消息，登录成功等场景可自定义为"登录成功"
    
    Returns:
        Dict: 统一格式的成功响应字典
    
    示例：
        >>> success_response({"id": 1, "username": "admin"})
        {"code": 200, "message": "success", "data": {"id": 1, "username": "admin"}}
        
        >>> success_response(None, "登出成功")
        {"code": 200, "message": "登出成功", "data": None}
    """
    return {
        "code": 200,        # 成功状态码
        "message": message, # 响应消息
        "data": data        # 响应数据
    }


def error_response(code: int, message: str, data: Any = None) -> Dict:
    """
    构建错误响应
    
    对应 API 接口规范文档中的：
    {
      "code": 400,           // 或其他错误码
      "message": "错误描述信息",
      "data": null
    }
    
    Args:
        code: 错误码（必须使用以下值之一）：
            - 400: 请求参数错误（参数校验失败、缺少必填字段）
            - 401: 未认证 / Token 过期（需要重新登录）
            - 403: 无权限（当前用户没有操作该资源的权限）
            - 404: 资源不存在（请求的用户/商品/订单等不存在）
            - 500: 服务器内部错误（代码异常、数据库连接失败等）
        message: 错误消息描述（通俗易懂的中文描述）
        data: 额外数据，通常为 None
    
    Returns:
        Dict: 统一格式的错误响应字典
    
    示例：
        >>> error_response(404, "用户不存在")
        {"code": 404, "message": "用户不存在", "data": None}
        
        >>> error_response(401, "Token已过期，请重新登录")
        {"code": 401, "message": "Token已过期，请重新登录", "data": None}
    """
    return {
        "code": code,        # 错误码
        "message": message,  # 错误消息
        "data": data         # 额外数据（通常为 None）
    }


def paginated_response(items: List, total: int, page: int, page_size: int) -> Dict:
    """
    构建分页响应
    
    对应 API 接口规范文档中的：
    {
      "code": 200,
      "message": "success",
      "data": {
        "items": [ ... ],      // 当前页的数据列表
        "total": 100,          // 总记录数
        "page": 1,             // 当前页码
        "page_size": 10        // 每页数量
      }
    }
    
    Args:
        items: 当前页的数据列表（已分页处理后的列表）
        total: 符合条件的总记录数（用于前端计算总页数）
        page: 当前页码（从 1 开始）
        page_size: 每页显示数量
    
    Returns:
        Dict: 统一格式的分页响应字典
    
    示例：
        >>> paginated_response([{"id": 1}, {"id": 2}], 100, 1, 10)
        {
            "code": 200,
            "message": "success",
            "data": {
                "items": [{"id": 1}, {"id": 2}],
                "total": 100,
                "page": 1,
                "page_size": 10
            }
        }
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "items": items,           # 当前页数据列表
            "total": total,           # 总记录数
            "page": page,             # 当前页码
            "page_size": page_size    # 每页数量
        }
    }
