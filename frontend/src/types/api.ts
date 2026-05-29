// =====================================================
// src/types/api.ts
// 智能零售用户行为分析系统 - TypeScript 类型定义
// 严格遵循 API 接口规范文档 v1.0
// Base URL: http://localhost:8000/api/v1
// 认证方式: JWT Bearer Token
// =====================================================

// ==================== 通用类型 ====================

/**
 * 统一响应格式 - 后端返回的所有数据都遵循此结构
 * @template T - data 字段的具体类型
 */
export interface ApiResponse<T = any> {
  code: number // 状态码: 200=成功 400=参数错误 401=未认证 403=无权限 404=不存在 500=服务器错误
  message: string // 提示信息
  data: T // 响应数据
}

/**
 * 分页请求参数 - 用于所有需要分页的列表查询接口
 */
export interface PaginationParams {
  page?: number // 页码，从1开始，默认1
  page_size?: number // 每页数量，默认10
}

/**
 * 分页响应数据 - 后端返回的分页列表统一使用此结构
 * @template T - items 列表中每一项的类型
 */
export interface PaginatedData<T> {
  items: T[] // 当前页数据列表
  total: number // 数据总数
  page: number // 当前页码
  page_size: number // 每页数量
}

// ==================== 认证相关 ====================
// 对应 API 文档第二章：认证接口

/**
 * 登录请求参数
 * 接口: POST /auth/login
 */
export interface LoginParams {
  username: string // 用户名（必填）
  password: string // 密码（必填）
}

/**
 * 登录成功后返回的数据结构
 * 对应 API 文档 2.1 用户登录
 */
export interface LoginResult {
  access_token: string // JWT 令牌，后续请求需在 Header 中携带: Authorization: Bearer <token>
  token_type: string // 令牌类型，固定值 "bearer"
  expires_in: number // 令牌有效期（秒），24小时 = 86400
  user: UserInfo // 登录用户的基本信息
}

/**
 * 当前登录用户信息
 * 对应 API 文档 2.2 获取当前用户信息
 */
export interface UserInfo {
  id: number // 用户ID
  username: string // 用户名
  role: 'admin' | 'user' // 角色: admin=管理员 user=普通用户
  nickname: string // 昵称/显示名称
  avatar?: string // 头像URL（可选）
  created_at: string // 创建时间 ISO 8601 格式
}

// ==================== 用户相关 ====================
// 对应 API 文档第三章：用户管理接口

/**
 * 用户列表查询参数
 * 接口: GET /users
 */
export interface UserQueryParams extends PaginationParams {
  keyword?: string // 搜索关键词，匹配用户名或昵称
  role?: string // 按角色筛选: admin | user
}

/**
 * 用户列表项
 * 对应 API 文档 3.1 获取用户列表
 */
export interface UserItem {
  id: number // 用户ID
  username: string // 用户名
  nickname: string // 昵称
  email: string // 邮箱
  phone: string // 手机号（脱敏显示）
  role: string // 角色
  total_consumption: number // 累计消费金额
  order_count: number // 订单数量
  last_login?: string // 最后登录时间
  created_at: string // 注册时间
}

/**
 * 用户详情
 * 对应 API 文档 3.2 获取用户详情
 */
export interface UserDetail {
  id: number // 用户ID
  username: string // 用户名
  nickname: string // 昵称
  email: string // 邮箱
  phone: string // 手机号
  role: string // 角色
  total_consumption: number // 累计消费金额
  order_count: number // 订单数量
  avg_order_value: number // 平均客单价
  last_purchase?: string // 最近购买时间
  rfm_score: {
    // RFM 评分
    recency: number // 最近购买（R值）：1-5分
    frequency: number // 购买频率（F值）：1-5分
    monetary: number // 消费金额（M值）：1-5分
  }
  cluster_label: number // K-Means 聚类标签（0-4）
  created_at: string // 注册时间
}

// ==================== 商品相关 ====================
// 对应 API 文档第四章：商品管理接口

export interface ProductQueryParams extends PaginationParams {
  keyword?: string
  category_id?: number
  status?: 'on' | 'off'
}

export interface ProductItem {
  id: number
  product_no: string
  name: string
  category_id: number
  category_name: string
  price: number
  stock: number
  status: string
  sales_count: number
  rating: number
  created_at: string
}

export interface ProductDetail extends ProductItem {
  description: string
  related_products: number[]
}

export interface CategoryItem {
  id: number
  name: string
  parent_id: number | null
}

// ==================== 订单相关 ====================
// 对应 API 文档第五章：订单管理接口

export interface OrderQueryParams extends PaginationParams {
  user_id?: number
  status?: string
  start_date?: string
  end_date?: string
}

export interface OrderItem {
  id: number
  order_no: string
  user_id: number
  user_name: string
  total_amount: number
  status: string
  item_count: number
  created_at: string
}

export interface OrderDetail extends OrderItem {
  items: OrderProductItem[]
  paid_at?: string
  completed_at?: string
}

export interface OrderProductItem {
  product_id: number
  product_name: string
  price: number
  quantity: number
}

// ==================== 行为相关 ====================
// 对应 API 文档第六章：行为数据接口

export interface BehaviorQueryParams extends PaginationParams {
  user_id?: number
  product_id?: number
  behavior_type?: 'view' | 'cart' | 'favorite' | 'buy'
  start_date?: string
  end_date?: string
}

export interface BehaviorItem {
  id: number
  user_id: number
  product_id: number
  behavior_type: string
  created_at: string
}

export interface FunnelData {
  steps: FunnelStep[]
}

export interface FunnelStep {
  name: string
  count: number
  rate: number
}

export interface BehaviorTrendData {
  dates: string[]
  pv: number[]
  uv: number[]
  view_count: number[]
  cart_count: number[]
  buy_count: number[]
}

// ==================== 数据分析相关 ====================
// 对应 API 文档第七章：数据分析接口

export interface RFMResult {
  distribution: {
    labels: string[]
    values: number[]
  }
  scores: RFMScore[]
}

export interface RFMScore {
  user_id: number
  recency: number
  frequency: number
  monetary: number
  segment: string
}

export interface ClusterResult {
  clusters: ClusterItem[]
}

export interface ClusterItem {
  label: number
  name: string
  count: number
  center: number[]
  points: ClusterPoint[]
}

export interface ClusterPoint {
  user_id: number
  x: number
  y: number
  z: number
}

export interface AssociationRule {
  antecedents: string[]
  consequents: string[]
  antecedent_names: string[]
  consequent_names: string[]
  support: number
  confidence: number
  lift: number
}

export interface UserProfile {
  user_id: number
  nickname: string
  tags: string[]
  prefer_categories: { name: string; count: number }[]
  active_hours: number[]
  avg_order_value: number
  total_orders: number
  days_since_last_purchase: number
}

// ==================== 推荐相关 ====================
// 对应 API 文档第八章：推荐系统接口

export interface RecommendItem {
  product_id: number
  name: string
  price: number
  sales_count?: number
  rating?: number
  score?: number
  reason?: string
}

// ==================== 数据驾驶舱相关 ====================
// 对应 API 文档第九章：数据驾驶舱接口

export interface DashboardMetrics {
  total_sales: number
  total_orders: number
  avg_order_value: number
  total_users: number
  today_sales: number
  today_orders: number
  conversion_rate: number
  repurchase_rate: number
}

export interface SalesTrendData {
  dates: string[]
  sales: number[]
  orders: number[]
  users: number[]
}

export interface ProductRankingItem {
  name: string
  sales: number
  revenue: number
}

export interface UserSegmentItem {
  name: string
  value: number
}
