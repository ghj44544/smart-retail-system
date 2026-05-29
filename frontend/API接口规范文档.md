# 智能零售用户行为分析系统 - 前后端 API 接口规范文档

> **项目**: 智能零售用户行为分析系统  
> **前端技术栈**: Vue3 + Vite + TypeScript + vue-pure-admin + ECharts  
> **后端技术栈**: Python FastAPI + MySQL + Redis + pandas + scikit-learn  
> **接口格式**: RESTful API + JSON  
> **认证方式**: JWT (JSON Web Token)  
> **文档版本**: v1.0  
> **生成日期**: 2026年5月28日

---

## 📌 目录

1. [通用规范](#一通用规范)
2. [认证接口](#二认证接口)
3. [用户管理接口](#三用户管理接口)
4. [商品管理接口](#四商品管理接口)
5. [订单管理接口](#五订单管理接口)
6. [行为数据接口](#六行为数据接口)
7. [数据分析接口](#七数据分析接口)
8. [推荐系统接口](#八推荐系统接口)
9. [数据驾驶舱接口](#九数据驾驶舱接口)
10. [TypeScript 类型定义](#十typescript-类型定义)

---

## 一、通用规范

### 1.1 基础信息

| 项目 | 说明 |
|------|------|
| **Base URL** | `http://localhost:8000/api/v1` |
| **请求方式** | GET / POST / PUT / DELETE |
| **Content-Type** | `application/json` |
| **认证方式** | Header: `Authorization: Bearer <token>` |

### 1.2 统一响应格式

```json
// 成功响应
{
  "code": 200,
  "message": "success",
  "data": { ... }
}

// 分页响应
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 10
  }
}

// 错误响应
{
  "code": 400,
  "message": "错误描述信息",
  "data": null
}
```

### 1.3 错误码定义

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 / Token 过期 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 1.4 认证说明

- 登录后获取 `access_token`，后续请求在 Header 中携带：
  ```
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```
- Token 有效期：24小时
- 使用 Redis 存储 Token 黑名单（登出时加入）

---

## 二、认证接口

### 2.1 用户登录

- **接口**: `POST /auth/login`
- **描述**: 用户登录，获取 JWT Token

**请求参数**:
```json
{
  "username": "string",   // 用户名（必填）
  "password": "string"    // 密码（必填）
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin",
      "nickname": "系统管理员"
    }
  }
}
```

### 2.2 获取当前用户信息

- **接口**: `GET /auth/me`
- **描述**: 获取当前登录用户信息

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "nickname": "系统管理员",
    "avatar": "",
    "created_at": "2026-01-01T00:00:00"
  }
}
```

### 2.3 用户登出

- **接口**: `POST /auth/logout`
- **描述**: 登出系统，Token 加入 Redis 黑名单

**响应示例**:
```json
{
  "code": 200,
  "message": "登出成功",
  "data": null
}
```

---

## 三、用户管理接口

### 3.1 获取用户列表

- **接口**: `GET /users`
- **描述**: 分页获取用户列表，支持搜索和筛选

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认10 |
| keyword | string | 否 | 搜索关键词（用户名/昵称） |
| role | string | 否 | 角色筛选（admin/user） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "username": "user001",
        "nickname": "张三",
        "email": "zhangsan@example.com",
        "phone": "138****1234",
        "role": "user",
        "total_consumption": 1250.50,
        "order_count": 8,
        "last_login": "2026-05-20T10:30:00",
        "created_at": "2025-01-15T08:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 10
  }
}
```

### 3.2 获取用户详情

- **接口**: `GET /users/{user_id}`
- **描述**: 获取指定用户的详细信息

**响应示例**:
```json
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
    "rfm_score": {
      "recency": 2,     // 最近购买：1-5分
      "frequency": 3,    // 购买频率：1-5分
      "monetary": 4      // 消费金额：1-5分
    },
    "cluster_label": 2,  // 聚类标签（0-4）
    "created_at": "2025-01-15T08:00:00"
  }
}
```

### 3.3 创建用户

- **接口**: `POST /users`
- **描述**: 新增用户（管理员操作）

**请求参数**:
```json
{
  "username": "user002",
  "nickname": "李四",
  "email": "lisi@example.com",
  "phone": "13900001111",
  "password": "123456",
  "role": "user"
}
```

### 3.4 更新用户

- **接口**: `PUT /users/{user_id}`
- **描述**: 更新用户信息

### 3.5 删除用户

- **接口**: `DELETE /users/{user_id}`
- **描述**: 删除用户（软删除）

---

## 四、商品管理接口

### 4.1 获取商品列表

- **接口**: `GET /products`
- **描述**: 分页获取商品列表，支持分类筛选和搜索

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| keyword | string | 否 | 搜索关键词 |
| category_id | int | 否 | 分类ID |
| status | string | 否 | 状态（on/off） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "product_no": "P1001",
        "name": "无线蓝牙耳机",
        "category_id": 3,
        "category_name": "电子产品",
        "price": 299.00,
        "stock": 500,
        "status": "on",
        "sales_count": 1200,
        "rating": 4.5,
        "created_at": "2025-03-10T09:00:00"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 10
  }
}
```

### 4.2 获取商品详情

- **接口**: `GET /products/{product_id}`

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "product_no": "P1001",
    "name": "无线蓝牙耳机",
    "description": "高品质无线蓝牙耳机，降噪功能",
    "category_id": 3,
    "category_name": "电子产品",
    "price": 299.00,
    "stock": 500,
    "status": "on",
    "sales_count": 1200,
    "rating": 4.5,
    "related_products": [2, 3, 5],  // 关联商品ID列表
    "created_at": "2025-03-10T09:00:00"
  }
}
```

### 4.3 创建商品

- **接口**: `POST /products`

### 4.4 更新商品

- **接口**: `PUT /products/{product_id}`

### 4.5 删除商品

- **接口**: `DELETE /products/{product_id}`

### 4.6 获取商品分类列表

- **接口**: `GET /categories`

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {"id": 1, "name": "服装", "parent_id": null},
    {"id": 2, "name": "男装", "parent_id": 1},
    {"id": 3, "name": "电子产品", "parent_id": null}
  ]
}
```

### 4.7 获取热门商品排行

- **接口**: `GET /products/hot`
- **描述**: 获取热门商品排行榜（Redis 缓存）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认10 |
| sort_by | string | 否 | 排序字段（sales/cRating） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "product_id": 1,
      "name": "无线蓝牙耳机",
      "sales_count": 1200,
      "rating": 4.5,
      "price": 299.00
    }
  ]
}
```

---

## 五、订单管理接口

### 5.1 获取订单列表

- **接口**: `GET /orders`
- **描述**: 分页获取订单列表

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| user_id | int | 否 | 用户ID筛选 |
| status | string | 否 | 订单状态（pending/paid/shipped/completed/cancelled） |
| start_date | string | 否 | 开始日期（YYYY-MM-DD） |
| end_date | string | 否 | 结束日期（YYYY-MM-DD） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1001,
        "order_no": "ORD20260520001",
        "user_id": 1,
        "user_name": "张三",
        "total_amount": 598.00,
        "status": "completed",
        "item_count": 2,
        "created_at": "2026-05-20T10:30:00"
      }
    ],
    "total": 500,
    "page": 1,
    "page_size": 10
  }
}
```

### 5.2 获取订单详情

- **接口**: `GET /orders/{order_id}`

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1001,
    "order_no": "ORD20260520001",
    "user_id": 1,
    "user_name": "张三",
    "total_amount": 598.00,
    "status": "completed",
    "items": [
      {
        "product_id": 1,
        "product_name": "无线蓝牙耳机",
        "price": 299.00,
        "quantity": 2
      }
    ],
    "created_at": "2026-05-20T10:30:00",
    "paid_at": "2026-05-20T10:31:00",
    "completed_at": "2026-05-22T16:00:00"
  }
}
```

