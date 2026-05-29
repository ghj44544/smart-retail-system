# =============================================================================
# 智能零售用户行为分析系统 - 用户表 ORM 模型
# =============================================================================
# 对应数据库表：users（用户表）
#
# 表结构（来自 API 接口规范文档和计划文档）：
#   id         INT           自增主键
#   username   VARCHAR(50)   用户名（唯一，必填）
#   password   VARCHAR(255)  密码（加密存储，使用 bcrypt）
#   role       ENUM          角色（admin: 管理员 / user: 普通用户）
#   nickname   VARCHAR(100)  昵称
#   avatar     VARCHAR(255)  头像URL
#   email      VARCHAR(100)  邮箱
#   phone      VARCHAR(20)   手机号
#   last_login DATETIME      最后登录时间
#   created_at DATETIME      创建时间
#   deleted_at DATETIME      软删除时间（非NULL表示已删除）
# =============================================================================

from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum  # SQLAlchemy 字段类型
from sqlalchemy.sql import func                                           # SQL 函数（如 CURRENT_TIMESTAMP）
from app.models.base import Base                                          # ORM 基类


class User(Base):
    """
    用户表 ORM 模型
    
    映射到数据库中的 users 表，每个实例对应表中的一行数据
    
    字段说明：
        id          : 用户唯一标识，自增主键
        username    : 登录用户名，全局唯一
        password    : 加密后的密码（使用 bcrypt 算法加密）
        role        : 用户角色，admin=管理员（拥有所有权限），user=普通用户
        nickname    : 用户昵称/显示名称
        avatar      : 用户头像的 URL 地址
        email       : 用户邮箱地址
        phone       : 用户手机号码
        created_at  : 账号创建时间（数据库自动生成）
    
    使用示例：
        # 查询用户
        user = db.query(User).filter(User.id == 1).first()
        
        # 创建用户
        new_user = User(username="test", password="hashed_pw", nickname="测试")
        db.add(new_user)
        db.commit()
    """
    
    # ======================== 表名 ========================
    # 指定该模型对应的数据库表名
    __tablename__ = "users"
    
    # ======================== 表字段定义 ========================
    
    # 主键：自增整数 ID
    # primary_key=True: 标记为主键
    # autoincrement=True: MySQL 自动递增
    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    
    # 用户名：登录凭证，全局唯一
    # unique=True: 数据库层面保证唯一性
    # nullable=False: 不允许为空
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    
    # 密码：使用 bcrypt 加密后的哈希值
    # 存储格式示例：$2b$12$LJ3m4ys3GAx2k1Vz6K0z9.xxxxx（60字符）
    # 注意：绝不明文存储密码！
    password = Column(String(255), nullable=False, comment="密码（加密存储）")
    
    # 角色：admin（管理员）或 user（普通用户）
    # default="user": 新注册用户默认为普通用户
    role = Column(
        SQLEnum('admin', 'user', name='user_role_enum'),
        default='user',
        nullable=False,
        comment="角色：admin=管理员, user=普通用户"
    )
    
    # 昵称：用户的显示名称（可以不是唯一的）
    nickname = Column(String(100), comment="昵称")
    
    # 头像：用户头像图片的 URL 地址
    avatar = Column(String(255), comment="头像URL")
    
    # 邮箱：用户的邮箱地址
    email = Column(String(100), comment="邮箱")
    
    # 手机号：用户的手机号码
    phone = Column(String(20), comment="手机号")
    
    # 创建时间：账号的创建日期时间
    # server_default=func.now(): 数据库服务器在插入时自动填充当前时间
    created_at = Column(
        DateTime,
        server_default=func.now(),
        comment="创建时间"
    )
    
    # 最后登录时间：用户最近一次登录的时间
    # nullable=True: 新注册用户可能从未登录过
    last_login = Column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )
    
    # 软删除时间：非NULL表示用户已被软删除
    # 软删除：不清除数据库记录，仅标记为已删除
    # 查询用户时需要过滤 deleted_at != None 的记录（排除已删除用户）
    # nullable=True: NULL 表示未被删除
    deleted_at = Column(
        DateTime,
        nullable=True,
        default=None,
        comment="软删除时间（NULL=未删除）"
    )
    
    # ======================== 对象表示方法 ========================
    
    def __repr__(self) -> str:
        """
        返回对象的字符串表示（用于调试和日志输出）
        
        Returns:
            str: 如 "<User(id=1, username='admin', role='admin')>"
        """
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    def to_dict(self) -> dict:
        """
        将用户对象转换为字典（用于返回给前端）
        
        注意：此方法不会返回密码字段，保证安全性
        
        Returns:
            dict: 用户信息的字典表示（不含密码）
        
        示例：
            >>> user.to_dict()
            {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "nickname": "系统管理员",
                "avatar": "",
                "email": "admin@example.com",
                "phone": "13800138000",
                "created_at": "2026-01-01T00:00:00"
            }
        """
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "nickname": self.nickname or "",
            "avatar": self.avatar or "",
            "email": self.email or "",
            "phone": self.phone or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
