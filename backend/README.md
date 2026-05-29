# 智能零售用户行为分析系统 - 后端技术文档

> **技术栈**: Python 3.13 + FastAPI + MySQL 8.0 + Redis 7.x + pandas + scikit-learn  
> **Base URL**: `http://localhost:8000/api/v1`  
> **认证方式**: JWT (JSON Web Token)，有效期 24 小时  
> **文档版本**: v1.0 | **日期**: 2026年5月28日  

---

## 一、项目结构

```
backend/
├── .env                          # 环境变量配置（MySQL/Redis/JWT/CORS）
├── requirements.txt               # Python依赖包列表
├── init_db.py                     # 数据库初始化脚本（建表+初始用户）
│
└── app/
    ├── __init__.py
    ├── main.py                    # FastAPI应用入口（CORS/路由注册/生命周期）
    ├── config.py                  # 全局配置类（从.env读取）
    ├── dependencies.py            # 通用依赖注入（分页参数等）
    │
    ├── utils/                     # ---- 工具层 ----
    │   ├── response_utils.py      # 统一响应格式 {code, message, data}
    │   ├── jwt_utils.py           # JWT创建/解码/黑名单验证/依赖注入
    │   └── redis_utils.py         # Redis黑名单/通用缓存（get/set/delete）
    │
    ├── models/                    # ---- 数据模型层 ----
    │   ├── base.py                # SQLAlchemy引擎/会话/Base类
    │   ├── user.py                # 用户表（含软删除）
    │   ├── category.py            # 商品分类表（树形自引用）
    │   ├── product.py             # 商品表（含软删除）
    │   ├── order.py               # 订单表（5种状态枚举）
    │   ├── order_item.py          # 订单明细表
    │   ├── behavior.py            # 行为数据表（BIGINT主键）
    │   ├── rfm_score.py           # RFM分析结果表
    │   └── cluster_result.py      # K-Means聚类结果表
    │
    ├── schemas/                   # ---- 数据验证层 ----
    │   ├── auth.py                # 登录/用户信息 Pydantic模型
    │   ├── user.py                # 用户CRUD请求/响应模型
    │   ├── product.py             # 商品请求/响应模型
    │   ├── order.py               # 订单请求/响应模型
    │   ├── behavior.py            # 行为数据模型
    │   ├── analysis.py            # RFM/聚类/关联规则模型
    │   ├── recommend.py           # 推荐系统模型
    │   └── dashboard.py           # 驾驶舱指标模型
    │
    ├── api/                       # ---- 路由层（9大模块） ----
    │   ├── auth.py                # 认证模块（3个接口）
    │   ├── users.py               # 用户管理（5个接口）
    │   ├── products.py            # 商品管理（7个接口）
    │   ├── orders.py              # 订单管理（5个接口）
    │   ├── behaviors.py           # 行为数据（4个接口）
    │   ├── analysis.py            # 数据分析（5个接口）
    │   ├── recommend.py           # 推荐系统（4个接口）
    │   └── dashboard.py           # 数据驾驶舱（5个接口）
    │
    └── services/                  # ---- 业务逻辑层 ----
        └── analysis_service.py    # RFM/K-Means/Apriori/用户画像算法
```

---

## 二、全局设计说明

### 2.1 统一响应格式

所有接口返回标准 JSON 格式：

```json
// 成功：{"code": 200, "message": "success", "data": {...}}
// 分页：{"code": 200, "message": "success", "data": {"items": [...], "total": 100, "page": 1, "page_size": 10}}
// 错误：{"code": 400, "message": "错误描述", "data": null}
```

实现于 `app/utils/response_utils.py`，提供 `success_response()`、`error_response()`、`paginated_response()` 三个工具函数。

### 2.2 JWT 认证流程

```
1. 用户登录 → 后端验证密码 → 生成JWT Token (Payload: {user_id, role, exp})
2. 后续请求 → Header携带 Authorization: Bearer <token>
3. get_current_user 依赖 → 解码验证 → 检查Redis黑名单 → 返回 {user_id, role}
4. 用户登出 → Token加入Redis黑名单 → 后续请求返回401
```

实现于 `app/utils/jwt_utils.py`，使用 `python-jose` 库，HS256 算法签名。

### 2.3 Redis 缓存策略

| 缓存键 | 用途 | 过期时间 |
|--------|------|---------|
| `blacklist:{token}` | Token黑名单 | Token剩余有效时间 |
| `hot_products_{sort}_{limit}` | 热门商品 | 300秒 |
| `recommend_hot_{limit}` | 热门推荐 | 300秒 |
| `dashboard_metrics` | 驾驶舱指标 | 60秒 |

实现于 `app/utils/redis_utils.py`，提供通用的 `cache_get()`、`cache_set()`、`cache_delete()` 接口。

### 2.4 软删除设计

用户表和商品表使用 `deleted_at` 字段实现软删除：
- 删除操作不执行物理 `DELETE`，只设置 `deleted_at = 当前时间`
- 所有查询自动过滤 `deleted_at IS NULL`，排除已删除记录
- 数据可恢复（将 `deleted_at` 设回 NULL）

