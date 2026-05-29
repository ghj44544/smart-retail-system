<!--
  =====================================================
  src/views/login/index.vue
  登录页面 - 炫酷浅色系 UI
  严格遵循 API 接口规范文档 v1.0 第二章 2.1 用户登录

  设计风格: 柔和渐变背景 + 毛玻璃卡片 + 动态装饰元素
  配色: 浅紫/浅蓝/白色为主调的现代化登录界面
  =====================================================
-->
<template>
  <div
    class="login-page"
    :style="{
      '--mx': mouseX,
      '--my': mouseY,
    }"
    @mousemove="handleMouseMove"
  >
    <!-- ========== 背景装饰层 ========== -->
    <!-- 渐变色光球 - 左上 -->
    <div class="login-bg-orb orb-1"></div>
    <!-- 渐变色光球 - 右下 -->
    <div class="login-bg-orb orb-2"></div>
    <!-- 渐变色光球 - 右侧中间 -->
    <div class="login-bg-orb orb-3"></div>

    <!-- ========== 左侧品牌信息区 ========== -->
    <div class="login-brand">
      <div class="login-brand-content">
        <!-- Logo 图标 -->
        <div class="login-brand-icon">
          <svg viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 数据立方体图标 -->
            <rect x="8" y="20" width="28" height="28" rx="4" fill="rgba(255,255,255,0.9)" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>
            <rect x="22" y="12" width="28" height="28" rx="4" fill="rgba(255,255,255,0.75)" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>
            <rect x="36" y="28" width="28" height="28" rx="4" fill="rgba(255,255,255,0.6)" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>
            <!-- 数据分析折线 -->
            <polyline points="14,34 20,28 26,32 32,24" stroke="rgba(255,255,255,0.9)" stroke-width="2" fill="none" stroke-linecap="round"/>
          </svg>
        </div>

        <!-- 系统标题 -->
        <h1 class="login-brand-title">智能零售</h1>
        <h2 class="login-brand-subtitle">用户行为分析系统</h2>

        <!-- 描述文字 -->
        <p class="login-brand-desc">
          智慧零售，数据驱动。洞察消费者行为，挖掘潜在价值，
          让每一次决策都精准有力，让每一份数据都创造价值。
        </p>
      </div>
    </div>

    <!-- ========== 右侧登录表单区 ========== -->
    <div class="login-form-area">
      <div class="login-form-card">
        <!-- 表单头部 -->
        <div class="login-form-header">
          <h3 class="login-form-title">欢迎回来</h3>
          <p class="login-form-subtitle">请登录您的账户以继续使用</p>
        </div>

        <!-- 登录表单
             提交事件绑定 handleLogin
             禁用自动完成避免浏览器填充干扰 -->
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          @keyup.enter="handleLogin"
          autocomplete="off"
          class="login-form-body"
        >
          <!-- 用户名输入 -->
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              :prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>

          <!-- 密码输入 -->
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              :prefix-icon="Lock"
              size="large"
              show-password
              clearable
            />
          </el-form-item>

          <!-- 记住密码 & 忘记密码 -->
          <div class="login-form-extra">
            <el-checkbox v-model="rememberMe">记住密码</el-checkbox>
            <a class="login-forgot-link" href="javascript:void(0)">忘记密码？</a>
          </div>

          <!-- 登录按钮
               当 loading 为 true 时显示加载动画并禁用按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              :disabled="loading"
              @click="handleLogin"
              class="login-submit-btn"
            >
              {{ loading ? '登录中...' : '登 录' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 登录页面逻辑
// =====================================================
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { LoginParams } from '@/types/api'

// ==================== 依赖注入 ====================

/** 路由实例 - 用于登录成功后跳转 */
const router = useRouter()

/** 当前路由 - 用于获取 redirect 参数 */
const route = useRoute()

/** 认证 Store - 调用 login action 执行登录 */
const authStore = useAuthStore()

// ==================== 状态定义 ====================

/** 登录加载状态 - true 时按钮显示加载动画并禁用 */
const loading = ref(false)

/** 是否记住密码 */
const rememberMe = ref(false)

/** 表单组件引用 - 用于表单验证 */
const loginFormRef = ref<FormInstance>()

/** 鼠标位置 (0~1 百分比) - 驱动背景渐变和光球位置 */
const mouseX = ref(0.5)
const mouseY = ref(0.5)

/**
 * 登录表单数据
 * 严格对应 API 文档 2.1 接口: POST /auth/login
 * 请求参数: { username: string, password: string }
 */
const loginForm = reactive<LoginParams>({
  username: '',
  password: '',
})

/**
 * 表单验证规则
 * username: 必填，长度 3-20 字符
 * password: 必填，长度 6-30 字符
 */
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度 3-20 字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度 6-30 字符', trigger: 'blur' },
  ],
}

// ==================== 鼠标追踪 ====================

/** 鼠标移动 → 更新 CSS 变量，驱动背景渐变和光球跟随 */
const handleMouseMove = (e: MouseEvent): void => {
  mouseX.value = e.clientX / window.innerWidth
  mouseY.value = e.clientY / window.innerHeight
}

