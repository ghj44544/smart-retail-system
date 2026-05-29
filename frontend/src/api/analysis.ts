// =====================================================
// src/api/analysis.ts
// 数据分析模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第七章
// 包含: RFM分析、K-Means聚类、重新计算、关联规则、用户画像
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type {
  ApiResponse,
  RFMResult,
  ClusterResult,
  AssociationRule,
  UserProfile,
} from '@/types/api'

// ==================== Mock 开关 ====================
const USE_MOCK = false

// ==================== Mock 数据 ====================

/** Mock RFM 分析结果 - 对应 API 7.1 */
const mockRFMData = (): RFMResult => {
  const segments = ['高价值用户', '忠诚用户', '潜力用户', '新用户', '流失用户']
  const scores = Array.from({ length: 50 }, (_, i) => ({
    user_id: i + 1,
    recency: Math.floor(Math.random() * 5) + 1,
    frequency: Math.floor(Math.random() * 5) + 1,
    monetary: Math.floor(Math.random() * 5) + 1,
    segment: segments[Math.floor(Math.random() * segments.length)],
  }))

  return {
    distribution: {
      labels: segments,
      values: [158, 325, 287, 412, 198],
    },
    scores,
  }
}

/** Mock K-Means 聚类结果 - 对应 API 7.2 */
const mockClusterData = (): ClusterResult => {
  const clusterNames = [
    '高消费活跃用户',
    '中等消费用户',
    '低频低消费用户',
    '新用户群体',
    '流失预警用户',
  ]

  return {
    clusters: clusterNames.map((name, label) => ({
      label,
      name,
      count: [150, 320, 280, 400, 200][label],
      center: [
        [2.5, 8.3, 1250.0],
        [5.0, 4.2, 580.0],
        [8.2, 1.5, 120.0],
        [3.0, 2.0, 200.0],
        [9.0, 0.8, 50.0],
      ][label],
      points: Array.from({ length: 20 }, (_, i) => ({
        user_id: label * 20 + i + 1,
        x: parseFloat((Math.random() * 3 + 1).toFixed(2)),
        y: parseFloat((Math.random() * 8 + 0.5).toFixed(2)),
        z: parseFloat((Math.random() * 1500 + 50).toFixed(2)),
      })),
    })),
  }
}

/** Mock 关联规则 - 对应 API 7.4（商品相关，预留） */
const mockAssociationRules = (): { rules: AssociationRule[] } => {
  const products = [
    { id: 'P1001', name: '无线蓝牙耳机' },
    { id: 'P1002', name: '充电宝' },
    { id: 'P1003', name: '手机壳' },
    { id: 'P1004', name: 'Type-C数据线' },
    { id: 'P1005', name: '智能手表' },
    { id: 'P1006', name: '无线鼠标' },
    { id: 'P1007', name: '机械键盘' },
    { id: 'P1008', name: '平板支架' },
  ]

  const rules: AssociationRule[] = [
    {
      antecedents: ['P1001'],
      consequents: ['P1002'],
      antecedent_names: ['无线蓝牙耳机'],
      consequent_names: ['充电宝'],
      support: 0.052,
      confidence: 0.65,
      lift: 2.3,
    },
    {
      antecedents: ['P1001'],
      consequents: ['P1004'],
      antecedent_names: ['无线蓝牙耳机'],
      consequent_names: ['Type-C数据线'],
      support: 0.048,
      confidence: 0.58,
      lift: 1.9,
    },
    {
      antecedents: ['P1005'],
      consequents: ['P1007'],
      antecedent_names: ['智能手表'],
      consequent_names: ['机械键盘'],
      support: 0.035,
      confidence: 0.52,
      lift: 2.1,
    },
    {
      antecedents: ['P1006', 'P1007'],
      consequents: ['P1008'],
      antecedent_names: ['无线鼠标', '机械键盘'],
      consequent_names: ['平板支架'],
      support: 0.028,
      confidence: 0.61,
      lift: 2.6,
    },
  ]

  return { rules }
}

/** Mock 用户画像 - 对应 API 7.5 */
const mockUserProfile = (userId: number): UserProfile => ({
  user_id: userId,
  nickname: ['张三', '李四', '王五', '赵六'][userId % 4],
  tags: ['高价值用户', '电子产品爱好者', '周末购物', '促销敏感型'],
  prefer_categories: [
    { name: '电子产品', count: 15 },
    { name: '服装', count: 8 },
    { name: '家居用品', count: 5 },
    { name: '食品饮料', count: 3 },
    { name: '运动户外', count: 2 },
  ],
  active_hours: [10, 11, 14, 20, 21, 22],
  avg_order_value: parseFloat((Math.random() * 300 + 50).toFixed(2)),
  total_orders: Math.floor(Math.random() * 30) + 1,
  days_since_last_purchase: Math.floor(Math.random() * 30) + 1,
})

