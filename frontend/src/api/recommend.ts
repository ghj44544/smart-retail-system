// =====================================================
// src/api/recommend.ts
// 推荐系统模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第八章
// 包含: 热门推荐、关联推荐、个性化推荐、刷新推荐
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type { ApiResponse, RecommendItem } from '@/types/api'

const USE_MOCK = false

// ==================== Mock 数据 ====================

const hotProducts: RecommendItem[] = [
  { product_id: 1, name: '无线蓝牙耳机 Pro', price: 299.00, sales_count: 1256, rating: 4.8 },
  { product_id: 6, name: '机械键盘 RGB', price: 299.00, sales_count: 1089, rating: 4.7 },
  { product_id: 2, name: '智能手表 S3', price: 899.00, sales_count: 987, rating: 4.6 },
  { product_id: 4, name: '便携充电宝 20000mAh', price: 129.00, sales_count: 856, rating: 4.5 },
  { product_id: 13, name: '运动跑鞋', price: 499.00, sales_count: 743, rating: 4.4 },
  { product_id: 3, name: 'Type-C 数据线 1m', price: 29.90, sales_count: 689, rating: 4.3 },
  { product_id: 5, name: '降噪耳机罩', price: 399.00, sales_count: 612, rating: 4.5 },
  { product_id: 10, name: '高清摄像头 1080P', price: 249.00, sales_count: 534, rating: 4.2 },
  { product_id: 16, name: '智能台灯', price: 159.00, sales_count: 478, rating: 4.6 },
  { product_id: 7, name: '无线鼠标', price: 129.00, sales_count: 423, rating: 4.1 },
]

const associationRecs: Record<number, RecommendItem[]> = {
  1: [
    { product_id: 4, name: '便携充电宝 20000mAh', price: 129.00, confidence: 0.65, lift: 2.3 },
    { product_id: 3, name: 'Type-C 数据线 1m', price: 29.90, confidence: 0.58, lift: 1.9 },
    { product_id: 8, name: 'USB 集线器 7口', price: 69.00, confidence: 0.42, lift: 1.6 },
  ],
  2: [
    { product_id: 6, name: '机械键盘 RGB', price: 299.00, confidence: 0.52, lift: 2.1 },
    { product_id: 7, name: '无线鼠标', price: 129.00, confidence: 0.48, lift: 1.8 },
    { product_id: 9, name: '平板电脑支架', price: 79.00, confidence: 0.38, lift: 1.5 },
  ],
  6: [
    { product_id: 7, name: '无线鼠标', price: 129.00, confidence: 0.78, lift: 3.1 },
    { product_id: 9, name: '平板电脑支架', price: 79.00, confidence: 0.61, lift: 2.4 },
    { product_id: 2, name: '智能手表 S3', price: 899.00, confidence: 0.35, lift: 1.4 },
  ],
}

const personalizedRecs: Record<number, RecommendItem[]> = {
  1: [
    { product_id: 6, name: '机械键盘 RGB', price: 299.00, score: 0.92, reason: '您浏览过类似商品' },
    { product_id: 10, name: '高清摄像头 1080P', price: 249.00, score: 0.87, reason: '与您购买过的商品相关' },
    { product_id: 2, name: '智能手表 S3', price: 899.00, score: 0.81, reason: '根据您的消费偏好推荐' },
    { product_id: 16, name: '智能台灯', price: 159.00, score: 0.75, reason: '同类用户也购买了' },
  ],
  5: [
    { product_id: 13, name: '运动跑鞋', price: 499.00, score: 0.89, reason: '与您浏览过的商品相关' },
    { product_id: 25, name: '瑜伽垫', price: 79.00, score: 0.83, reason: '根据您的消费偏好推荐' },
    { product_id: 27, name: '登山背包', price: 399.00, score: 0.76, reason: '同类用户也购买了' },
  ],
}

const defaultPersonalized: RecommendItem[] = [
  { product_id: 1, name: '无线蓝牙耳机 Pro', price: 299.00, score: 0.85, reason: '热门商品推荐' },
  { product_id: 4, name: '便携充电宝 20000mAh', price: 129.00, score: 0.78, reason: '高评分商品推荐' },
  { product_id: 13, name: '运动跑鞋', price: 499.00, score: 0.72, reason: '新上架商品推荐' },
]

const mockDelay = <T>(data: T, d = 300): Promise<T> =>
  new Promise((r) => setTimeout(() => r(data), d))

// ==================== API 接口函数 ====================

/**
 * 8.1 热门商品推荐
 * 接口: GET /recommend/hot
 * 描述: 获取热门商品推荐列表（Redis 缓存）
 */
export const getHotRecommend = (limit = 10): Promise<ApiResponse<RecommendItem[]>> => {
  if (USE_MOCK) return mockDelay({ code: 200, message: 'success', data: hotProducts.slice(0, limit) })
  return request.get('/recommend/hot', { params: { limit } })
}

/**
 * 8.2 关联规则推荐
 * 接口: GET /recommend/association
 * 描述: 根据指定商品获取关联推荐（基于 Apriori 算法）
 */
export const getAssociationRecommend = (
  productId: number,
  limit = 10
): Promise<ApiResponse<RecommendItem[]>> => {
  if (USE_MOCK) {
    const recs = associationRecs[productId] || Object.values(associationRecs).flat().slice(0, 3).map((r, i) => ({ ...r, product_id: r.product_id + i }))
    return mockDelay({ code: 200, message: 'success', data: recs.slice(0, limit) })
  }
  return request.get('/recommend/association', { params: { product_id: productId, limit } })
}

/**
 * 8.3 个性化推荐
 * 接口: GET /recommend/personalized
 * 描述: 获取指定用户的个性化推荐（协同过滤/基于内容）
 */
export const getPersonalizedRecommend = (
  userId: number,
  limit = 10
): Promise<ApiResponse<RecommendItem[]>> => {
  if (USE_MOCK) {
    const recs = personalizedRecs[userId] || defaultPersonalized
    return mockDelay({ code: 200, message: 'success', data: recs.slice(0, limit) })
  }
  return request.get('/recommend/personalized', { params: { user_id: userId, limit } })
}

/**
 * 8.4 刷新推荐结果
 * 接口: POST /recommend/refresh
 * 描述: 触发后台重新计算所有推荐结果
 */
export const refreshRecommend = (): Promise<ApiResponse<null>> => {
  if (USE_MOCK) {
    return mockDelay({ code: 200, message: '推荐结果已重新计算', data: null }, 1500)
  }
  return request.post('/recommend/refresh')
}
