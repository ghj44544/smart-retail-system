// =====================================================
// src/api/behavior.ts
// 行为分析模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第六章
// 包含: 数据导入、行为列表、转化漏斗、行为趋势
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type {
  ApiResponse,
  PaginatedData,
  BehaviorItem,
  BehaviorQueryParams,
  FunnelData,
  BehaviorTrendData,
} from '@/types/api'

const USE_MOCK = false

// ==================== Mock 数据 ====================

const behaviorTypes = ['view', 'cart', 'favorite', 'buy']
const typeLabels: Record<string, string> = { view: '浏览', cart: '加购', favorite: '收藏', buy: '购买' }

let mockBehaviors: BehaviorItem[] = Array.from({ length: 300 }, (_, i) => ({
  id: i + 1,
  user_id: Math.floor(Math.random() * 50) + 1,
  product_id: Math.floor(Math.random() * 34) + 1,
  behavior_type: behaviorTypes[Math.floor(Math.random() * behaviorTypes.length)],
  created_at: new Date(Date.now() - Math.random() * 30 * 86400000).toISOString(),
}))

const mockDelay = <T>(data: T, d = 300): Promise<T> =>
  new Promise((r) => setTimeout(() => r(data), d))

// ==================== API 接口 ====================

/**
 * 6.1 导入行为数据
 * 接口: POST /behaviors/import
 * 描述: 批量导入用户行为数据（Excel/CSV 文件上传）
 * 请求: FormData { file, mode?: 'append'|'replace' }
 */
export const importBehaviors = (formData: FormData): Promise<ApiResponse<{ imported_count: number; skipped_count: number }>> => {
  if (USE_MOCK) {
    const count = Math.floor(Math.random() * 5000) + 1000
    return mockDelay({ code: 200, message: '导入成功', data: { imported_count: count, skipped_count: Math.floor(Math.random() * 20) } }, 2000)
  }
  return request.post('/behaviors/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

/**
 * 6.2 获取行为数据列表
 * 接口: GET /behaviors
 * 支持: 分页 + user_id + product_id + behavior_type + 日期范围
 */
export const getBehaviorList = (params: BehaviorQueryParams): Promise<ApiResponse<PaginatedData<BehaviorItem>>> => {
  if (USE_MOCK) {
    const page = params.page || 1
    const ps = params.page_size || 10
    let filtered = [...mockBehaviors]
    if (params.user_id) filtered = filtered.filter((b) => b.user_id === params.user_id)
    if (params.product_id) filtered = filtered.filter((b) => b.product_id === params.product_id)
    if (params.behavior_type) filtered = filtered.filter((b) => b.behavior_type === params.behavior_type)
    if (params.start_date) filtered = filtered.filter((b) => b.created_at >= params.start_date!)
    if (params.end_date) filtered = filtered.filter((b) => b.created_at <= params.end_date! + 'T23:59:59')
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    return mockDelay({ code: 200, message: 'success', data: { items: filtered.slice((page - 1) * ps, page * ps), total: filtered.length, page, page_size: ps } })
  }
  return request.get('/behaviors', { params })
}

/**
 * 6.3 获取行为转化漏斗
 * 接口: GET /behaviors/funnel
 * 描述: 浏览→加购→购买 转化漏斗数据
 */
export const getBehaviorFunnel = (startDate?: string, endDate?: string): Promise<ApiResponse<FunnelData>> => {
  if (USE_MOCK) {
    const viewCount = Math.floor(Math.random() * 20000) + 15000
    const cartCount = Math.floor(viewCount * (0.25 + Math.random() * 0.2))
    const buyCount = Math.floor(cartCount * (0.25 + Math.random() * 0.2))
    return mockDelay({
      code: 200, message: 'success',
      data: {
        steps: [
          { name: '浏览商品', count: viewCount, rate: 1.0 },
          { name: '加入购物车', count: cartCount, rate: parseFloat((cartCount / viewCount).toFixed(3)) },
          { name: '完成购买', count: buyCount, rate: parseFloat((buyCount / viewCount).toFixed(3)) },
        ],
      },
    })
  }
  return request.get('/behaviors/funnel', { params: { start_date: startDate, end_date: endDate } })
}

/**
 * 6.4 获取行为趋势
 * 接口: GET /behaviors/trend
 * 描述: 用户行为趋势（PV/UV/浏览/加购/购买）
 */
export const getBehaviorTrend = (days = 30): Promise<ApiResponse<BehaviorTrendData>> => {
  if (USE_MOCK) {
    const dates: string[] = []; const pv: number[] = []; const uv: number[] = []
    const view: number[] = []; const cart: number[] = []; const buy: number[] = []
    const bd = new Date(); bd.setDate(bd.getDate() - days + 1)
    for (let i = 0; i < days; i++) {
      const d = new Date(bd); d.setDate(d.getDate() + i)
      dates.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`)
      const bpv = Math.round(1200 + Math.random() * 800)
      const buv = Math.round(350 + Math.random() * 250)
      pv.push(bpv); uv.push(buv)
      view.push(Math.round(bpv * 0.85)); cart.push(Math.round(buv * 0.30)); buy.push(Math.round(buv * 0.12))
    }
    return mockDelay({ code: 200, message: 'success', data: { dates, pv, uv, view_count: view, cart_count: cart, buy_count: buy } })
  }
  return request.get('/behaviors/trend', { params: { days } })
}
