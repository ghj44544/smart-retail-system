// =====================================================
// src/router/index.ts
// 路由配置 - 包含路由守卫实现页面级别的权限控制
// 未登录用户只能访问 /login，已登录用户自动跳转到首页
// =====================================================

import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * 路由表定义
 *
 * meta.requiresAuth: true - 需要登录才能访问
 * meta.roles: 允许访问的角色数组，空数组表示所有角色
 * meta.title: 页面标题（用于面包屑和浏览器标题）
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: {
      requiresAuth: false, // 登录页面不需要认证
      title: '登录',
    },
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: {
      requiresAuth: true, // 需要登录
      title: '首页',
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/index.vue'),
        meta: {
          requiresAuth: true,
          title: '数据驾驶舱',
        },
      },
      // ========== 用户分析模块 ==========
      {
        path: 'users',
        name: 'UserList',
        component: () => import('@/views/users/index.vue'),
        meta: {
          requiresAuth: true,
          title: '用户列表',
        },
      },
      {
        path: 'users/:id',
        name: 'UserDetail',
        component: () => import('@/views/users/detail.vue'),
        meta: {
          requiresAuth: true,
          title: '用户详情',
        },
      },
      {
        path: 'users/rfm',
        name: 'RFMAnalysis',
        component: () => import('@/views/users/rfm.vue'),
        meta: {
          requiresAuth: true,
          title: 'RFM分析',
        },
      },
      {
        path: 'users/cluster',
        name: 'ClusterAnalysis',
        component: () => import('@/views/users/cluster.vue'),
        meta: {
          requiresAuth: true,
          title: '聚类分析',
        },
      },
      // ========== 商品管理模块 ==========
      {
        path: 'products',
        name: 'ProductList',
        component: () => import('@/views/products/index.vue'),
        meta: {
          requiresAuth: true,
          title: '商品管理',
        },
      },
      {
        path: 'products/:id',
        name: 'ProductDetail',
        component: () => import('@/views/products/detail.vue'),
        meta: { requiresAuth: true, title: '商品详情' },
      },
      // ========== 订单管理模块 ==========
      {
        path: 'orders',
        name: 'OrderList',
        component: () => import('@/views/orders/index.vue'),
        meta: { requiresAuth: true, title: '订单管理' },
      },
      {
        path: 'orders/:id',
        name: 'OrderDetail',
        component: () => import('@/views/orders/detail.vue'),
        meta: { requiresAuth: true, title: '订单详情' },
      },
      // ========== 行为分析模块 ==========
      {
        path: 'behaviors',
        name: 'BehaviorAnalysis',
        component: () => import('@/views/behaviors/index.vue'),
        meta: { requiresAuth: true, title: '行为分析' },
      },
      // ========== 推荐系统模块 ==========
      {
        path: 'recommend',
        name: 'RecommendSystem',
        component: () => import('@/views/recommend/index.vue'),
        meta: { requiresAuth: true, title: '推荐系统' },
      },
      // ========== 个人中心 ==========
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/profile/index.vue'),
        meta: { requiresAuth: true, title: '个人中心' },
      },
    ],
  },
  // 404 页面 - 捕获所有未匹配的路由
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/404.vue'),
    meta: {
      requiresAuth: false,
      title: '页面未找到',
    },
  },
]

const router = createRouter({
  // 使用 HTML5 History 模式（hash 模式用 createWebHashHistory）
  history: createWebHistory(),
  routes,
})

// ==================== 全局前置守卫 (Navigation Guard) ====================

/**
 * 路由守卫逻辑:
 * 1. 如果目标页面需要登录（meta.requiresAuth = true）且用户未登录
 *    → 重定向到 /login，携带 redirect 参数以便登录后跳回
 * 2. 如果用户已登录但访问 /login
 *    → 直接重定向到首页 /dashboard（已登录用户不需要再登录）
 * 3. 设置页面标题
 */
router.beforeEach(async (to, _from, next) => {
  // 修改浏览器标签标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 智能零售用户行为分析系统`
  }

  // 获取认证 Store（Pinia 的 Store 在 router 中使用需要等 Pinia 初始化完成后）
  // 这里通过 pinia 的 getActivePinia 或者使用动态导入的方式来获取
  // 由于 main.ts 中 router 在 pinia 之后安装，这里可以安全使用
  const authStore = useAuthStore()

  // 如果目标页面需要登录认证
  if (to.meta.requiresAuth) {
    // 检查是否已登录
    if (!authStore.isLoggedIn) {
      // 未登录 → 跳转到登录页
      // 携带 redirect 参数：登录成功后可以跳回目标页面
      next({
        path: '/login',
        query: { redirect: to.fullPath },
      })
      return
    }

    // 检查角色权限（如果路由配置了 roles 数组）
    if (to.meta.roles && Array.isArray(to.meta.roles) && to.meta.roles.length > 0) {
      const hasPermission = to.meta.roles.includes(authStore.userRole)
      if (!hasPermission) {
        // 无权限 → 跳转到首页
        next('/dashboard')
        return
      }
    }
  }

  // 如果用户已登录但访问的是登录页面 → 直接跳转到首页
  if (to.path === '/login' && authStore.isLoggedIn) {
    next('/dashboard')
    return
  }

  // 其他情况放行
  next()
})

export default router
