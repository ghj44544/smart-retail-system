# =============================================================================
# 智能零售用户行为分析系统 - 用户管理模块 API 路由
# =============================================================================
# 模块功能：
#   提供用户管理相关的 RESTful API 接口，包括：
#     1. GET    /users          - 分页获取用户列表（支持搜索和筛选）
#     2. GET    /users/{user_id} - 获取指定用户的详细信息
#     3. POST   /users          - 创建新用户（管理员操作）
#     4. PUT    /users/{user_id} - 更新用户信息
#     5. DELETE /users/{user_id} - 软删除用户
#
# 对应 API 接口规范文档：第三章「用户管理接口」
# Base URL: http://localhost:8000/api/v1
# =============================================================================

from fastapi import APIRouter, Depends, Query, HTTPException, status  # FastAPI 路由、依赖、查询参数、异常
from sqlalchemy.orm import Session                                     # SQLAlchemy 数据库会话
from datetime import datetime                                          # 日期时间处理
from typing import Dict, Optional                                      # 类型注解

# 自定义模块导入
from app.schemas.user import (
    CreateUserRequest,       # 创建用户请求模型
    UpdateUserRequest,       # 更新用户请求模型
    UserListItem,            # 用户列表项响应模型
    UserDetailResponse,      # 用户详情响应模型
    UserCreateResponse       # 创建用户响应模型
)
from app.models.user import User                                      # 用户 ORM 模型
from app.models.base import get_db                                    # 数据库会话依赖注入
from app.utils.response_utils import success_response, error_response, paginated_response  # 统一响应格式
from app.utils.jwt_utils import get_current_user                      # JWT 认证依赖注入

# 导入密码加密函数（从认证模块复用）
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# =============================================================================
# 创建路由实例
# =============================================================================
# prefix="/users": 该路由下所有接口都以 /users 开头
# tags=["用户管理"]: 在 Swagger 文档中归类到"用户管理"分组
router = APIRouter(
    prefix="/users",        # 路由前缀
    tags=["用户管理"]       # Swagger 文档分组标签
)


# ======================== 辅助函数 ========================