### 5.3 创建订单

- **接口**: `POST /orders`

### 5.4 更新订单状态

- **接口**: `PUT /orders/{order_id}/status`

**请求参数**:
```json
{
  "status": "shipped"
}
```

### 5.5 获取销售趋势

- **接口**: `GET /orders/trend`
- **描述**: 获取销售趋势数据（用于图表展示）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period | string | 否 | 时间粒度（day/week/month），默认day |
| days | int | 否 | 查询天数，默认30 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dates": ["2026-05-01", "2026-05-02", ...],
    "sales": [12500.50, 9800.00, ...],
    "orders": [45, 38, ...]
  }
}
```

---

## 六、行为数据接口

### 6.1 导入行为数据

- **接口**: `POST /behaviors/import`
- **描述**: 批量导入用户行为数据（Excel/CSV）

**请求参数**: `FormData`
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | Excel/CSV 文件 |
| mode | string | 否 | 导入模式（append/replace） |

**响应示例**:
```json
{
  "code": 200,
  "message": "导入成功",
  "data": {
    "imported_count": 5000,
    "skipped_count": 10
  }
}
```

### 6.2 获取行为数据列表

- **接口**: `GET /behaviors`
- **描述**: 分页查询用户行为记录

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码 |
| page_size | int | 否 | 每页数量 |
| user_id | int | 否 | 用户ID |
| product_id | int | 否 | 商品ID |
| behavior_type | string | 否 | 行为类型（view/cart/favorite/buy） |
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "product_id": 100,
        "behavior_type": "view",
        "created_at": "2026-05-20T10:30:00"
      }
    ],
    "total": 10000,
    "page": 1,
    "page_size": 10
  }
}
```

