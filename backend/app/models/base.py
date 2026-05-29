# =============================================================================
# 智能零售用户行为分析系统 - SQLAlchemy 数据库基类
# =============================================================================
# 功能说明：
#   创建 SQLAlchemy 引擎、会话管理器和声明式基类
#   所有数据库表模型都继承自 Base 类
#
# 使用方式：
#   在模型文件中：from app.models.base import Base
#   class MyModel(Base): ...
#
# 数据库连接：
#   使用 SQLAlchemy 的连接池管理数据库连接，默认连接池大小为 5
#   连接字符串格式：mysql+pymysql://用户名:密码@主机:端口/数据库名
# =============================================================================

from sqlalchemy import create_engine            # 数据库引擎
from sqlalchemy.orm import sessionmaker          # 会话工厂
from sqlalchemy.ext.declarative import declarative_base  # 声明式基类
from app.config import settings                  # 应用配置


# =============================================================================
# 创建数据库引擎
# =============================================================================
# create_engine 是 SQLAlchemy 的核心工厂函数，用于创建数据库连接
#
# 关键参数说明：
#   - pool_size=10: 连接池大小（最多同时保持 10 个数据库连接）
#   - max_overflow=20: 连接池溢出大小（当连接池满时，最多额外创建 20 个连接）
#   - pool_recycle=3600: 连接回收时间（秒），超过 1 小时的连接自动回收
#   - pool_pre_ping=True: 每次从连接池获取连接前先发送 ping 测试连接是否有效
#                         （推荐开启，防止 MySQL 8小时超时断开连接）
#   - echo=False: 是否打印 SQL 语句（生产环境必须关闭，调试时可设为 True）
# =============================================================================
engine = create_engine(
    settings.database_url,       # 数据库连接字符串（从 config 获取）
    pool_size=10,                # 连接池大小
    max_overflow=20,             # 最大溢出连接数
    pool_recycle=3600,           # 连接回收时间（3600秒 = 1小时）
    pool_pre_ping=True,          # 连接前预检查
    echo=False                   # 不打印 SQL 日志（调试时可改为 True）
)


# =============================================================================
# 创建会话工厂
# =============================================================================
# sessionmaker 用于创建数据库会话对象
# 会话（Session）是操作数据库的主要接口：增、删、改、查都通过会话完成
#
# 关键参数：
#   - autocommit=False: 不自动提交，需要手动调用 session.commit()
#   - autoflush=False: 不自动刷新，需要手动调用 session.flush()
#   - bind=engine: 绑定到上面创建的数据库引擎
# =============================================================================
SessionLocal = sessionmaker(
    autocommit=False,   # 不自动提交事务
    autoflush=False,    # 不自动刷新
    bind=engine         # 绑定数据库引擎
)


# =============================================================================
# 创建声明式基类
# =============================================================================
# declarative_base() 返回一个基类，所有 ORM 模型类都继承自它
# 继承 Base 的类会自动映射到数据库中的表
#
# 使用示例：
#   class User(Base):
#       __tablename__ = "users"
#       id = Column(Integer, primary_key=True)
#       username = Column(String(50))
# =============================================================================
Base = declarative_base()


# =============================================================================
# 数据库依赖注入函数
# =============================================================================
# FastAPI 使用依赖注入方式获取数据库会话
# 在路由函数中通过 Depends(get_db) 获取会话对象
#
# 使用示例：
#   @router.get("/users")
#   async def get_users(db: Session = Depends(get_db)):
#       users = db.query(User).all()
#       return users
# =============================================================================
def get_db():
    """
    获取数据库会话（FastAPI 依赖注入）
    
    这是一个生成器函数，用于 FastAPI 的 Depends 依赖注入。
    每次请求会创建一个新的数据库会话，请求结束后自动关闭。
    
    Yields:
        Session: SQLAlchemy 数据库会话对象
    
    使用方式（在路由函数中）：
        from app.models.base import get_db
        @router.get("/users")
        async def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()  # 创建新的数据库会话
    try:
        yield db          # 将会话提供给路由函数
    finally:
        db.close()        # 请求结束后确保关闭会话，归还连接给连接池
