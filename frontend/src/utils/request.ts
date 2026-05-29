// =====================================================
// src/utils/request.ts
// Axios 请求封装 - 统一处理 JWT 认证、错误拦截、请求/响应拦截
// Base URL: http://localhost:8000/api/v1
// 认证方式: Header: Authorization: Bearer <token>
// =====================================================

import axios, { AxiosInstance, AxiosRequestConfig, InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'

/**
 * 创建 Axios 实例，配置基础参数
 *
 * baseURL: 后端 API 基础地址，优先使用环境变量 VITE_API_BASE_URL
 * timeout: 请求超时时间 10秒
 * Content-Type: 默认 application/json
 */
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ==================== 请求拦截器 ====================

/**
 * 请求拦截器 - 在每个请求发送前自动执行
 * 功能:
 * 1. 从 localStorage 获取 JWT Token
 * 2. 将 Token 添加到请求头 Authorization 字段中
 * 3. 格式: Bearer <token>
 */
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 Pinia 持久化存储 auth-store 中读取 Token
    // Pinia persist key: 'auth-store', paths: ['token', 'userInfo']
    // 存储格式: {"token":"eyJ...", "userInfo":{...}}
    // 对应 API 文档 1.4 认证说明：
    // "登录后获取 access_token，后续请求在 Header 中携带: Authorization: Bearer xxx"
    const authData = localStorage.getItem('auth-store')
    let token: string | null = null
    if (authData) {
      try {
        const parsed = JSON.parse(authData)
        token = parsed.token || null
      } catch {
        token = null
      }
    }

    if (token && config.headers) {
      // 设置 JWT 认证头（严格遵循 API 文档规范）
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    // 请求配置错误，直接拒绝
    return Promise.reject(error)
  }
)

// ==================== 响应拦截器 ====================

/**
 * 响应拦截器 - 在每个响应返回后自动执行
 * 功能:
 * 1. 检查响应状态码 code !== 200 时弹出错误提示
 * 2. 401 状态码时清除 Token 并跳转到登录页
 * 3. 网络错误时提示用户
 */
request.interceptors.response.use(
  (response) => {
    // 获取后端返回的统一响应格式 { code, message, data }
    const res = response.data as ApiResponse

    // 如果后端返回的 code 不是 200，说明业务逻辑出错
    if (res.code !== 200) {
      // 弹窗提示错误信息
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }

    // 返回成功数据
    return res
  },
  (error) => {
    // HTTP 状态码错误处理

    // 401 未认证：Token 过期或无效
    // 对应 API 文档错误码：401 = 未认证 / Token 过期
    if (error.response?.status === 401) {
      // 清除 Pinia 持久化的认证状态（auth-store）
      localStorage.removeItem('auth-store')
      // 跳转到登录页面
      window.location.href = '/login'
      ElMessage.error('登录已过期，请重新登录')
      return Promise.reject(error)
    }

    // 403 无权限
    if (error.response?.status === 403) {
      ElMessage.error('您没有权限执行此操作')
      return Promise.reject(error)
    }

    // 404 资源不存在
    if (error.response?.status === 404) {
      ElMessage.error('请求的资源不存在')
      return Promise.reject(error)
    }

    // 500 服务器错误
    if (error.response?.status === 500) {
      ElMessage.error('服务器内部错误，请稍后重试')
      return Promise.reject(error)
    }

    // 网络错误或其他错误
    ElMessage.error(error.message || '网络连接失败，请检查网络')
    return Promise.reject(error)
  }
)

export default request