### 6.3 获取行为转化漏斗

- **接口**: `GET /behaviors/funnel`
- **描述**: 获取行为转化漏斗数据（浏览→加购→购买）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | string | 否 | 开始日期 |
| end_date | string | 否 | 结束日期 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "steps": [
      {"name": "浏览", "count": 10000, "rate": 1.0},
      {"name": "加购", "count": 3500, "rate": 0.35},
      {"name": "购买", "count": 1200, "rate": 0.12}
    ]
  }
}
```

### 6.4 获取行为趋势

- **接口**: `GET /behaviors/trend`
- **描述**: 获取用户行为趋势（PV/UV）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| days | int | 否 | 查询天数，默认30 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dates": ["2026-05-01", ...],
    "pv": [1200, 980, ...],
    "uv": [350, 290, ...],
    "view_count": [1000, 850, ...],
    "cart_count": [350, 290, ...],
    "buy_count": [120, 98, ...]
  }
}
```

---

## 七、数据分析接口

### 7.1 RFM 用户价值分析

- **接口**: `GET /analysis/rfm`
- **描述**: 获取 RFM 分析结果

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "distribution": {
      "labels": ["高价值用户", "忠诚用户", "潜力用户", "新用户", "流失用户"],
      "values": [150, 320, 280, 400, 200]
    },
    "scores": [
      {
        "user_id": 1,
        "recency": 2,     // 最近购买天数（分值1-5）
        "frequency": 3,    // 购买频率（分值1-5）
        "monetary": 4,     // 消费金额（分值1-5）
        "segment": "忠诚用户"
      }
    ]
  }
}
```

### 7.2 K-Means 用户分群

- **接口**: `GET /analysis/cluster`
- **描述**: 获取 K-Means 聚类结果（用于散点图/雷达图）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "clusters": [
      {
        "label": 0,
        "name": "高消费活跃用户",
        "count": 150,
        "center": [2.5, 8.3, 1250.0],  // [Recency, Frequency, Monetary]
        "points": [
          {"user_id": 1, "x": 2.1, "y": 7.8, "z": 1100.0}
        ]
      },
      {
        "label": 1,
        "name": "中等消费用户",
        "count": 320,
        "center": [5.0, 4.2, 580.0],
        "points": [...]
      }
    ]
  }
}
```

### 7.3 触发 RFM / 聚类分析

