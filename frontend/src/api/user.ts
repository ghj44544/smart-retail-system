// =====================================================
// src/api/user.ts
// 用户管理模块 API 接口层
// 严格遵循 API 接口规范文档 v1.0 第三章
// 包含: 列表查询、详情、创建、更新、删除
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type {
  ApiResponse,
  PaginatedData,
  UserItem,
  UserDetail,
  UserQueryParams,
} from '@/types/api'

// ==================== Mock 开关 ====================
const USE_MOCK = false

// ==================== Mock 数据 ====================

/** Mock 用户存储（模拟后端数据库） */
let mockUsers: UserItem[] = Array.from({ length: 100 }, (_, i) => ({
  id: i + 1,
  username: `user${String(i + 1).padStart(3, '0')}`,
  nickname: [
    '张三', '李四', '王五', '赵六', '孙七', '周八', '吴九', '郑十',
    '小明', '小红', '小刚', '小丽', '大伟', '阿杰', '小芳', '阿强',
    '志明', '春娇', '建国', '秀英', '国栋', '雅文', '浩然', '雨桐',
  ][i % 24] + (i >= 24 ? String(Math.floor(i / 24)) : ''),
  email: `user${i + 1}@example.com`,
  phone: `138${String(10000000 + i).slice(0, 8)}`,
  role: i < 5 ? 'admin' : 'user',
  total_consumption: parseFloat((Math.random() * 8000 + 200).toFixed(2)),
  order_count: Math.floor(Math.random() * 50) + 1,
  last_login: new Date(Date.now() - Math.random() * 30 * 86400000).toISOString(),
  created_at: new Date(2025, 0, 1 + i * 3).toISOString(),
}))

/** Mock 用户详情数据 */
const mockUserDetail = (userId: number): UserDetail => {
  const base = mockUsers.find((u) => u.id === userId) || mockUsers[0]
  return {
    ...base,
    avg_order_value: parseFloat((base.total_consumption / base.order_count).toFixed(2)),
    last_purchase: new Date(Date.now() - Math.random() * 15 * 86400000).toISOString(),
    rfm_score: {
      recency: Math.floor(Math.random() * 5) + 1,
      frequency: Math.floor(Math.random() * 5) + 1,
      monetary: Math.floor(Math.random() * 5) + 1,
    },
    cluster_label: Math.floor(Math.random() * 5),
  }
}

/** 模拟网络延迟 */
const mockDelay = <T>(data: T, delay = 300): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), delay))

// ==================== API 接口函数 ====================

/**
 * 3.1 获取用户列表
 * 接口: GET /users
 * 描述: 分页获取用户列表，支持搜索和角色筛选
 *
 * @param params - 查询参数 { page, page_size, keyword, role }
 * @returns Promise<ApiResponse<PaginatedData<UserItem>>>
 */
export const getUserList = (
  params: UserQueryParams
): Promise<ApiResponse<PaginatedData<UserItem>>> => {
  if (USE_MOCK) {
    const page = params.page || 1
    const pageSize = params.page_size || 10
    const keyword = params.keyword || ''
    const role = params.role || ''

    // 按关键词和角色筛选
    let filtered = [...mockUsers]
    if (keyword) {
      const kw = keyword.toLowerCase()
      filtered = filtered.filter(
        (u) => u.username.toLowerCase().includes(kw) || u.nickname.includes(kw)
      )
    }
    if (role) {
      filtered = filtered.filter((u) => u.role === role)
    }

    const total = filtered.length
    const items = filtered.slice((page - 1) * pageSize, page * pageSize)

    return mockDelay({
      code: 200,
      message: 'success',
      data: { items, total, page, page_size: pageSize },
    })
  }
  return request.get('/users', { params })
}

/**
 * 3.2 获取用户详情
 * 接口: GET /users/{user_id}
 * 描述: 获取指定用户的详细信息（含 RFM 评分和聚类标签）
 *
 * @param userId - 用户ID
 * @returns Promise<ApiResponse<UserDetail>>
 */
export const getUserDetail = (userId: number): Promise<ApiResponse<UserDetail>> => {
  if (USE_MOCK) {
    return mockDelay({
      code: 200,
      message: 'success',
      data: mockUserDetail(userId),
    })
  }
  return request.get(`/users/${userId}`)
}

/**
 * 3.3 创建用户
 * 接口: POST /users
 * 描述: 新增用户（管理员操作）
 *
 * @param data - 用户信息 { username, nickname, email, phone, password, role }
 * @returns Promise<ApiResponse<UserItem>>
 */
export const createUser = (
  data: Partial<UserItem> & { password?: string }
): Promise<ApiResponse<UserItem>> => {
  if (USE_MOCK) {
    const newUser: UserItem = {
      id: mockUsers.length + 1,
      username: data.username || '',
      nickname: data.nickname || '',
      email: data.email || '',
      phone: data.phone || '',
      role: data.role || 'user',
      total_consumption: 0,
      order_count: 0,
      last_login: undefined,
      created_at: new Date().toISOString(),
    }
    mockUsers.unshift(newUser)
    return mockDelay({
      code: 200,
      message: '创建成功',
      data: newUser,
    })
  }
  return request.post('/users', data)
}

/**
 * 3.4 更新用户
 * 接口: PUT /users/{user_id}
 * 描述: 更新用户信息
 *
 * @param userId - 用户ID
 * @param data - 要更新的字段
 * @returns Promise<ApiResponse<UserItem>>
 */
export const updateUser = (
  userId: number,
  data: Partial<UserItem>
): Promise<ApiResponse<UserItem>> => {
  if (USE_MOCK) {
    const index = mockUsers.findIndex((u) => u.id === userId)
    if (index !== -1) {
      mockUsers[index] = { ...mockUsers[index], ...data }
      return mockDelay({
        code: 200,
        message: '更新成功',
        data: mockUsers[index],
      })
    }
    return Promise.reject(new Error('用户不存在'))
  }
  return request.put(`/users/${userId}`, data)
}

/**
 * 3.5 删除用户
 * 接口: DELETE /users/{user_id}
 * 描述: 删除用户（软删除）
 *
 * @param userId - 用户ID
 * @returns Promise<ApiResponse<null>>
 */
export const deleteUser = (userId: number): Promise<ApiResponse<null>> => {
  if (USE_MOCK) {
    mockUsers = mockUsers.filter((u) => u.id !== userId)
    return mockDelay({
      code: 200,
      message: '删除成功',
      data: null,
    })
  }
  return request.delete(`/users/${userId}`)
}
