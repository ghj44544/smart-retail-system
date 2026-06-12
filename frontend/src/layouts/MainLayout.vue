<!--
  =====================================================
  src/layouts/MainLayout.vue
  主布局组件 - 侧边栏 + 顶栏 + 内容区三栏布局
  用于登录后的所有页面
  =====================================================
-->
<template>
  <div class="main-layout">
    <!-- ========== 侧边栏 ========== -->
    <aside class="main-layout-sidebar" :class="{ collapsed: sidebarCollapsed }">
      <!-- Logo 区域 -->
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon">
          <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="10" width="14" height="14" rx="3" fill="rgba(108,92,231,0.9)"/>
            <rect x="11" y="6" width="14" height="14" rx="3" fill="rgba(108,92,231,0.7)"/>
            <rect x="18" y="14" width="14" height="14" rx="3" fill="rgba(108,92,231,0.5)"/>
          </svg>
        </div>
        <transition name="fade">
          <span v-show="!sidebarCollapsed" class="sidebar-logo-text">智能零售分析</span>
        </transition>
      </div>

      <!-- 导航菜单
           各模块路由对应 API 文档中的功能模块
           后续开发各模块时按需添加对应路由 -->
      <el-menu
        :default-active="currentRoute"
        :collapse="sidebarCollapsed"
        :router="true"
        class="sidebar-menu"
        background-color="transparent"
        text-color="#636e72"
        active-text-color="#6c5ce7"
      >
        <!-- 数据驾驶舱（已完成） -->
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据驾驶舱</template>
        </el-menu-item>

        <!-- 用户分析（已完成） -->
        <el-sub-menu index="/users-group">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户分析</span>
          </template>
          <el-menu-item index="/users">
            <el-icon><List /></el-icon>
            <template #title>用户列表</template>
          </el-menu-item>
          <el-menu-item index="/users/rfm">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>RFM 分析</template>
          </el-menu-item>
          <el-menu-item index="/users/cluster">
            <el-icon><Connection /></el-icon>
            <template #title>聚类分析</template>
          </el-menu-item>
        </el-sub-menu>

        <!-- 商品管理（已完成） -->
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>商品管理</template>
        </el-menu-item>

        <!-- 订单管理（已完成） -->
        <el-menu-item index="/orders">
          <el-icon><List /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>

        <!-- 行为分析（已完成） -->
        <el-menu-item index="/behaviors">
          <el-icon><Monitor /></el-icon>
          <template #title>行为分析</template>
        </el-menu-item>

        <!-- 推荐系统（已完成） -->
        <el-menu-item index="/recommend">
          <el-icon><Present /></el-icon>
          <template #title>推荐系统</template>
        </el-menu-item>

        <el-menu-item index="/ai-assistant">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>AI 智能助手</template>
        </el-menu-item>

        <!-- 个人中心 -->
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>个人中心</template>
        </el-menu-item>
      </el-menu>

      <!-- 折叠按钮 -->
      <div class="sidebar-collapse-btn" @click="toggleSidebar">
        <el-icon :class="{ rotated: sidebarCollapsed }">
          <ArrowLeft />
        </el-icon>
      </div>
    </aside>

    <!-- ========== 主体区域 ========== -->
    <div class="main-layout-body">
      <!-- 顶部栏 -->
      <header class="main-layout-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 用户信息下拉 -->
          <el-dropdown trigger="click">
            <div class="header-user">
              <el-avatar :size="36" icon="UserFilled" style="background: linear-gradient(135deg, #6c5ce7, #a29bfe);" />
              <span class="header-user-name">{{ authStore.displayName }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/profile')">
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 内容区域 -->
      <main class="main-layout-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 主布局逻辑
// =====================================================
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  DataAnalysis, ArrowLeft, ArrowDown, User, SwitchButton,
  Goods, List, Monitor, Present, Connection, ChatDotRound,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

/** 侧边栏折叠状态 */
const sidebarCollapsed = ref(false)

/** 当前路由路径（用于菜单高亮） */
const currentRoute = ref(route.path)
watch(() => route.path, (path) => {
  currentRoute.value = path
}, { immediate: true })

/** 当前页面标题 */
const currentPageTitle = computed(() => (route.meta.title as string) || '首页')

// ==================== 方法 ====================

/** 切换侧边栏折叠 */
const toggleSidebar = (): void => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

/**
 * 处理退出登录
 * 弹出确认框，确认后调用 authStore.logout()
 * authStore.logout 内部:
 *   1. 调用 POST /auth/logout 接口
 *   2. 清除 Token 和用户信息
 *   3. 跳转到 /login
 */
const handleLogout = async (): Promise<void> => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    // 调用 Store 的 logout action
    await authStore.logout()
  } catch {
    // 用户取消退出
  }
}
</script>

<style lang="scss" scoped>
/* =====================================================
   主布局样式
   ===================================================== */

.main-layout {
  display: flex;
  height: 100vh;
  background: var(--bg-body);
}

/* ==================== 侧边栏 ==================== */
.main-layout-sidebar {
  position: relative;
  flex-shrink: 0;
  width: 240px;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.02);

  &.collapsed {
    width: 64px;
  }
}

/* Logo 区 */
.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--border-light);
  overflow: hidden;
}

.sidebar-logo-icon svg {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
}

.sidebar-logo-text {
  margin-left: 10px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
  white-space: nowrap;
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 菜单 */
.sidebar-menu {
  flex: 1;
  border-right: none;
  padding: 8px;

  :deep(.el-menu-item) {
    border-radius: 8px;
    margin-bottom: 4px;
    height: 44px;
    line-height: 44px;

    &:hover {
      background: rgba(108, 92, 231, 0.06);
    }

    &.is-active {
      background: linear-gradient(135deg, rgba(108, 92, 231, 0.1), rgba(162, 155, 254, 0.05));
      font-weight: 600;
    }
  }
}

/* 折叠按钮 */
.sidebar-collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-top: 1px solid var(--border-light);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.3s;

  &:hover {
    color: var(--color-primary);
    background: rgba(108, 92, 231, 0.04);
  }

  .el-icon {
    transition: transform 0.3s ease;

    &.rotated {
      transform: rotate(180deg);
    }
  }
}

/* ==================== 主体区域 ==================== */
.main-layout-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-body);
}

/* 顶部栏 */
.main-layout-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--bg-header);
  border-bottom: 1px solid var(--border-light);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.02);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

/* 用户信息区 */
.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: background 0.2s;

  &:hover {
    background: var(--bg-hover);
  }
}

.header-user-name {
  font-size: 14px;
  color: var(--text-primary);
}

/* 内容区域 */
.main-layout-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
}

/* ==================== 动画 ==================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