- **接口**: `POST /analysis/recalculate`
- **描述**: 触发后台重新计算 RFM 和聚类结果

**请求参数**:
```json
{
  "type": "rfm",          // rfm / cluster / all
  "clusters": 5           // 聚类数量（仅 cluster 时有效）
}
```

### 7.4 关联规则挖掘（Apriori）

- **接口**: `GET /analysis/association`
- **描述**: 获取商品关联规则

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| min_support | float | 否 | 最小支持度，默认0.01 |
| min_confidence | float | 否 | 最小置信度，默认0.5 |
| limit | int | 否 | 返回数量，默认20 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "rules": [
      {
        "antecedents": ["P1001"],      // 前置商品
        "consequents": ["P1002"],      // 后置商品
        "antecedent_names": ["无线蓝牙耳机"],
        "consequent_names": ["充电宝"],
        "support": 0.05,
        "confidence": 0.65,
        "lift": 2.3
      }
    ]
  }
}
```

### 7.5 用户画像

- **接口**: `GET /analysis/profile/{user_id}`
- **描述**: 获取指定用户的画像数据

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_id": 1,
    "nickname": "张三",
    "tags": ["高价值用户", "电子产品爱好者", "周末购物"],
    "prefer_categories": [
      {"name": "电子产品", "count": 5},
      {"name": "服装", "count": 3}
    ],
    "active_hours": [10, 11, 14, 20],  // 活跃时段
    "avg_order_value": 156.31,
    "total_orders": 8,
    "days_since_last_purchase": 10
  }
}
```

---

## 八、推荐系统接口

### 8.1 热门商品推荐

- **接口**: `GET /recommend/hot`
- **描述**: 获取热门商品推荐列表（Redis 缓存）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认10 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "product_id": 1,
      "name": "无线蓝牙耳机",
      "price": 299.00,
      "sales_count": 1200,
      "rating": 4.5
    }
  ]
}
```

### 8.2 关联规则推荐

- **接口**: `GET /recommend/association`
- **描述**: 根据商品获取关联推荐

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| product_id | int | 是 | 当前商品ID |
| limit | int | 否 | 返回数量，默认10 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "product_id": 2,
      "name": "充电宝",
      "price": 129.00,
      "confidence": 0.65,
      "lift": 2.3
    }
  ]
}
```

### 8.3 个性化推荐

- **接口**: `GET /recommend/personalized`
- **描述**: 获取个性化推荐（基于协同过滤）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | int | 是 | 用户ID |
| limit | int | 否 | 返回数量，默认10 |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "product_id": 5,
      "name": "智能手表",
      "price": 899.00,
      "score": 0.85,       // 推荐分数
      "reason": "根据您的购买历史推荐"
    }
  ]
}
```

### 8.4 刷新推荐结果

- **接口**: `POST /recommend/refresh`
- **描述**: 触发后台重新计算推荐结果

---

## 九、数据驾驶舱接口

### 9.1 获取核心指标

- **接口**: `GET /dashboard/metrics`
- **描述**: 获取数据驾驶舱核心指标（Redis 缓存）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_sales": 1250000.50,    // 销售总额
    "total_orders": 4200,         // 订单总量
    "avg_order_value": 297.62,    // 客单价
    "total_users": 3500,          // 用户总数
    "today_sales": 25800.00,     // 今日销售额
    "today_orders": 86,           // 今日订单量
    "conversion_rate": 0.12,      // 转化率
    "repurchase_rate": 0.35       // 复购率
  }
}
```

### 9.2 获取销售趋势

- **接口**: `GET /dashboard/sales-trend`
- **描述**: 获取销售趋势数据（折线图）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period | string | 否 | 时间粒度（day/week/month） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dates": ["2026-05-01", "2026-05-02", ...],
    "sales": [12500.50, 9800.00, ...],
    "orders": [45, 38, ...],
    "users": [120, 98, ...]
  }
}
```

### 9.3 获取用户行为趋势

- **接口**: `GET /dashboard/user-behavior`
- **描述**: 获取用户行为趋势（用于图表）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "dates": ["2026-05-01", ...],
    "pv": [1200, 980, ...],
    "uv": [350, 290, ...],
    "new_users": [25, 18, ...]
  }
}
```

