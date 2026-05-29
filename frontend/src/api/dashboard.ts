// =====================================================
// src/api/dashboard.ts
// 数据驾驶舱模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第九章
// 包含五个接口: 核心指标、销售趋势、用户行为趋势、商品排行、用户分群
// 当前使用 Mock 数据，后端就绪后删除 Mock 部分即可
// =====================================================

import request from '@/utils/request'
import type {
  ApiResponse,
  DashboardMetrics,
  SalesTrendData,
  BehaviorTrendData,
  ProductRankingItem,
  UserSegmentItem,
} from '@/types/api'

// ==================== Mock 开关 ====================
// 后端就绪后，将此值改为 false 即可切换到真实接口
const USE_MOCK = false

// ==================== Mock 数据生成 ====================

/** 生成 Mock 核心指标数据 */
const mockMetrics = (): DashboardMetrics => ({
  total_sales: 1256250.50,
  total_orders: 4286,
  avg_order_value: 293.07,
  total_users: 3520,
  today_sales: 25800.00,
  today_orders: 86,
  conversion_rate: 0.128,
  repurchase_rate: 0.356,
})

/** 生成 Mock 销售趋势数据（最近30天） */
const mockSalesTrend = (): SalesTrendData => {
  const dates: string[] = []
  const sales: number[] = []
  const orders: number[] = []
  const users: number[] = []

  const baseDate = new Date()
  baseDate.setDate(baseDate.getDate() - 29)

  for (let i = 0; i < 30; i++) {
    const d = new Date(baseDate)
    d.setDate(d.getDate() + i)
    dates.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`)

    // 模拟周末销量较高
    const dayOfWeek = d.getDay()
    const weekendBoost = (dayOfWeek === 0 || dayOfWeek === 6) ? 1.5 : 1

    sales.push(Math.round((25000 + Math.random() * 35000) * weekendBoost * 100) / 100)
    orders.push(Math.round((80 + Math.random() * 70) * weekendBoost))
    users.push(Math.round((100 + Math.random() * 80) * weekendBoost))
  }

  return { dates, sales, orders, users }
}

/** 生成 Mock 用户行为趋势数据（最近30天） */
const mockUserBehavior = (): BehaviorTrendData => {
  const dates: string[] = []
  const pv: number[] = []
  const uv: number[] = []
  const view_count: number[] = []
  const cart_count: number[] = []
  const buy_count: number[] = []

  const baseDate = new Date()
  baseDate.setDate(baseDate.getDate() - 29)

  for (let i = 0; i < 30; i++) {
    const d = new Date(baseDate)
    d.setDate(d.getDate() + i)
    dates.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`)

    const basePv = 1200 + Math.random() * 800
    const baseUv = 350 + Math.random() * 250
    pv.push(Math.round(basePv))
    uv.push(Math.round(baseUv))
    view_count.push(Math.round(basePv * 0.85))
    cart_count.push(Math.round(baseUv * 0.30))
    buy_count.push(Math.round(baseUv * 0.12))
  }

  return { dates, pv, uv, view_count, cart_count, buy_count }
}

/** 生成 Mock 商品表现排行数据 */
const mockProductRanking = (): { products: ProductRankingItem[] } => ({
  products: [
    { name: '无线蓝牙耳机 Pro', sales: 1256, revenue: 377428.00 },
    { name: '智能手表 S3', sales: 1089, revenue: 979011.00 },
    { name: '便携充电宝 20000mAh', sales: 987, revenue: 127323.00 },
    { name: 'Type-C 数据线', sales: 856, revenue: 25680.00 },
    { name: '降噪耳机罩', sales: 743, revenue: 222157.00 },
    { name: '手机壳 全系列', sales: 689, revenue: 24115.00 },
    { name: '无线鼠标', sales: 612, revenue: 79560.00 },
    { name: '机械键盘 RGB', sales: 534, revenue: 160200.00 },
    { name: '平板支架', sales: 478, revenue: 33460.00 },
    { name: 'USB 集线器', sales: 423, revenue: 29610.00 },
  ],
})

