# =============================================================================
# 智能零售用户行为分析系统 - FastAPI 应用入口
# =============================================================================
# 功能说明：
#   1. 创建 FastAPI 应用实例
#   2. 配置 CORS 跨域中间件（允许前端域名访问）
#   3. 注册所有 API 路由模块
#   4. 配置应用启动/关闭事件（初始化/清理数据库连接、Redis 连接）
#
# 启动方式：
#   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
#   或执行命令：python -m uvicorn app.main:app --reload
#
# Base URL: http://localhost:8000/api/v1
# Swagger 文档: http://localhost:8000/docs
# ReDoc 文档: http://localhost:8000/redoc
# =============================================================================

from fastapi import FastAPI, Depends                                     # FastAPI 框架
from fastapi.middleware.cors import CORSMiddleware                    # CORS 跨域中间件
from contextlib import asynccontextmanager                           # 异步上下文管理器
from sqlalchemy.orm import Session                                   # SQLAlchemy 会话类型
from app.config import settings                                      # 应用配置
from app.models.base import engine, Base, get_db                     # 数据库引擎、基类、会话依赖


# =============================================================================
# 应用生命周期管理（启动/关闭事件）
# =============================================================================
# FastAPI 推荐使用 asynccontextmanager 管理应用生命周期
# startup: 应用启动时执行（创建数据库表、初始化连接等）
# shutdown: 应用关闭时执行（释放资源、关闭连接等）
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 应用生命周期管理器
    
    startup（应用启动时）：
        1. 创建所有数据库表（如果表不存在则自动创建）
        2. 打印启动信息
    
    shutdown（应用关闭时）：
        1. 释放数据库连接池资源（归还所有连接到连接池）
        2. 打印关闭信息
    
    注意：
        - create_all 不会影响已存在的表，只在表不存在时创建
        - 如果修改了表结构，需要手动迁移，不能自动更新
        - dispose 会释放所有连接，但不影响其他进程的连接
    """
    # ==================== 启动阶段 ====================
    print(f"\n{'='*60}")
    print(f"  {settings.APP_NAME}")
    print(f"  API 文档地址: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"  Base URL: http://{settings.HOST}:{settings.PORT}/api/v1")
    print(f"{'='*60}\n")
    
    # 创建所有数据库表（仅创建不存在的表，不修改已存在的表）
    # Base.metadata 包含所有继承自 Base 的模型的表定义
    Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表初始化完成")
    
    # 进入应用运行阶段
    yield
    
    # ==================== 关闭阶段 ====================
    # 释放数据库连接池中的所有连接
    engine.dispose()
    print("[OK] 数据库连接已关闭，应用已停止")


# =============================================================================
# 创建 FastAPI 应用实例
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,                  # API 文档标题
    description="智能零售用户行为分析系统 - 后端 API 服务",  # API 文档描述
    version="1.0.0",                          # API 版本
    docs_url="/docs",                         # Swagger UI 文档地址
    redoc_url="/redoc",                       # ReDoc 文档地址
    lifespan=lifespan                         # 生命周期管理器
)


# =============================================================================
# CORS 跨域中间件配置
# =============================================================================
# CORS（Cross-Origin Resource Sharing）跨域资源共享
# 前端和后端在不同端口运行（如前端 5173、后端 8000），浏览器会阻止跨域请求
# CORSMiddleware 允许特定域名的前端访问后端 API
#
# 配置说明：
#   - allow_origins: 允许的前端域名列表（从配置文件读取）
#   - allow_credentials: 允许携带 Cookie/认证信息（True 表示允许）
#   - allow_methods: 允许的 HTTP 方法（["*"] 表示允许所有方法）
#   - allow_headers: 允许的请求头（["*"] 表示允许所有请求头）
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,    # 允许的前端域名列表
    allow_credentials=True,                       # 允许携带认证凭据（如 Cookie）
    allow_methods=["*"],                          # 允许所有 HTTP 方法（GET/POST/PUT/DELETE等）
    allow_headers=["*"],                          # 允许所有请求头（Authorization、Content-Type等）
)


# =============================================================================
# 注册 API 路由模块
# =============================================================================
# include_router: 将子路由注册到主应用中
# prefix: 路由前缀（所有子路由的路径前都会加上此前缀）
#
# 路由结构：
#   /api/v1/auth/login     -> 认证模块：登录
#   /api/v1/auth/me        -> 认证模块：获取用户信息
#   /api/v1/auth/logout    -> 认证模块：登出
#   /api/v1/users          -> 用户管理模块（后续开发）
#   ...以此类推
# =============================================================================

# 导入各模块的路由
from app.api.auth import router as auth_router          # 认证模块路由
from app.api.users import router as users_router        # 用户管理模块路由
from app.api.products import router as products_router  # 商品管理模块路由
from app.api.orders import router as orders_router      # 订单管理模块路由
from app.api.behaviors import router as behaviors_router  # 行为数据模块路由
from app.api.analysis import router as analysis_router    # 数据分析模块路由
from app.api.recommend import router as recommend_router  # 推荐系统模块路由
from app.api.dashboard import router as dashboard_router  # 数据驾驶舱模块路由

# 注册认证模块路由
app.include_router(auth_router, prefix="/api/v1")

# 注册用户管理模块路由
app.include_router(users_router, prefix="/api/v1")

# 注册商品管理模块路由
app.include_router(products_router, prefix="/api/v1")

# 注册订单管理模块路由
app.include_router(orders_router, prefix="/api/v1")

# 注册行为数据模块路由
app.include_router(behaviors_router, prefix="/api/v1")

# 注册数据分析模块路由
app.include_router(analysis_router, prefix="/api/v1")

# 注册推荐系统模块路由
app.include_router(recommend_router, prefix="/api/v1")

# 注册数据驾驶舱模块路由
app.include_router(dashboard_router, prefix="/api/v1")

# ======================== 分类独立路由（4.6 GET /categories） ========================
# 分类路由独立于 /products 前缀，直接挂载在 /api/v1/categories
from app.models.category import Category as CatModel
from app.schemas.product import CategoryResponse as CatResp
from app.utils.response_utils import success_response as s_ok

@app.get("/api/v1/categories", summary="获取分类列表", tags=["商品管理"])
async def get_categories(db: Session = Depends(get_db)):
    """获取所有商品分类列表，支持树形结构（通过parent_id）"""
    cats = db.query(CatModel).order_by(CatModel.id).all()
    data = [
        CatResp(id=c.id, name=str(c.name), parent_id=c.parent_id).model_dump()
        for c in cats
    ]
    return s_ok(data=data)


# =============================================================================
# 根路由：API 欢迎页
# =============================================================================

@app.get("/", summary="API 根路径", tags=["系统"])
async def root():
    """
    API 根路径，返回欢迎信息和可用接口列表
    
    访问 http://localhost:8000/ 可查看此欢迎页面
    访问 http://localhost:8000/docs 可查看 Swagger API 文档
    """
    return {
        "code": 200,
        "message": "success",
        "data": {
            "app_name": settings.APP_NAME,
            "version": "1.0.0",
            "docs": f"http://{settings.HOST}:{settings.PORT}/docs",
            "base_url": f"http://{settings.HOST}:{settings.PORT}/api/v1",
            "available_modules": {
                "认证模块": ["POST /auth/login", "GET /auth/me", "POST /auth/logout"],
                "用户管理": ["GET /users", "GET /users/{id}", "POST /users", "PUT /users/{id}", "DELETE /users/{id}"],
                "商品管理": ["GET /products", "GET /products/{id}", "POST /products", "PUT /products/{id}", "DELETE /products/{id}", "GET /categories", "GET /products/hot"],
                "订单管理": ["GET /orders", "GET /orders/{id}", "POST /orders", "PUT /orders/{id}/status", "GET /orders/trend"]
            }
        }
    }


# =============================================================================
# 健康检查路由
# =============================================================================

@app.get("/health", summary="健康检查", tags=["系统"])
async def health_check():
    """
    健康检查接口
    
    用于监控系统状态，不需要认证即可访问
    返回 "ok" 表示服务正常运行
    """
    return {
        "code": 200,
        "message": "ok",
        "data": {"status": "healthy"}
    }
