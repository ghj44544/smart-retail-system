// =====================================================
// src/api/order.ts
// 订单管理模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第五章
// 包含: 订单列表、详情、创建、状态更新、销售趋势
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type {
  ApiResponse,
  PaginatedData,
  OrderItem,
  OrderDetail,
  OrderQueryParams,
} from '@/types/api'

// ==================== Mock 开关 ====================
const USE_MOCK = false

// ==================== Mock 数据 ====================

const orderStatuses = ['pending', 'paid', 'shipped', 'completed', 'cancelled']
const statusLabels: Record<string, string> = {
  pending: '待支付', paid: '已支付', shipped: '已发货', completed: '已完成', cancelled: '已取消',
}

/** Mock 订单存储 */
let mockOrders: OrderItem[] = Array.from({ length: 80 }, (_, i) => ({
  id: 1001 + i,
  order_no: `ORD2026${String(5).padStart(2, '0')}${String(i + 1).padStart(3, '0')}`,
  user_id: Math.floor(Math.random() * 30) + 1,
  user_name: ['张三', '李四', '王五', '赵六', '小明', '小红', '志明', '春娇', '大伟', '小芳'][Math.floor(Math.random() * 10)],
  total_amount: parseFloat((Math.random() * 2000 + 30).toFixed(2)),
  status: orderStatuses[Math.floor(Math.random() * orderStatuses.length)],
  item_count: Math.floor(Math.random() * 5) + 1,
  created_at: new Date(Date.now() - Math.random() * 60 * 86400000).toISOString(),
}))

/** Mock 订单详情 */
const mockOrderDetail = (orderId: number): OrderDetail => {
  const base = mockOrders.find((o) => o.id === orderId) || mockOrders[0]
  const products = [
    { product_id: 1, product_name: '无线蓝牙耳机 Pro', price: 299.00, quantity: 1 },
    { product_id: 2, product_name: '智能手表 S3', price: 899.00, quantity: 1 },
    { product_id: 4, product_name: '便携充电宝', price: 129.00, quantity: 2 },
    { product_id: 6, product_name: '机械键盘 RGB', price: 299.00, quantity: 1 },
    { product_id: 3, product_name: 'Type-C 数据线', price: 29.90, quantity: 3 },
  ]
  const items = products.slice(0, base.item_count)
  const created = new Date(base.created_at)
  return {
    ...base,
    items: items.map((p, idx) => ({ ...p, quantity: idx === 0 ? Math.ceil((base.total_amount / p.price) * 0.6) : p.quantity })),
    paid_at: base.status !== 'pending' ? new Date(created.getTime() + 3600000).toISOString() : undefined,
    completed_at: base.status === 'completed' ? new Date(created.getTime() + 7 * 86400000).toISOString() : undefined,
  }
}

const mockDelay = <T>(data: T, d = 300): Promise<T> =>
  new Promise((r) => setTimeout(() => r(data), d))

// ==================== API 接口函数 ====================

/**
 * 5.1 获取订单列表
 * 接口: GET /orders
 * 支持: 分页、用户ID筛选、状态筛选、日期范围筛选
 */
export const getOrderList = (
  params: OrderQueryParams
): Promise<ApiResponse<PaginatedData<OrderItem>>> => {
  if (USE_MOCK) {
    const page = params.page || 1
    const pageSize = params.page_size || 10
    let filtered = [...mockOrders]

    if (params.user_id) filtered = filtered.filter((o) => o.user_id === params.user_id)
    if (params.status) filtered = filtered.filter((o) => o.status === params.status)
    if (params.start_date) filtered = filtered.filter((o) => o.created_at >= params.start_date!)
    if (params.end_date) filtered = filtered.filter((o) => o.created_at <= params.end_date! + 'T23:59:59')

    // 按创建时间倒序
    filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    return mockDelay({
      code: 200, message: 'success',
      data: {
        items: filtered.slice((page - 1) * pageSize, page * pageSize),
        total: filtered.length, page, page_size: pageSize,
      },
    })
  }
  return request.get('/orders', { params })
}

/**
 * 5.2 获取订单详情
 * 接口: GET /orders/{order_id}
 */
export const getOrderDetail = (orderId: number): Promise<ApiResponse<OrderDetail>> => {
  if (USE_MOCK) {
    return mockDelay({ code: 200, message: 'success', data: mockOrderDetail(orderId) })
  }
  return request.get(`/orders/${orderId}`)
}

/**
 * 5.3 创建订单
 * 接口: POST /orders
 */
export const createOrder = (
  data: { user_id: number; items: { product_id: number; quantity: number }[] }
): Promise<ApiResponse<OrderItem>> => {
  if (USE_MOCK) {
    const total = Math.random() * 1500 + 50
    const newOrder: OrderItem = {
      id: 1001 + mockOrders.length,
      order_no: `ORD2026${String(new Date().getMonth() + 1).padStart(2, '0')}${String(mockOrders.length + 1).padStart(3, '0')}`,
      user_id: data.user_id, user_name: '当前用户',
      total_amount: parseFloat(total.toFixed(2)),
      status: 'pending', item_count: data.items.reduce((s, i) => s + i.quantity, 0),
      created_at: new Date().toISOString(),
    }
    mockOrders.unshift(newOrder)
    return mockDelay({ code: 200, message: '订单创建成功', data: newOrder })
  }
  return request.post('/orders', data)
}

/**
 * 5.4 更新订单状态
 * 接口: PUT /orders/{order_id}/status
 */
export const updateOrderStatus = (
  orderId: number,
  status: string
): Promise<ApiResponse<OrderItem>> => {
  if (USE_MOCK) {
    const idx = mockOrders.findIndex((o) => o.id === orderId)
    if (idx !== -1) {
      mockOrders[idx].status = status
      return mockDelay({ code: 200, message: '状态更新成功', data: mockOrders[idx] })
    }
    return Promise.reject(new Error('订单不存在'))
  }
  return request.put(`/orders/${orderId}/status`, { status })
}

/**
 * 5.5 获取销售趋势
 * 接口: GET /orders/trend
 */
export const getOrderTrend = (period = 'day', days = 30) => {
  if (USE_MOCK) {
    const dates: string[] = []
    const sales: number[] = []
    const orders: number[] = []
    const bd = new Date(); bd.setDate(bd.getDate() - days + 1)
    for (let i = 0; i < days; i++) {
      const d = new Date(bd); d.setDate(d.getDate() + i)
      dates.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`)
      const wb = (d.getDay() === 0 || d.getDay() === 6) ? 1.5 : 1
      sales.push(Math.round((25000 + Math.random() * 30000) * wb * 100) / 100)
      orders.push(Math.round((70 + Math.random() * 60) * wb))
    }
    return mockDelay({ code: 200, message: 'success', data: { dates, sales, orders } })
  }
  return request.get('/orders/trend', { params: { period, days } })
}