// ==================== 方法定义 ====================

/**
 * 处理登录操作
 *
 * 流程:
 * 1. 表单验证 → 失败则终止
 * 2. 调用 authStore.login() → 内部调用 POST /auth/login
 * 3. 登录成功 → 跳转到 redirect 页面或首页 /dashboard
 * 4. 登录失败 → 显示错误提示
 */
const handleLogin = async (): Promise<void> => {
  // 表单验证 - 点击登录按钮时手动触发
  if (!loginFormRef.value) return

  try {
    // Step 1: 验证表单
    await loginFormRef.value.validate()
  } catch {
    // 表单验证失败，不执行登录
    return
  }

  // Step 2: 设置加载状态
  loading.value = true

  try {
    // Step 3: 调用 Store 的 login action
    // authStore.login 内部:
    //   调用 POST /auth/login 接口
    //   保存 Token 和用户信息到 Store（自动持久化到 localStorage）
    await authStore.login({
      username: loginForm.username,
      password: loginForm.password,
    })

    // Step 4: 登录成功提示
    ElMessage.success({
      message: `欢迎回来，${authStore.displayName}！`,
      duration: 2000,
    })

    // Step 5: 跳转到目标页面（安全校验：仅允许内部路径）
    let redirectPath = (route.query.redirect as string) || '/dashboard'
    if (!redirectPath.startsWith('/') || redirectPath.startsWith('//')) {
      redirectPath = '/dashboard'
    }
    router.push(redirectPath)
  } catch (error: any) {
    // Step 6: 登录失败处理
    // 错误信息由 Axios 响应拦截器统一显示
    // 这里做额外的处理（如清空密码框）
    loginForm.password = ''
  } finally {
    // Step 7: 关闭加载状态
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
/* =====================================================
   登录页面样式 - 炫酷浅色系 UI
   设计理念: 柔和渐变 + 毛玻璃效果 + 流动光球装饰
   ===================================================== */

/* ==================== 页面容器 ==================== */
.login-page {
  position: relative;
  display: flex;
  width: 100%;
  height: 100vh;
  min-height: 650px;
  overflow: hidden;
  /* 卡通粉色小花光标（带小脸和叶子） */
  cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='36' viewBox='0 0 32 36'%3E%3Cg transform='translate(16,18)'%3E%3C!-- 花瓣 --%3E%3Cellipse cx='0' cy='-8' rx='5.5' ry='7' fill='%23f9a8d4' stroke='%23f472b6' stroke-width='0.8'/%3E%3Cellipse cx='7.6' cy='-2.5' rx='5.5' ry='7' fill='%23f9a8d4' stroke='%23f472b6' stroke-width='0.8' transform='rotate(72)'/%3E%3Cellipse cx='4.7' cy='6.5' rx='5.5' ry='7' fill='%23fbcfe8' stroke='%23f472b6' stroke-width='0.8' transform='rotate(144)'/%3E%3Cellipse cx='-4.7' cy='6.5' rx='5.5' ry='7' fill='%23f9a8d4' stroke='%23f472b6' stroke-width='0.8' transform='rotate(216)'/%3E%3Cellipse cx='-7.6' cy='-2.5' rx='5.5' ry='7' fill='%23fbcfe8' stroke='%23f472b6' stroke-width='0.8' transform='rotate(288)'/%3E%3C!-- 花心 --%3E%3Ccircle cx='0' cy='0' r='5' fill='%23fdf2f8' stroke='%23f472b6' stroke-width='0.5'/%3E%3C!-- 小脸 --%3E%3Ccircle cx='-2' cy='-1' r='0.8' fill='%23333'/%3E%3Ccircle cx='2' cy='-1' r='0.8' fill='%23333'/%3E%3C!-- 笑脸 --%3E%3Cpath d='M-1.5,1.2 Q0,2.8 1.5,1.2' fill='none' stroke='%23333' stroke-width='0.6' stroke-linecap='round'/%3E%3C/g%3E%3Cg transform='translate(16,30)'%3E%3C!-- 茎 --%3E%3Cline x1='0' y1='-4' x2='0' y2='6' stroke='%234ade80' stroke-width='2' stroke-linecap='round'/%3E%3C!-- 叶子 --%3E%3Cellipse cx='0' cy='4' rx='2.5' ry='5' fill='%234ade80' stroke='%2322c55e' stroke-width='0.6' transform='rotate(-25)'/%3E%3C/g%3E%3C/svg%3E") 16 18, auto;
  /* 鼠标位置映射 */
  --grad-x: calc(var(--mx) * 100%);
  --grad-y: calc(var(--my) * 100%);
  /* 背景图 + 跟随鼠标的紫色辉光叠加 */
  background:
    radial-gradient(ellipse 60% 60% at var(--grad-x) calc(100% - var(--grad-y)), rgba(168,85,247,0.14), transparent 60%),
    url('/denglu.png') center / cover no-repeat;
  transition: background 0.6s ease-out;
}

/* ==================== 背景装饰光球（跟随鼠标偏移） ==================== */
.login-bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.3;
  pointer-events: none;
  z-index: 0;
  transition: transform 0.8s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

/* 光球1 - 紫粉，跟随鼠标同向偏移 */
.orb-1 {
  width: 450px; height: 450px;
  top: -20%; left: -10%;
  background: radial-gradient(circle, rgba(192,132,252,0.4), rgba(216,180,254,0.12), transparent 70%);
  transform: translate(calc(var(--mx) * 120px), calc(var(--my) * 80px));
}

/* 光球2 - 粉紫，跟随鼠标反向偏移 */
.orb-2 {
  width: 380px; height: 380px;
  bottom: -15%; right: -8%;
  background: radial-gradient(circle, rgba(244,114,182,0.35), rgba(249,168,212,0.1), transparent 70%);
  transform: translate(calc((1 - var(--mx)) * 100px), calc((1 - var(--my)) * 70px));
}

/* 光球3 - 紫色，跟随鼠标轻微偏移 */
.orb-3 {
  width: 300px; height: 300px;
  top: 35%; right: 25%;
  background: radial-gradient(circle, rgba(168,85,247,0.28), rgba(196,181,253,0.1), transparent 70%);
  transform: translate(calc(var(--mx) * 60px - 30px), calc(var(--my) * 60px - 30px));
}

/* ==================== 左侧品牌信息区 ==================== */
.login-brand {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.login-brand-content {
  max-width: 480px;
}

/* Logo 图标 */
.login-brand-icon {
  width: 88px;
  height: 88px;
  margin-bottom: 32px;
  background: linear-gradient(135deg, rgba(168,85,247,0.14), rgba(244,114,182,0.08));
  border-radius: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.3);
  box-shadow: 0 4px 20px rgba(168,85,247,0.08);
}

.login-brand-icon svg {
  width: 60px;
  height: 60px;
}

/* 主标题 */
.login-brand-title {
  font-size: 52px;
  font-weight: 900;
  letter-spacing: 8px;
  background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 40%, #3b82f6 70%, #06b6d4 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  line-height: 1.15;
  text-shadow: none;
  filter: drop-shadow(0 2px 6px rgba(37,99,235,0.15));
}

/* 副标题 */
.login-brand-subtitle {
  font-size: 24px;
  font-weight: 400;
  color: #93a3bb;
  margin-top: 8px;
  letter-spacing: 6px;
}

/* 描述文字 */
.login-brand-desc {
  margin-top: 32px;
  font-size: 17px;
  line-height: 2.1;
  color: #64748b;
  opacity: 0.85;
  max-width: 380px;
  font-weight: 400;
  letter-spacing: 1px;
}

/* ==================== 右侧登录表单区 ==================== */
.login-form-area {
  position: relative;
  z-index: 1;
  flex: 0 0 500px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

/* 登录卡片 - 毛玻璃效果 */
.login-form-card {
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow:
    0 8px 32px rgba(0,0,0,0.06),
    0 2px 8px rgba(0,0,0,0.03),
    inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    box-shadow:
     0 12px 40px rgba(0,0,0,0.08),
     0 4px 12px rgba(0,0,0,0.04),
      inset 0 1px 0 rgba(255, 255, 255, 0.5);
  }
}

/* 表单头部 */
.login-form-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-form-title {
  font-size: 28px;
  font-weight: 700;
  color: #2d3436;
  letter-spacing: 1px;
}

.login-form-subtitle {
  margin-top: 8px;
  font-size: 14px;
  color: #b2bec3;
}

/* 表单主体 */
.login-form-body {
  margin-top: 8px;
}

/* 自定义 Element Plus 表单项间距 */
:deep(.el-form-item) {
  margin-bottom: 22px;
}

/* 自定义输入框样式 - 柔和圆角 */
:deep(.el-input__wrapper) {
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.65);
  box-shadow: 0 0 0 1px rgba(168,85,247,0.1);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 0 0 1px rgba(168,85,247,0.25);
    background: rgba(255, 255, 255, 0.85);
  }
}

:deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 2px rgba(168,85,247,0.25);
  background: rgba(255, 255, 255, 0.9);
}

:deep(.el-input__inner) {
  font-size: 15px;
  color: #2d3436;

  &::placeholder {
    color: #c8d6e5;
  }
}

/* 额外操作栏 */
.login-form-extra {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
}

.login-forgot-link {
  color: #3b82f6;
  text-decoration: none;
  transition: color 0.3s;

  &:hover {
    color: #1d4ed8;
  }
}

/* 登录按钮 */
.login-submit-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  border: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(37,99,235,0.3);

  &:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(37,99,235,0.4);
  }

  &:not(:disabled):active {
    transform: translateY(0);
  }
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 900px) {
  .login-brand {
    display: none; // 小屏幕隐藏品牌区
  }

  .login-form-area {
    flex: 1;
    padding: 20px;
  }

  .login-form-card {
    padding: 36px 28px;
  }
}

@media (max-width: 480px) {
  .login-form-card {
    border-radius: 20px;
    padding: 28px 20px;
  }

  .login-form-title {
    font-size: 24px;
  }
}
</style>