### 2.5 数据库连接管理

- 连接池大小：10（`pool_size=10`）
- 最大溢出连接：20（`max_overflow=20`）
- 连接回收：3600秒（`pool_recycle=3600`）
- 连接前预检：开启（`pool_pre_ping=True`，防止 MySQL 8小时超时）

---

## 三、各模块详细说明

### 模块1：认证模块 (auth)

| 接口 | 方法 | 路径 | 认证 | 功能 |
|------|------|------|------|------|
| 登录 | POST | `/auth/login` | 否 | 验证用户名密码，返回JWT Token |
| 获取用户 | GET | `/auth/me` | 是 | 根据Token返回当前用户信息 |
| 登出 | POST | `/auth/logout` | 是 | Token加入Redis黑名单 |

**设计要点**:
- 密码使用 bcrypt 加密（自动加盐，防彩虹表攻击）
- 错误消息统一（不区分"用户不存在"和"密码错误"，防用户枚举）
- Token 有效期 24 小时（可配置 `ACCESS_TOKEN_EXPIRE_HOURS`）

**代码文件**: `app/api/auth.py`

---

### 模块2：用户管理模块 (users)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 获取列表 | GET | `/users` | 分页查询，支持 keyword/role 筛选 |
| 获取详情 | GET | `/users/{id}` | 含消费统计、RFM分值、聚类标签 |
| 创建用户 | POST | `/users` | 密码bcrypt加密，用户名唯一校验 |
| 更新信息 | PUT | `/users/{id}` | 部分更新（只更新传入字段） |
| 删除用户 | DELETE | `/users/{id}` | 软删除（设置deleted_at），防自删 |

**设计要点**:
- 用户详情中 `total_consumption`、`order_count`、`rfm_score` 等字段来自关联表计算
- 删除用户时保护：不能删除自己的账号（`user.id == current_user_id`）
- phone 字段按原始存储返回（脱敏由前端负责）

**代码文件**: `app/api/users.py`, `app/models/user.py`

---

### 模块3：商品管理模块 (products)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 获取列表 | GET | `/products` | 分页，支持 keyword/category_id/status 筛选 |
| 获取详情 | GET | `/products/{id}` | 含关联商品（同分类其他商品ID） |
| 创建商品 | POST | `/products` | 商品编号唯一，状态 on/off |
| 更新信息 | PUT | `/products/{id}` | 部分更新，修改后清除热门缓存 |
| 删除商品 | DELETE | `/products/{id}` | 软删除，清除缓存 |
| 分类列表 | GET | `/categories` | 树形结构（parent_id自引用） |
| 热门排行 | GET | `/products/hot` | Redis缓存，支持 sales/rating 排序 |

**设计要点**:
- `/categories` 独立于 `/products` 前缀，挂载在 `/api/v1/categories`
- `/products/hot` 路由必须在 `/{product_id}` 之前注册（FastAPI路由匹配顺序）
- 热门排行优先从 Redis 读取，缓存失效则查库并更新缓存

**代码文件**: `app/api/products.py`, `app/models/product.py`, `app/models/category.py`

---

### 模块4：订单管理模块 (orders)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 获取列表 | GET | `/orders` | 分页，支持 user_id/status/日期 筛选 |
| 获取详情 | GET | `/orders/{id}` | 含订单商品明细 |
| 创建订单 | POST | `/orders` | 自动扣库存、算总金额、生成订单号 |
| 更新状态 | PUT | `/orders/{id}/status` | 状态流转，completed时更新商品销量 |
| 销售趋势 | GET | `/orders/trend` | 按天聚合销售额/订单数 |

**设计要点**:
- 订单编号自动生成：`ORD + 日期 + 4位随机数`
- 创建时扣减库存（`product.stock -= quantity`），库存不足返回 400
- 状态流转规则：`pending → paid → shipped → completed` 或 `pending → cancelled`
- 订单完成时自动更新商品 `sales_count`
- `/trend` 路由在 `/{order_id}` 之前注册（路由匹配顺序）

**代码文件**: `app/api/orders.py`, `app/models/order.py`, `app/models/order_item.py`

---

### 模块5：行为数据模块 (behaviors)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 导入数据 | POST | `/behaviors/import` | 上传 Excel/CSV，append或replace模式 |
| 获取列表 | GET | `/behaviors` | 分页，支持 user_id/product_id/type/日期 筛选 |
| 转化漏斗 | GET | `/behaviors/funnel` | 浏览→加购→购买 去重用户数统计 |
| 行为趋势 | GET | `/behaviors/trend` | 每日 PV/UV/view_count/cart_count/buy_count |

**设计要点**:
- 行为类型枚举：`view`（浏览）、`cart`（加购）、`favorite`（收藏）、`buy`（购买）
- 导入支持 CSV 和 Excel 格式，使用 pandas 解析
- 漏斗统计使用 `COUNT(DISTINCT user_id)` 确保去重
- 趋势接口返回 31 天连续序列（无数据填0）