/** 模拟网络延迟 */
const mockDelay = <T>(data: T, delay = 400): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), delay))

// ==================== API 接口函数 ====================

/**
 * 7.1 RFM 用户价值分析
 * 接口: GET /analysis/rfm
 * 描述: 获取 RFM 分析结果（用户分布 + 分数列表）
 *
 * RFM 模型说明:
 *   R(Recency)  - 最近购买时间，值越小越好（1-5分）
 *   F(Frequency) - 购买频率，值越大越好（1-5分）
 *   M(Monetary)  - 消费金额，值越大越好（1-5分）
 *
 * @returns Promise<ApiResponse<RFMResult>>
 */
export const getRFMAnalysis = (): Promise<ApiResponse<RFMResult>> => {
  if (USE_MOCK) {
    return mockDelay({
      code: 200,
      message: 'success',
      data: mockRFMData(),
    })
  }
  return request.get('/analysis/rfm')
}

/**
 * 7.2 K-Means 用户分群
 * 接口: GET /analysis/cluster
 * 描述: 获取 K-Means 聚类结果（用于散点图/雷达图）
 *
 * 聚类说明:
 *   使用 K-Means 算法对用户进行分群（默认 k=5）
 *   基于 RFM 三维特征进行聚类
 *
 * @returns Promise<ApiResponse<ClusterResult>>
 */
export const getClusterAnalysis = (): Promise<ApiResponse<ClusterResult>> => {
  if (USE_MOCK) {
    return mockDelay({
      code: 200,
      message: 'success',
      data: mockClusterData(),
    }, 500)
  }
  return request.get('/analysis/cluster')
}

/**
 * 7.3 触发分析重新计算
 * 接口: POST /analysis/recalculate
 * 描述: 触发后台重新计算 RFM 和聚类结果（耗时操作）
 *
 * @param type - 计算类型: 'rfm' | 'cluster' | 'all'
 * @param clusters - 聚类数量（仅 type='cluster' 时有效）
 * @returns Promise<ApiResponse<null>>
 */
export const recalculateAnalysis = (
  type: 'rfm' | 'cluster' | 'all' = 'all',
  clusters = 5
): Promise<ApiResponse<null>> => {
  if (USE_MOCK) {
    return mockDelay(
      {
        code: 200,
        message: `${type === 'all' ? 'RFM分析和聚类' : type === 'rfm' ? 'RFM分析' : '聚类分析'}重新计算完成`,
        data: null,
      },
      1500
    )
  }
  return request.post('/analysis/recalculate', { type, clusters })
}

/**
 * 7.4 关联规则挖掘（Apriori 算法）
 * 接口: GET /analysis/association
 * 描述: 获取商品关联规则（用于推荐模块）
 *
 * @param minSupport - 最小支持度，默认 0.01
 * @param minConfidence - 最小置信度，默认 0.5
 * @param limit - 返回数量，默认 20
 * @returns Promise<ApiResponse<{rules: AssociationRule[]}>>
 */
export const getAssociationRules = (
  minSupport = 0.01,
  minConfidence = 0.5,
  limit = 20
): Promise<ApiResponse<{ rules: AssociationRule[] }>> => {
  if (USE_MOCK) {
    const data = mockAssociationRules()
    return mockDelay({
      code: 200,
      message: 'success',
      data: { rules: data.rules.slice(0, limit) },
    })
  }
  return request.get('/analysis/association', {
    params: { min_support: minSupport, min_confidence: minConfidence, limit },
  })
}

/**
 * 7.5 用户画像
 * 接口: GET /analysis/profile/{user_id}
 * 描述: 获取指定用户的画像数据（标签、偏好分类、活跃时段等）
 *
 * @param userId - 用户ID
 * @returns Promise<ApiResponse<UserProfile>>
 */
export const getUserProfile = (userId: number): Promise<ApiResponse<UserProfile>> => {
  if (USE_MOCK) {
    return mockDelay({
      code: 200,
      message: 'success',
      data: mockUserProfile(userId),
    })
  }
  return request.get(`/analysis/profile/${userId}`)
}