### 9.4 获取商品表现排行

- **接口**: `GET /dashboard/product-ranking`
- **描述**: 获取商品销售排行（柱状图/饼图）

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| limit | int | 否 | 返回数量，默认10 |
| sort_by | string | 否 | 排序字段（sales/revenue/rating） |

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "products": [
      {"name": "无线蓝牙耳机", "sales": 1200, "revenue": 358800.00},
      {"name": "充电宝", "sales": 980, "revenue": 126420.00}
    ]
  }
}
```

### 9.5 获取用户分群分布

- **接口**: `GET /dashboard/user-segments`
- **描述**: 获取用户分群分布（饼图）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "segments": [
      {"name": "高价值用户", "value": 150},
      {"name": "忠诚用户", "value": 320},
      {"name": "潜力用户", "value": 280},
      {"name": "新用户", "value": 400},
      {"name": "流失用户", "value": 200}
    ]
  }
}
```

---

## 十、TypeScript 类型定义

### 10.1 创建类型文件

创建 `src/types/api.ts`，定义所有接口的类型：

```typescript
// src/types/api.ts

// ==================== 通用类型 ====================

// 统一响应格式
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
}

// 分页请求参数
export interface PaginationParams {
  page?: number;
  page_size?: number;
}

// 分页响应数据
export interface PaginatedData<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

// ==================== 认证相关 ====================

export interface LoginParams {
  username: string;
  password: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserInfo;
}

export interface UserInfo {
  id: number;
  username: string;
  role: 'admin' | 'user';
  nickname: string;
  avatar?: string;
  created_at: string;
}

// ==================== 用户相关 ====================

export interface UserQueryParams extends PaginationParams {
  keyword?: string;
  role?: string;
}

export interface UserItem {
  id: number;
  username: string;
  nickname: string;
  email: string;
  phone: string;
  role: string;
  total_consumption: number;
  order_count: number;
  last_login?: string;
  created_at: string;
}

export interface UserDetail {
  id: number;
  username: string;
  nickname: string;
  email: string;
  phone: string;
  role: string;
  total_consumption: number;
  order_count: number;
  avg_order_value: number;
  last_purchase?: string;
  rfm_score: {
    recency: number;
    frequency: number;
    monetary: number;
  };
  cluster_label: number;
  created_at: string;
}

// ==================== 商品相关 ====================

export interface ProductQueryParams extends PaginationParams {
  keyword?: string;
  category_id?: number;
  status?: 'on' | 'off';
}

export interface ProductItem {
  id: number;
  product_no: string;
  name: string;
  category_id: number;
  category_name: string;
  price: number;
  stock: number;
  status: string;
  sales_count: number;
  rating: number;
  created_at: string;
}

export interface ProductDetail extends ProductItem {
  description: string;
  related_products: number[];
}

export interface CategoryItem {
  id: number;
  name: string;
  parent_id: number | null;
}

// ==================== 订单相关 ====================

export interface OrderQueryParams extends PaginationParams {
  user_id?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export interface OrderItem {
  id: number;
  order_no: string;
  user_id: number;
  user_name: string;
  total_amount: number;
  status: string;
  item_count: number;
  created_at: string;
}

export interface OrderDetail extends OrderItem {
  items: OrderProductItem[];
  paid_at?: string;
  completed_at?: string;
}

export interface OrderProductItem {
  product_id: number;
  product_name: string;
  price: number;
  quantity: number;
}

// ==================== 行为相关 ====================

export interface BehaviorQueryParams extends PaginationParams {
  user_id?: number;
  product_id?: number;
  behavior_type?: 'view' | 'cart' | 'favorite' | 'buy';
  start_date?: string;
  end_date?: string;
}

export interface BehaviorItem {
  id: number;
  user_id: number;
  product_id: number;
  behavior_type: string;
  created_at: string;
}

export interface FunnelData {
  steps: FunnelStep[];
}

export interface FunnelStep {
  name: string;
  count: number;
  rate: number;
}

export interface BehaviorTrendData {
  dates: string[];
  pv: number[];
  uv: number[];
  view_count: number[];
  cart_count: number[];
  buy_count: number[];
}

// ==================== 数据分析相关 ====================

export interface RFMResult {
  distribution: {
    labels: string[];
    values: number[];
  };
  scores: RFMScore[];
}

export interface RFMScore {
  user_id: number;
  recency: number;
  frequency: number;
  monetary: number;
  segment: string;
}

export interface ClusterResult {
  clusters: ClusterItem[];
}

export interface ClusterItem {
  label: number;
  name: string;
  count: number;
  center: number[];
  points: ClusterPoint[];
}

export interface ClusterPoint {
  user_id: number;
  x: number;
  y: number;
  z: number;
}

export interface AssociationRule {
  antecedents: string[];
  consequents: string[];
  antecedent_names: string[];
  consequent_names: string[];
  support: number;
  confidence: number;
  lift: number;
}

export interface UserProfile {
  user_id: number;
  nickname: string;
  tags: string[];
  prefer_categories: { name: string; count: number }[];
  active_hours: number[];
  avg_order_value: number;
  total_orders: number;
  days_since_last_purchase: number;
}

// ==================== 推荐相关 ====================

export interface RecommendItem {
  product_id: number;
  name: string;
  price: number;
  sales_count?: number;
  rating?: number;
  score?: number;
  reason?: string;
}

// ==================== 数据驾驶舱相关 ====================

export interface DashboardMetrics {
  total_sales: number;
  total_orders: number;
  avg_order_value: number;
  total_users: number;
  today_sales: number;
  today_orders: number;
  conversion_rate: number;
  repurchase_rate: number;
}

export interface SalesTrendData {
  dates: string[];
  sales: number[];
  orders: number[];
  users: number[];
}

export interface ProductRankingItem {
  name: string;
  sales: number;
  revenue: number;
}

export interface UserSegmentItem {
  name: string;
  value: number;
}
```