/** 生成 Mock 用户分群分布数据 */
const mockUserSegments = (): { segments: UserSegmentItem[] } => ({
  segments: [
    { name: '高价值用户', value: 158 },
    { name: '忠诚用户', value: 325 },
    { name: '潜力用户', value: 287 },
    { name: '新用户', value: 412 },
    { name: '流失用户', value: 198 },
  ],
})

// ==================== 延迟模拟函数 ====================

/** 模拟网络延迟（后端就绪后可删除） */
const mockDelay = <T>(data: T, delay = 300): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), delay))

// ==================== API 接口函数 ====================

/**
 * 9.1 获取核心指标
 * 接口: GET /dashboard/metrics
 * 描述: 获取数据驾驶舱核心指标（Redis 缓存）
 *
 * @returns Promise<ApiResponse<DashboardMetrics>>
 */
export const getMetrics = async (): Promise<ApiResponse<DashboardMetrics>> => {
  // 后端就绪后，删除 if/else 分支，使用: return request.get('/dashboard/metrics')
  if (USE_MOCK) {
    const data = {
      code: 200,
      message: 'success',
      data: mockMetrics(),
    }
    return mockDelay(data)
  }
  return request.get('/dashboard/metrics')
}

/**
 * 9.2 获取销售趋势
 * 接口: GET /dashboard/sales-trend
 * 描述: 获取销售趋势数据（折线图）
 *
 * @param period - 时间粒度（day/week/month），默认 day
 * @returns Promise<ApiResponse<SalesTrendData>>
 */
export const getSalesTrend = async (period = 'day'): Promise<ApiResponse<SalesTrendData>> => {
  if (USE_MOCK) {
    const data = {
      code: 200,
      message: 'success',
      data: mockSalesTrend(),
    }
    return mockDelay(data, 400)
  }
  return request.get('/dashboard/sales-trend', { params: { period } })
}

/**
 * 9.3 获取用户行为趋势
 * 接口: GET /dashboard/user-behavior
 * 描述: 获取用户行为趋势（PV/UV/新增用户图表）
 *
 * @returns Promise<ApiResponse<{dates, pv, uv, new_users}>
 */
export const getUserBehavior = async (): Promise<ApiResponse<BehaviorTrendData>> => {
  if (USE_MOCK) {
    const data = {
      code: 200,
      message: 'success',
      data: mockUserBehavior(),
    }
    return mockDelay(data, 400)
  }
  return request.get('/dashboard/user-behavior')
}

/**
 * 9.4 获取商品表现排行
 * 接口: GET /dashboard/product-ranking
 * 描述: 获取商品销售排行（柱状图/饼图）
 *
 * @param limit - 返回数量，默认10
 * @param sortBy - 排序字段（sales/revenue/rating），默认 sales
 * @returns Promise<ApiResponse<{products: ProductRankingItem[]}>
 */
export const getProductRanking = async (
  limit = 10,
  sortBy = 'sales'
): Promise<ApiResponse<{ products: ProductRankingItem[] }>> => {
  if (USE_MOCK) {
    const fullData = mockProductRanking()
    const data = {
      code: 200,
      message: 'success',
      data: {
        products: fullData.products.slice(0, limit),
      },
    }
    return mockDelay(data, 350)
  }
  return request.get('/dashboard/product-ranking', { params: { limit, sort_by: sortBy } })
}

/**
 * 9.5 获取用户分群分布
 * 接口: GET /dashboard/user-segments
 * 描述: 获取用户分群分布（饼图）
 *
 * @returns Promise<ApiResponse<{segments: UserSegmentItem[]}>
 */
export const getUserSegments = async (): Promise<ApiResponse<{ segments: UserSegmentItem[] }>> => {
  if (USE_MOCK) {
    const data = {
      code: 200,
      message: 'success',
      data: mockUserSegments(),
    }
    return mockDelay(data, 300)
  }
  return request.get('/dashboard/user-segments')
}
