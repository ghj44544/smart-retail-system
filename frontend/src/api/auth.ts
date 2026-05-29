// =====================================================
// src/api/auth.ts
// 认证模块 API 接口层 - 严格遵循 API 接口规范文档 v1.0 第二章
// 包含三个接口: 登录、获取当前用户信息、登出
// 当前使用 Mock 数据，后端就绪后设置 USE_MOCK = false
// =====================================================

import request from '@/utils/request'
import type { ApiResponse, LoginParams, LoginResult, UserInfo } from '@/types/api'

const USE_MOCK = false

const mockDelay = <T>(data: T, d = 400): Promise<T> =>
  new Promise((r) => setTimeout(() => r(data), d))

/** Mock 用户数据库 */
const mockUsers: Record<string, { password: string; user: LoginResult['user'] }> = {
  admin: {
    password: 'admin123',
    user: { id: 1, username: 'admin', role: 'admin', nickname: '管理员', created_at: '2026-01-01T00:00:00' },
  },
  user001: {
    password: 'user123',
    user: { id: 2, username: 'user001', role: 'user', nickname: '张三', created_at: '2026-01-15T00:00:00' },
  },
}

// 为方便测试，任意非空用户名+密码都可登录（默认用 admin 角色）
const DEFAULT_USER: LoginResult['user'] = {
  id: 99, username: '', role: 'admin', nickname: '', created_at: '2026-01-01T00:00:00',
}

/** 当前登录的 Token（Mock 用） */
let mockToken = ''

/**
 * 2.1 用户登录
 * 接口: POST /auth/login
 */
export const login = async (params: LoginParams): Promise<ApiResponse<LoginResult>> => {
  if (USE_MOCK) {
    // 校验非空
    if (!params.username || !params.password) {
      throw new Error('请输入用户名和密码')
    }
    // 如果匹配预设账户则用预设信息，否则用输入的用户名创建临时用户
    const found = mockUsers[params.username]
    const user = found && found.password === params.password
      ? found.user
      : { ...DEFAULT_USER, id: Math.floor(Math.random() * 100), username: params.username, nickname: params.username }

    mockToken = 'mock-jwt-token-' + Date.now()
    return mockDelay({
      code: 200, message: '登录成功',
      data: { access_token: mockToken, token_type: 'bearer', expires_in: 86400, user },
    })
  }
  return request.post('/auth/login', params)
}

/**
 * 2.2 获取当前用户信息
 * 接口: GET /auth/me
 */
export const getCurrentUser = async (): Promise<ApiResponse<UserInfo>> => {
  if (USE_MOCK) {
    // 从 localStorage 读取之前保存的用户信息
    const saved = localStorage.getItem('auth-store')
    let user: UserInfo
    try {
      const parsed = saved ? JSON.parse(saved) : null
      user = parsed?.userInfo
    } catch {
      user = mockUsers.admin.user
    }
    if (!user) {
      return mockDelay({ code: 401, message: '未认证', data: null as any })
    }
    return mockDelay({ code: 200, message: 'success', data: user })
  }
  return request.get('/auth/me')
}

/**
 * 2.3 用户登出
 * 接口: POST /auth/logout
 */
export const logout = async (): Promise<ApiResponse<null>> => {
  if (USE_MOCK) {
    mockToken = ''
    return mockDelay({ code: 200, message: '登出成功', data: null })
  }
  return request.post('/auth/logout')
}
