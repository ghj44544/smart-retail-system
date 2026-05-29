# =============================================================================
# 智能零售用户行为分析系统 - 应用配置模块
# =============================================================================
# 功能说明：
#   1. 从 .env 文件和环境变量中读取配置
#   2. 提供统一的配置访问接口
#   3. 包含数据库、Redis、JWT、CORS 等所有配置项
#
# 使用方式：
#   from app.config import settings
#   print(settings.MYSQL_HOST)    # 读取数据库主机
#   print(settings.database_url)   # 使用属性方法获取完整数据库URL
# =============================================================================

from pydantic_settings import BaseSettings      # Pydantic配置管理基类
from typing import Optional, List                 # 类型注解
import os                                         # 操作系统接口


class Settings(BaseSettings):
    """
    应用配置类
    
    继承自 pydantic_settings.BaseSettings，自动从以下来源读取配置（优先级从高到低）：
    1. 环境变量（操作系统环境变量）
    2. .env 文件（项目根目录下的.env文件）
    3. 类中定义的默认值
    
    注意：配置名称大小写敏感，与 .env 文件中的名称必须完全一致
    """
    
    # ======================== 应用配置 ========================
    # 应用名称，用于 Swagger 文档标题
    APP_NAME: str = "智能零售用户行为分析系统"
    # 调试模式，True 时 FastAPI 会自动重载代码
    DEBUG: bool = True
    # FastAPI 服务监听地址，0.0.0.0 表示监听所有网络接口
    HOST: str = "0.0.0.0"
    # FastAPI 服务端口
    PORT: int = 8001
    
    # ======================== MySQL 数据库配置 ========================
    # 数据库主机地址
    MYSQL_HOST: str = "localhost"
    # 数据库端口（MySQL 默认 3306）
    MYSQL_PORT: int = 3306
    # 数据库用户名
    MYSQL_USER: str = "root"
    # 数据库密码
    MYSQL_PASSWORD: str = "123456"
    # 数据库名称（需要在 MySQL 中提前创建）
    MYSQL_DATABASE: str = "retail"
    # 可选的完整数据库 URL（如果设置了此项，则忽略上述字段拼接的URL）
    SQLALCHEMY_DATABASE_URL: Optional[str] = None
    
    # ======================== Redis 缓存配置 ========================
    # Redis 主机地址
    REDIS_HOST: str = "localhost"
    # Redis 端口（默认 6379）
    REDIS_PORT: int = 6379
    # Redis 数据库编号（0-15，默认使用0号库）
    REDIS_DB: int = 0
    # Redis 密码（本环境无需密码，留空）
    REDIS_PASSWORD: Optional[str] = ""
    
    # ======================== JWT 认证配置 ========================
    # JWT 签名密钥（生产环境必须改为复杂随机字符串！）
    JWT_SECRET_KEY: str = "smart-retail-analysis-jwt-secret-key-2026"
    # JWT 签名算法（HS256 = HMAC-SHA256，对称加密）
    JWT_ALGORITHM: str = "HS256"
    # Access Token 过期时间（单位：小时，默认24小时 = 86400秒）
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # ======================== CORS 跨域配置 ========================
    # 允许访问的前端源列表（支持多个，用英文逗号分隔）
    # 开发环境常见前端端口：Vue(Vite)=5173, React=3000, Angular=4200
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # ======================== 属性方法（仅计算，不从环境变量读取） ========================
    
    @property
    def database_url(self) -> str:
        """
        构建 SQLAlchemy 数据库连接 URL
        
        格式：mysql+pymysql://用户名:密码@主机:端口/数据库名
        
        Returns:
            str: 完整的数据库连接字符串，如 "mysql+pymysql://root:123456@localhost:3306/retail"
        """
        # 如果用户指定了完整的数据库URL，则直接使用
        if self.SQLALCHEMY_DATABASE_URL:
            return self.SQLALCHEMY_DATABASE_URL
        # 否则根据各字段拼接MySQL连接URL
        # pymysql 是 Python 连接 MySQL 的驱动库
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        将 CORS_ORIGINS 字符串解析为列表
        
        .env 文件中域名用逗号分隔，此方法将其拆分并去除前后空白
        
        Returns:
            List[str]: CORS允许的域名列表，如 ["http://localhost:3000", "http://localhost:5173"]
        """
        # 按逗号分隔，去除每个元素的前后空白字符
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
    
    @property
    def redis_url(self) -> str:
        """
        构建 Redis 连接 URL
        
        格式：redis://[:password@]host:port/db
        
        Returns:
            str: Redis 连接字符串，如 "redis://localhost:6379/0"
        """
        # 如果有密码，则包含密码部分
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        # 无密码则省略密码部分
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    # Pydantic Settings 配置
    class Config:
        """
        Pydantic Settings 的元配置
        
        - env_file: 指定 .env 文件路径（相对于当前工作目录）
        - case_sensitive: 保持大小写敏感（JWT_SECRET_KEY 和 JWT_SECRET_KEY 是不同的）
        - extra: "ignore" 表示忽略 .env 中未定义的额外字段
        """
        # .env 文件路径（项目根目录下的 .env 文件）
        env_file = ".env"
        # 大小写敏感（确保配置名称精确匹配）
        case_sensitive = True
        # 忽略未定义的额外字段
        extra = "ignore"


# =============================================================================
# 创建全局配置实例
# 其他模块通过导入此实例来访问配置
# 
# 使用示例：
#   from app.config import settings
#   db_url = settings.database_url
#   jwt_key = settings.JWT_SECRET_KEY
# =============================================================================
settings = Settings()
