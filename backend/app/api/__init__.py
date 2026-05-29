"""
智能零售用户行为分析系统 - API 路由模块
==========================================
本目录包含所有 API 路由定义，按业务模块拆分。

包含以下子模块：
    - auth.py         : 认证接口（POST /auth/login, GET /auth/me, POST /auth/logout）
    - users.py        : 用户管理接口（待开发）
    - products.py     : 商品管理接口（待开发）
    - orders.py       : 订单管理接口（待开发）
    - behaviors.py    : 行为数据接口（待开发）
    - analysis.py     : 数据分析接口（待开发）
    - recommend.py    : 推荐系统接口（待开发）
    - dashboard.py    : 数据驾驶舱接口（待开发）

路由注册方式：
    在 main.py 中使用 FastAPI 的 include_router 方法注册路由
    Base URL 前缀：/api/v1
"""