---

## 十一、前端 API 调用示例

### 11.1 创建 API 请求封装

创建 `src/utils/request.ts`：

```typescript
// src/utils/request.ts
import axios, { AxiosInstance } from 'axios';
import { ElMessage } from 'element-plus';
import type { ApiResponse } from '@/types/api';

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    const res = response.data;
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败');
      return Promise.reject(new Error(res.message));
    }
    return res;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，跳转到登录页
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    ElMessage.error(error.message || '网络错误');
    return Promise.reject(error);
  }
);

export default request;
```

### 11.2 创建各模块 API 文件

创建 `src/api/` 目录，按模块拆分：

**示例：用户管理 API** (`src/api/user.ts`)

```typescript
// src/api/user.ts
import request from '@/utils/request';
import type {
  ApiResponse,
  PaginatedData,
  UserItem,
  UserDetail,
  UserQueryParams,
} from '@/types/api';

// 获取用户列表
export const getUserList = (params: UserQueryParams) =>
  request.get<ApiResponse<PaginatedData<UserItem>>>('/users', { params });

// 获取用户详情
export const getUserDetail = (userId: number) =>
  request.get<ApiResponse<UserDetail>>(`/users/${userId}`);

// 创建用户
export const createUser = (data: Partial<UserItem>) =>
  request.post<ApiResponse<UserItem>>('/users', data);

// 更新用户
export const updateUser = (userId: number, data: Partial<UserItem>) =>
  request.put<ApiResponse<UserItem>>(`/users/${userId}`, data);

// 删除用户
export const deleteUser = (userId: number) =>
  request.delete<ApiResponse<null>>(`/users/${userId}`);
```

---

## 十二、Mock 数据方案

在后端未完成时，使用 Mock 数据进行前端开发：

### 12.1 安装 Mock 工具

```bash
pnpm add -D vite-plugin-mock mockjs
```

