// =====================================================
// src/main.ts
// 应用入口文件 - 初始化 Vue 应用
// 注册: Pinia（状态管理）、Router（路由）、Element Plus（UI组件库）
// =====================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import router from './router'
import App from './App.vue'

// 引入全局样式（浅色系主题）
import './assets/styles/global.scss'

// 创建 Pinia 实例并安装持久化插件
// pinia-plugin-persistedstate: 自动将 store 状态同步到 localStorage
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// 创建 Vue 应用
const app = createApp(App)

// 注册插件
app.use(pinia) // 状态管理（必须在 router 之前注册，因为 router 守卫中要用到 store）
app.use(router) // 路由

// 挂载到 #app
app.mount('#app')
