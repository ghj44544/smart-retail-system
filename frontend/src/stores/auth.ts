// =====================================================
// src/stores/auth.ts
// 认证状态管理 - 使用 Pinia + pinia-plugin-persistedstate 持久化存储
// 管理用户登录状态、Token、用户信息、权限判断
// =====================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi, getCurrentUser, logout as logoutApi } from '@/api/auth'
import type { UserInfo, LoginParams } from '@/types/api'

/**
 * 认证 Store
 *
 * 使用 pinia-plugin-persistedstate 插件将 state 持久化到 localStorage
 * 这样页面刷新后仍然可以保持登录状态
 */
export const useAuthStore = defineStore(
  'auth',
  () => {
    // ==================== State（状态） ====================

    /** JWT Token - 存储在 localStorage，每次请求通过拦截器自动携带 */
    const token = ref<string>('')

    /** 当前登录用户信息 */
    const userInfo = ref<UserInfo | null>(null)

    // ==================== Getters（计算属性） ====================

    /** 是否已登录 - 用于路由守卫判断 */
    const isLoggedIn = computed(() => !!token.value && !!userInfo.value)

    /** 用户角色 - 用于权限控制判断 */
    const userRole = computed(() => userInfo.value?.role || '')

    /** 是否为管理员 - 只有 admin 角色可以访问管理功能 */
    const isAdmin = computed(() => userInfo.value?.role === 'admin')

    /** 用户显示名称 - 优先显示昵称，其次用户名 */
    const displayName = computed(() => userInfo.value?.nickname || userInfo.value?.username || '未登录')

    // ==================== Actions（操作） ====================

    /**
     * 登录操作
     *
     * 流程:
     * 1. 调用 POST /auth/login 接口获取 Token 和用户信息
     * 2. 将 Token 存储到 state（自动持久化到 localStorage）
     * 3. 将用户信息存储到 state
     *
     * @param params - 登录参数 { username, password }
     * @throws 登录失败时抛出错误
     */
    const login = async (params: LoginParams): Promise<void> => {
      // 调用登录接口（自动走 request 拦截器，不需要手动携带 Token）
      const response = await loginApi(params)

      // 保存 Token 和用户信息到状态中
      token.value = response.data.access_token
      userInfo.value = response.data.user
    }

    /**
     * 获取当前用户信息（刷新时恢复登录状态）
     *
     * 流程:
     * 1. 调用 GET /auth/me 接口验证 Token 是否有效
     * 2. 如果 Token 有效，更新用户信息
     * 3. 如果 Token 无效（401），清除登录状态
     *
     * @returns 是否成功获取用户信息
     */
    const fetchUserInfo = async (): Promise<boolean> => {
      // 如果连 Token 都没有，直接返回 false
      if (!token.value) return false

      try {
        const response = await getCurrentUser()
        userInfo.value = response.data
        return true
      } catch {
        // Token 过期或无效，清除状态
        clearAuth()
        return false
      }
    }

    /**
     * 登出操作
     *
     * 流程:
     * 1. 调用 POST /auth/logout 接口通知后端将 Token 加入黑名单
     * 2. 清除前端本地存储的 Token 和用户信息
     * 3. 跳转到登录页面
     */
    const logout = async (): Promise<void> => {
      try {
        // 调用后端登出接口
        // 后端的 logout 接口会将 Token 加入 Redis 黑名单使其失效
        await logoutApi()
      } catch {
        // 即使后端登出失败（网络错误等），前端也要清除状态
        console.warn('登出接口调用失败，前端状态已清除')
      } finally {
        // 无论如何都清除本地状态
        clearAuth()
        // 跳转到登录页面
        window.location.href = '/login'
      }
    }

    /**
     * 清除认证状态
     * 将 Token 和用户信息全部置空
     * pinia-plugin-persistedstate 会自动同步到 localStorage
     */
    const clearAuth = (): void => {
      token.value = ''
      userInfo.value = null
    }

    return {
      // State
      token,
      userInfo,
      // Getters
      isLoggedIn,
      userRole,
      isAdmin,
      displayName,
      // Actions
      login,
      fetchUserInfo,
      logout,
      clearAuth,
    }
  },
  {
    // ==================== Pinia 持久化配置 ====================
    // 使用 pinia-plugin-persistedstate 将状态自动同步到 localStorage
    // 页面刷新后登录状态不会丢失
    persist: {
      key: 'auth-store', // localStorage 中的键名
      storage: localStorage, // 存储方式
      // 只持久化 token 和 userInfo，不持久化计算属性
      paths: ['token', 'userInfo'],
    },
  }
)