### 12.2 创建 Mock 文件

创建 `mock/` 目录，按模块创建 Mock 接口：

**示例：用户管理 Mock** (`mock/user.ts`)

```typescript
// mock/user.ts
import { MockMethod } from 'vite-plugin-mock';
import Mock from 'mockjs';

const users = Mock.mock({
  'list|100': [
    {
      'id|+1': 1,
      'username': '@string("lower", 5, 10)',
      'nickname': '@cname',
      'email': '@email',
      'phone': /1[3-9]\d{9}/,
      'role': '@pick(["admin", "user"])',
      'total_consumption': '@float(100, 10000, 2, 2)',
      'order_count': '@integer(1, 50)',
      'last_login': '@datetime',
      'created_at': '@datetime',
    },
  ],
}).list;

export default [
  {
    url: '/api/v1/users',
    method: 'get',
    response: ({ query }) => {
      const page = parseInt(query.page) || 1;
      const pageSize = parseInt(query.page_size) || 10;
      const keyword = query.keyword || '';
      
      let filteredUsers = users;
      if (keyword) {
        filteredUsers = users.filter(
          (u) => u.username.includes(keyword) || u.nickname.includes(keyword)
        );
      }
      
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      
      return {
        code: 200,
        message: 'success',
        data: {
          items: filteredUsers.slice(start, end),
          total: filteredUsers.length,
          page,
          page_size: pageSize,
        },
      };
    },
  },
] as MockMethod[];
```

---

## 附录：接口汇总表

| 模块 | 接口路径 | 方法 | 说明 |
|------|---------|------|------|
| **认证** | `/auth/login` | POST | 登录 |
| | `/auth/me` | GET | 获取当前用户信息 |
| | `/auth/logout` | POST | 登出 |
| **用户** | `/users` | GET | 获取用户列表 |
| | `/users/{id}` | GET | 获取用户详情 |
| | `/users` | POST | 创建用户 |
| | `/users/{id}` | PUT | 更新用户 |
| | `/users/{id}` | DELETE | 删除用户 |
| **商品** | `/products` | GET | 获取商品列表 |
| | `/products/{id}` | GET | 获取商品详情 |
| | `/products` | POST | 创建商品 |
| | `/products/{id}` | PUT | 更新商品 |
| | `/products/{id}` | DELETE | 删除商品 |
| | `/categories` | GET | 获取分类列表 |
| | `/products/hot` | GET | 获取热门商品 |
| **订单** | `/orders` | GET | 获取订单列表 |
| | `/orders/{id}` | GET | 获取订单详情 |
| | `/orders` | POST | 创建订单 |
| | `/orders/{id}/status` | PUT | 更新订单状态 |
| | `/orders/trend` | GET | 获取销售趋势 |
| **行为** | `/behaviors/import` | POST | 导入行为数据 |
| | `/behaviors` | GET | 获取行为列表 |
| | `/behaviors/funnel` | GET | 获取转化漏斗 |
| | `/behaviors/trend` | GET | 获取行为趋势 |
| **分析** | `/analysis/rfm` | GET | RFM 分析 |
| | `/analysis/cluster` | GET | 用户聚类 |
| | `/analysis/recalculate` | POST | 触发重新计算 |
| | `/analysis/association` | GET | 关联规则 |
| | `/analysis/profile/{id}` | GET | 用户画像 |
| **推荐** | `/recommend/hot` | GET | 热门推荐 |
| | `/recommend/association` | GET | 关联推荐 |
| | `/recommend/personalized` | GET | 个性化推荐 |
| | `/recommend/refresh` | POST | 刷新推荐 |
| **驾驶舱** | `/dashboard/metrics` | GET | 核心指标 |
| | `/dashboard/sales-trend` | GET | 销售趋势 |
| | `/dashboard/user-behavior` | GET | 用户行为趋势 |
| | `/dashboard/product-ranking` | GET | 商品排行 |
| | `/dashboard/user-segments` | GET | 用户分群 |

---

**文档结束** | 如有疑问，请联系后端开发团队