**代码文件**: `app/api/behaviors.py`, `app/models/behavior.py`

---

### 模块6：数据分析模块 (analysis)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| RFM分析 | GET | `/analysis/rfm` | RFM分群分布+用户分值列表 |
| 用户聚类 | GET | `/analysis/cluster` | K-Means聚类散点图/雷达图数据 |
| 重新计算 | POST | `/analysis/recalculate` | 触发RFM或聚类重新计算 |
| 关联规则 | GET | `/analysis/association` | Apriori商品关联规则（支持度/置信度/提升度） |
| 用户画像 | GET | `/analysis/profile/{id}` | 用户标签/偏好分类/活跃时段/消费统计 |

**设计要点**:
- **RFM算法**: 使用分位数打分法（pd.qcut），R值反向打分，自动标记"高价值/忠诚/潜力/流失"四群
- **K-Means**: 基于RFM三特征聚类，默认5类，聚类数可调（2-10）
- **Apriori**: 基于订单商品共现，从订单明细中挖掘商品对，计算 support/confidence/lift
- **用户画像**: 综合订单统计、行为时段分析、RFM标签、偏好分类生成360度画像
- 无缓存数据时自动触发首次计算

**代码文件**: `app/api/analysis.py`, `app/services/analysis_service.py`

---

### 模块7：推荐系统模块 (recommend)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 热门推荐 | GET | `/recommend/hot` | 按销量排序，Redis缓存300秒 |
| 关联推荐 | GET | `/recommend/association` | 根据商品ID推荐关联商品 |
| 个性化推荐 | GET | `/recommend/personalized` | 基于用户购买偏好+协同过滤 |
| 刷新缓存 | POST | `/recommend/refresh` | 清除所有推荐缓存 |

**设计要点**:
- **关联推荐**: 复用 Apriori 关联规则，匹配指定商品的前件/后件
- **个性化推荐**: 找出用户偏好分类 → 推荐同分类热销品 → 不够则补充全局热门
- 推荐理由分类："根据您的购买偏好推荐"、"热门商品推荐"

**代码文件**: `app/api/recommend.py`

---

### 模块8：数据驾驶舱模块 (dashboard)

| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 核心指标 | GET | `/dashboard/metrics` | 8项KPI指标，Redis缓存60秒 |
| 销售趋势 | GET | `/dashboard/sales-trend` | 30天销售额/订单量/用户数折线图 |
| 行为趋势 | GET | `/dashboard/user-behavior` | 30天PV/UV/新用户趋势 |
| 商品排行 | GET | `/dashboard/product-ranking` | 按sales/revenue/rating排序 |
| 用户分群 | GET | `/dashboard/user-segments` | RFM四群+新用户分布饼图 |

**设计要点**:
- **转化率**: `购买行为数 / 浏览行为数`，基于行为数据表计算
- **复购率**: 购买≥2次用户数 / 总购买用户数
- **今日数据**: 按 `created_at >= 当日0点` 筛选
- 商品排行支持三种排序：销量、销售额（price × sales_count）、评分

**代码文件**: `app/api/dashboard.py`

---

## 四、数据库表关系

```
users ──1:N── orders ──1:N── order_items ──N:1── products ──N:1── categories
  │                                      │
  │         behaviors (user_id, product_id, type)
  │
  ├──1:1── rfm_scores (user_id PK)
  └──1:1── cluster_results (user_id PK)
```

---

## 五、启动方式

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 确保 MySQL 和 Redis 已启动

# 3. 创建数据库（首次）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS retail CHARACTER SET utf8mb4;"

# 4. 初始化表+管理员账号
python init_db.py

# 5. 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**访问地址**:
- API 服务: http://localhost:8000
- Swagger 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc

**初始账号**:
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |
| 普通用户 | user001 | user123 |

---

## 六、接口汇总表

| 模块 | 数量 | 接口列表 |
|------|------|---------|
| 认证 | 3 | POST /auth/login, GET /auth/me, POST /auth/logout |
| 用户 | 5 | GET/POST /users, GET/PUT/DELETE /users/{id} |
| 商品 | 7 | GET/POST /products, GET/PUT/DELETE /products/{id}, GET /categories, GET /products/hot |
| 订单 | 5 | GET/POST /orders, GET /orders/{id}, PUT /orders/{id}/status, GET /orders/trend |
| 行为 | 4 | POST /behaviors/import, GET /behaviors, GET /behaviors/funnel, GET /behaviors/trend |
| 分析 | 5 | GET /analysis/rfm, GET /analysis/cluster, POST /analysis/recalculate, GET /analysis/association, GET /analysis/profile/{id} |
| 推荐 | 4 | GET /recommend/hot, GET /recommend/association, GET /recommend/personalized, POST /recommend/refresh |
| 驾驶舱 | 5 | GET /dashboard/metrics, GET /dashboard/sales-trend, GET /dashboard/user-behavior, GET /dashboard/product-ranking, GET /dashboard/user-segments |
| **合计** | **38** | |
