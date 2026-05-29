# =============================================================================
# 智能零售用户行为分析系统 - 数据库初始化脚本
# =============================================================================
# 功能说明：
#   1. 创建数据库（如果不存在）
#   2. 创建所有数据库表
#   3. 插入初始管理员账号和测试数据
#
# 使用方式：
#   python init_db.py           # 创建表并插入初始数据
#   python init_db.py --reset   # 删除所有表后重新创建（危险操作！）
#
# 注意：
#   - 首次运行前确保 MySQL 和 Redis 服务已启动
#   - 需要预先安装依赖：pip install -r requirements.txt
# =============================================================================

import sys                          # 系统参数
import os                           # 操作系统接口

# 将项目根目录添加到 Python 路径，确保可以导入 app 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.base import engine, Base, SessionLocal  # 数据库引擎、基类、会话工厂
from app.models.user import User                        # 用户表模型

# 导入密码加密库（bcrypt）
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_tables():
    """
    创建所有数据库表
    
    使用 SQLAlchemy 的 create_all 方法，自动根据 ORM 模型定义创建表
    注意：只会创建不存在的表，不会修改已存在的表结构
    """
    print("\n" + "=" * 60)
    print("  正在创建数据库表...")
    print("=" * 60)
    
    # 创建所有继承自 Base 的模型对应的数据库表
    Base.metadata.create_all(bind=engine)
    
    print("[OK] 数据库表创建成功！")
    # 打印已创建的表名
    table_names = Base.metadata.tables.keys()
    for name in table_names:
        print(f"   [TABLE] {name}")


def init_admin_user():
    """
    初始化管理员账号
    
    创建默认管理员用户（admin）和普通测试用户（user001）
    密码使用 bcrypt 加密存储
    
    管理员账号：
        - 用户名: admin
        - 密码: admin123
        - 角色: admin（管理员，拥有所有权限）
    
    测试用户账号：
        - 用户名: user001
        - 密码: user123
        - 角色: user（普通用户）
    """
    print("\n" + "=" * 60)
    print("  正在初始化用户数据...")
    print("=" * 60)
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # -------------------- 1. 创建管理员账号 --------------------
        # 检查管理员是否已存在（避免重复创建）
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("[WARN] 管理员账号已存在，跳过创建")
        else:
            # 创建管理员用户
            admin_user = User(
                username="admin",                          # 用户名
                password=pwd_context.hash("admin123"),     # 密码（bcrypt 加密）
                role="admin",                              # 角色：管理员
                nickname="系统管理员",                      # 昵称
                email="admin@retail.com",                  # 邮箱
                phone="13800000001",                       # 手机号
            )
            db.add(admin_user)
            db.commit()
            print("[OK] 管理员账号创建成功！")
            print(f"   用户名: admin")
            print(f"   密码: admin123")
            print(f"   角色: 管理员（admin）")
        
        # -------------------- 2. 创建普通测试用户 --------------------
        existing_user = db.query(User).filter(User.username == "user001").first()
        if existing_user:
            print("[WARN] 测试用户账号已存在，跳过创建")
        else:
            user = User(
                username="user001",                        # 用户名
                password=pwd_context.hash("user123"),      # 密码（bcrypt 加密）
                role="user",                               # 角色：普通用户
                nickname="测试用户",                        # 昵称
                email="user001@retail.com",                # 邮箱
                phone="13800000002",                       # 手机号
            )
            db.add(user)
            db.commit()
            print("[OK] 测试用户账号创建成功！")
            print(f"   用户名: user001")
            print(f"   密码: user123")
            print(f"   角色: 普通用户（user）")
        
        # -------------------- 3. 验证密码加密 --------------------
        # 从数据库读取管理员用户，验证密码是否正确
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            is_valid = pwd_context.verify("admin123", admin.password)
            if is_valid:
                print("\n[OK] 密码加密验证通过！")
            else:
                print("\n[ERROR] 密码加密验证失败！请检查 bcrypt 是否正确安装。")
        
        print("\n" + "=" * 60)
        print("  数据库初始化完成！")
        print("=" * 60)
        print(f"\n可用账号：")
        print(f"   管理员: admin / admin123")
        print(f"   普通用户: user001 / user123")
        print(f"\n启动后端服务：")
        print(f"   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        print(f"\nAPI 文档地址：")
        print(f"   http://localhost:8000/docs")
        print(f"   http://localhost:8000/redoc")
        print()
        
    except Exception as e:
        # 发生错误时回滚事务
        db.rollback()
        print(f"\n[ERROR] 初始化失败: {str(e)}")
        raise
    finally:
        # 确保关闭数据库会话
        db.close()


def reset_database():
    """
    重置数据库（危险操作！）
    
    删除所有表后重新创建，所有数据将丢失！
    仅在开发/测试环境使用，生产环境严禁使用！
    """
    print("\n[WARN] 警告：即将删除所有数据库表和数据！")
    confirm = input("   输入 'yes' 确认操作: ")
    
    if confirm.lower() != "yes":
        print("[CANCEL] 操作已取消")
        return
    
    print("\n正在删除所有表...")
    # drop_all 删除所有由 Base 管理的表
    Base.metadata.drop_all(bind=engine)
    print("[OK] 所有表已删除")
    
    # 重新创建表
    create_tables()
    
    # 重新插入初始数据
    init_admin_user()


# =============================================================================
# 主函数
# =============================================================================

if __name__ == "__main__":
    """
    脚本入口
    
    用法：
        python init_db.py           # 创建表和初始数据（推荐首次运行时使用）
        python init_db.py --reset   # 重置所有表和数据（危险！）
    """
    # 检查命令行参数
    if "--reset" in sys.argv:
        # 重置模式：删除所有表后重新创建
        reset_database()
    else:
        # 初始化模式：创建表并插入初始数据
        create_tables()    # 步骤1：创建数据库表
        init_admin_user()  # 步骤2：插入初始用户数据
