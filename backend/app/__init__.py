"""
智能零售用户行为分析系统 - 应用包初始化
==========================================
该文件标记 app 目录为 Python 包，使其可以被其他模块导入。

项目结构：
    app/
    ├── main.py          # FastAPI 应用入口
    ├── config.py         # 配置文件（数据库、Redis、JWT 配置）
    ├── dependencies.py   # 依赖注入（认证、分页等）
    ├── utils/            # 工具函数模块
    ├── models/           # 数据库 ORM 模型
    ├── schemas/          # Pydantic 数据验证模型
    └── api/              # API 路由模块
"""