def verify_password_helper(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与加密密码是否匹配（复用认证模块的逻辑）
    
    Args:
        plain_password: 用户输入的明文密码
        hashed_password: 数据库中存储的 bcrypt 加密密码
    
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password_helper(password: str) -> str:
    """
    将明文密码加密为 bcrypt 哈希值（复用认证模块的逻辑）
    
    Args:
        password: 明文密码
    
    Returns:
        str: bcrypt 加密后的哈希值
    """
    return pwd_context.hash(password)


# ======================== 接口 1：获取用户列表 ========================

@router.get("", summary="获取用户列表")
async def get_users(
    # ===== 分页参数 =====
    page: int = Query(default=1, ge=1, description="页码，从1开始"),
    page_size: int = Query(default=10, ge=1, le=100, description="每页数量，最大100"),
    # ===== 筛选参数 =====
    keyword: Optional[str] = Query(default=None, description="搜索关键词（用户名/昵称）"),
    role: Optional[str] = Query(default=None, description="角色筛选（admin/user）"),
    # ===== 依赖注入 =====
    db: Session = Depends(get_db),                                  # 数据库会话
    current_user: Dict = Depends(get_current_user)                  # 当前登录用户（需认证）
) -> Dict:
    """
    分页获取用户列表，支持搜索和筛选
    
    对应 API 接口规范文档：3.1 获取用户列表
    
    功能说明：
        1. 按条件筛选用户（排除已软删除的用户）
        2. 支持按用户名/昵称模糊搜索
        3. 支持按角色筛选
        4. 分页返回结果
    
    请求参数（Query）：
        ?page=1&page_size=10&keyword=张三&role=user
    
    成功响应格式：
        {
            "code": 200,
            "message": "success",
            "data": {
                "items": [{...}],
                "total": 100,
                "page": 1,
                "page_size": 10
            }
        }
    """
    
    # 步骤1：构建基础查询（默认排除已软删除的用户）
    # deleted_at == None 表示用户未被删除
    query = db.query(User).filter(User.deleted_at == None)
    
    # 步骤2：关键词模糊搜索（同时匹配用户名和昵称）
    if keyword:
        # OR 条件：username 包含关键词 OR nickname 包含关键词
        # like() 中的 % 是 SQL 通配符，表示任意字符
        query = query.filter(
            (User.username.like(f"%{keyword}%")) |
            (User.nickname.like(f"%{keyword}%"))
        )
    
    # 步骤3：角色筛选
    if role and role in ['admin', 'user']:
        query = query.filter(User.role == role)
    
    # 步骤4：获取总数（在分页前计算）
    total = query.count()
    
    # 步骤5：分页查询
    # offset: 跳过前面 (page-1)*page_size 条记录
    # limit: 只取 page_size 条记录
    users = query.order_by(User.id.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    
    # 步骤6：构建响应数据列表
    items = []
    for user in users:
        # 构建用户列表项
        # 注意：total_consumption 和 order_count 当前返回 0
        # 待订单模块开发后，从订单表实时计算
        item = UserListItem(
            id=user.id,
            username=str(user.username),
            nickname=str(user.nickname or ""),
            email=user.email,
            phone=user.phone,
            role=str(user.role),
            total_consumption=0.0,       # 订单模块开发后填充
            order_count=0,                # 订单模块开发后填充
            last_login=user.last_login,
            created_at=user.created_at
        )
        items.append(item.model_dump())
    
    # 步骤7：返回分页响应
    return paginated_response(
        items=items,          # 当前页数据
        total=total,          # 总记录数
        page=page,            # 当前页码
        page_size=page_size   # 每页数量
    )


# ======================== 接口 2：获取用户详情 ========================

@router.get("/{user_id}", summary="获取用户详情")
async def get_user_detail(
    user_id: int,                                                   # 路径参数：用户ID
    db: Session = Depends(get_db),                                  # 数据库会话
    current_user: Dict = Depends(get_current_user)                  # 当前登录用户（需认证）
) -> Dict:
    """
    获取指定用户的详细信息
    
    对应 API 接口规范文档：3.2 获取用户详情
    
    功能说明：
        1. 根据用户ID查询用户信息
        2. 返回用户详细信息（含消费统计、RFM分值、聚类标签等）
    
    路径参数：
        /users/{user_id}  - user_id 为用户ID
    
    成功响应格式：
        {
            "code": 200,
            "message": "success",
            "data": {
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
        }
    
    注意：
        - total_consumption, order_count, avg_order_value, last_purchase
          当前返回默认值（0 或 null），订单模块开发后从订单表计算
        - rfm_score 当前返回 null，RFM分析模块开发后填充
        - cluster_label 当前返回 null，聚类分析模块开发后填充
    """
    
    # 步骤1：查询用户（排除已软删除的用户）
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None   # 只查询未删除的用户
    ).first()
    
    # 步骤2：验证用户是否存在
    if not user:
        return error_response(
            code=status.HTTP_404_NOT_FOUND,  # 404 资源不存在
            message="用户不存在"
        )
    
    # 步骤3：构建用户详情响应
    # 注意：消费统计相关字段（total_consumption, order_count 等）
    # 当前返回默认值，后续由订单模块提供真实数据
    # RFM 分值和聚类标签也返回 null，由分析模块填充
    user_detail = UserDetailResponse(
        id=user.id,
        username=str(user.username),
        nickname=str(user.nickname or ""),
        email=user.email,
        phone=user.phone,
        role=str(user.role),
        # ===== 消费统计（订单模块开发后填充真实数据） =====
        total_consumption=0.0,
        order_count=0,
        avg_order_value=0.0,
        last_purchase=None,
        # ===== 分析结果（分析模块开发后填充真实数据） =====
        rfm_score=None,
        cluster_label=None,
        # ===== 时间字段 =====
        last_login=user.last_login,
        created_at=user.created_at,
        avatar=user.avatar
    )
    
    # 步骤4：返回成功响应
    return success_response(data=user_detail.model_dump())


# ======================== 接口 3：创建用户 ========================

@router.post("", summary="创建用户")
async def create_user(
    request: CreateUserRequest,                                      # 请求体（Pydantic 自动验证）
    db: Session = Depends(get_db),                                   # 数据库会话
    current_user: Dict = Depends(get_current_user)                  # 当前登录用户（需认证）
) -> Dict:
    """
    创建新用户（管理员操作）
    
    对应 API 接口规范文档：3.3 创建用户
    
    功能说明：
        1. 接收用户信息
        2. 验证用户名是否已存在
        3. 密码使用 bcrypt 加密存储
        4. 创建用户记录并返回
    
    请求格式（POST /users）：
        {
            "username": "user002",
            "nickname": "李四",
            "email": "lisi@example.com",
            "phone": "13900001111",
            "password": "123456",
            "role": "user"
        }
    
    安全说明：
        - 密码使用 bcrypt 加密后存储，数据库中不会保存明文密码
        - 用户名全局唯一，重复创建会返回 400 错误
    """
    
    # 步骤1：检查用户名是否已存在（包括已删除的用户）
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        return error_response(
            code=status.HTTP_400_BAD_REQUEST,  # 400 请求参数错误
            message=f"用户名 '{request.username}' 已存在"
        )
    
    # 步骤2：验证角色值是否合法
    if request.role not in ['admin', 'user']:
        return error_response(
            code=status.HTTP_400_BAD_REQUEST,
            message="角色必须为 admin 或 user"
        )
    
    # 步骤3：创建新用户对象
    new_user = User(
        username=request.username,                              # 用户名
        password=hash_password_helper(request.password),        # 密码（bcrypt 加密）
        nickname=request.nickname,                               # 昵称
        email=request.email,                                     # 邮箱
        phone=request.phone,                                     # 手机号
        role=request.role                                        # 角色
    )
    
    # 步骤4：保存到数据库
    db.add(new_user)      # 添加到会话
    db.commit()           # 提交事务（写入数据库）
    db.refresh(new_user)  # 刷新对象（获取数据库生成的 id 和 created_at）
    
    # 步骤5：构建响应数据
    user_response = UserCreateResponse(
        id=new_user.id,
        username=str(new_user.username),
        nickname=str(new_user.nickname or ""),
        email=new_user.email,
        phone=new_user.phone,
        role=str(new_user.role),
        created_at=new_user.created_at
    )
    
    # 步骤6：返回成功响应
    return success_response(
        data=user_response.model_dump(),
        message="用户创建成功"
    )


# ======================== 接口 4：更新用户信息 ========================

@router.put("/{user_id}", summary="更新用户信息")
async def update_user(
    user_id: int,                                                    # 路径参数：用户ID
    request: UpdateUserRequest,                                      # 请求体（所有字段可选）
    db: Session = Depends(get_db),                                   # 数据库会话
    current_user: Dict = Depends(get_current_user)                  # 当前登录用户（需认证）
) -> Dict:
    """
    更新用户信息
    
    对应 API 接口规范文档：3.4 更新用户
    
    功能说明：
        1. 根据用户ID查找用户
        2. 只更新请求中提供的字段（部分更新）
        3. 如果提供了密码则重新加密存储
    
    路径参数：
        /users/{user_id}  - user_id 为用户ID
    
    请求格式（PUT /users/{user_id}）：
        {
            "nickname": "新昵称",       // 可选
            "email": "new@example.com", // 可选
            "phone": "13900000000",     // 可选
            "password": "newpassword",  // 可选
            "role": "admin"             // 可选
        }
    
    注意：
        - 请求体中只需要包含要更新的字段
        - 不包含的字段保持原有值不变
    """
    
    # 步骤1：查询用户（排除已软删除的用户）
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    # 步骤2：验证用户是否存在
    if not user:
        return error_response(
            code=status.HTTP_404_NOT_FOUND,  # 404 资源不存在
            message="用户不存在"
        )
    
    # 步骤3：逐字段检查并更新（只更新请求中提供的字段）
    # 使用 model_dump(exclude_unset=True) 获取请求中实际传入的字段
    update_data = request.model_dump(exclude_unset=True)
    
    # 如果提供了密码，则加密后存储
    if "password" in update_data and update_data["password"]:
        user.password = hash_password_helper(update_data["password"])
        del update_data["password"]  # 密码字段特殊处理，从更新数据中移除
    
    # 更新其他字段
    for field, value in update_data.items():
        # 如果值不为 None，则更新对应字段
        if value is not None:
            setattr(user, field, value)
    
    # 步骤4：保存更新到数据库
    db.commit()           # 提交事务
    db.refresh(user)      # 刷新对象（获取最新数据）
    
    # 步骤5：构建响应数据
    user_detail = UserDetailResponse(
        id=user.id,
        username=str(user.username),
        nickname=str(user.nickname or ""),
        email=user.email,
        phone=user.phone,
        role=str(user.role),
        total_consumption=0.0,
        order_count=0,
        avg_order_value=0.0,
        last_purchase=None,
        rfm_score=None,
        cluster_label=None,
        last_login=user.last_login,
        created_at=user.created_at,
        avatar=user.avatar
    )
    
    # 步骤6：返回成功响应
    return success_response(
        data=user_detail.model_dump(),
        message="用户信息更新成功"
    )


# ======================== 接口 5：删除用户（软删除） ========================

@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: int,                                                    # 路径参数：用户ID
    db: Session = Depends(get_db),                                   # 数据库会话
    current_user: Dict = Depends(get_current_user)                  # 当前登录用户（需认证）
) -> Dict:
    """
    软删除用户
    
    对应 API 接口规范文档：3.5 删除用户
    
    功能说明：
        1. 根据用户ID查找用户
        2. 将 deleted_at 字段设置为当前时间（软删除）
        3. 数据不会从数据库中物理删除，仅标记为已删除
    
    路径参数：
        /users/{user_id}  - user_id 为用户ID
    
    软删除原理：
        - 不执行 SQL DELETE 语句，而是设置 deleted_at = 当前时间
        - 所有查询接口会自动过滤 deleted_at != None 的记录
        - 数据保留在数据库中，必要时可以恢复（将 deleted_at 设回 NULL）
    
    安全说明：
        - 不能删除自己（防止管理员误删自己的账号）
        - 不能删除 admin 角色的其他管理员（保留后门）
    """
    
    # 步骤1：查询用户（排除已软删除的用户）
    user = db.query(User).filter(
        User.id == user_id,
        User.deleted_at == None
    ).first()
    
    # 步骤2：验证用户是否存在
    if not user:
        return error_response(
            code=status.HTTP_404_NOT_FOUND,  # 404 资源不存在
            message="用户不存在或已被删除"
        )
    
    # 步骤3：安全校验 —— 不能删除自己
    current_user_id = current_user["user_id"]
    if user.id == current_user_id:
        return error_response(
            code=status.HTTP_400_BAD_REQUEST,  # 400 请求参数错误
            message="不能删除自己的账号"
        )
    
    # 步骤4：执行软删除（设置 deleted_at 时间戳）
    user.deleted_at = datetime.utcnow()  # 设置为当前 UTC 时间
    db.commit()                           # 提交事务
    
    # 步骤5：返回成功响应
    return success_response(
        data=None,                     # 删除操作不需要返回数据
        message="用户已删除"
    )
