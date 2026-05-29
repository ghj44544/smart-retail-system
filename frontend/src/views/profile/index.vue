<!--
  =====================================================
  src/views/profile/index.vue
  个人中心页面 - 查看和编辑当前用户信息
  =====================================================
-->
<template>
  <div class="profile-page">
    <div class="page-header">
      <h2>个人中心</h2>
      <p class="page-desc">查看和编辑您的个人信息</p>
    </div>

    <div class="profile-content">
      <!-- 左侧：用户卡片 -->
      <div class="profile-card">
        <div class="card-avatar">
          <el-avatar :size="80" icon="UserFilled" style="background: linear-gradient(135deg, #6c5ce7, #a29bfe);" />
        </div>
        <div class="card-info">
          <h3>{{ authStore.displayName }}</h3>
          <el-tag :type="authStore.isAdmin ? 'danger' : 'info'" size="small">
            {{ authStore.isAdmin ? '管理员' : '普通用户' }}
          </el-tag>
          <p class="card-username">@{{ authStore.userInfo?.username }}</p>
        </div>
        <el-divider />
        <div class="card-stats">
          <div class="stat-item">
            <span class="stat-value">{{ formatMoney(userDetail?.total_consumption || 0) }}</span>
            <span class="stat-label">累计消费</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ userDetail?.order_count || 0 }}</span>
            <span class="stat-label">订单数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ formatMoney(userDetail?.avg_order_value || 0) }}</span>
            <span class="stat-label">客单价</span>
          </div>
        </div>
      </div>

      <!-- 右侧：编辑表单 -->
      <div class="profile-forms">
        <!-- 基本信息编辑 -->
        <el-card shadow="never" class="form-card">
          <template #header>
            <span class="card-title">基本信息</span>
          </template>
          <el-form
            ref="infoFormRef"
            :model="infoForm"
            :rules="infoRules"
            label-width="80px"
            label-position="left"
          >
            <el-form-item label="用户名">
              <el-input :model-value="authStore.userInfo?.username" disabled />
            </el-form-item>
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="infoForm.nickname" placeholder="请输入昵称" maxlength="100" show-word-limit />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="infoForm.email" placeholder="请输入邮箱" />
            </el-form-item>
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="infoForm.phone" placeholder="请输入手机号" maxlength="11" />
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="authStore.isAdmin ? 'danger' : 'info'">
                {{ authStore.isAdmin ? '管理员' : '普通用户' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="注册时间">
              <span class="form-text">{{ authStore.userInfo?.created_at || '-' }}</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="saving" @click="handleSaveInfo">保存修改</el-button>
              <el-button @click="handleResetInfo">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- 修改密码 -->
        <el-card shadow="never" class="form-card">
          <template #header>
            <span class="card-title">修改密码</span>
          </template>
          <el-form
            ref="pwdFormRef"
            :model="pwdForm"
            :rules="pwdRules"
            label-width="80px"
            label-position="left"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input v-model="pwdForm.old_password" type="password" placeholder="请输入当前密码" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input v-model="pwdForm.new_password" type="password" placeholder="至少6位，含字母和数字" show-password />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm_password">
              <el-input v-model="pwdForm.confirm_password" type="password" placeholder="请再次输入新密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="changingPwd" @click="handleChangePwd">修改密码</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { getUserDetail, updateUser } from '@/api/user'
import type { UserDetail } from '@/types/api'

const authStore = useAuthStore()
const formatMoney = (value: number): string => `¥${Number(value || 0).toFixed(2)}`

// ==================== 状态 ====================
const saving = ref(false)
const changingPwd = ref(false)
const userDetail = ref<UserDetail | null>(null)
const infoFormRef = ref<FormInstance>()
const pwdFormRef = ref<FormInstance>()

const infoForm = reactive({
  nickname: '',
  email: '',
  phone: '',
})

const infoRules: FormRules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [{ type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }],
}

const pwdForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPwd = (_rule: any, value: string, callback: (e?: Error) => void) => {
  if (value !== pwdForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const pwdRules: FormRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
    { pattern: /^(?=.*[a-zA-Z])(?=.*\d)/, message: '密码需包含字母和数字', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' },
  ],
}

// ==================== 初始化 ====================
onMounted(() => {
  loadUserDetail()
  resetForm()
})

const loadUserDetail = async () => {
  if (!authStore.userInfo?.id) return
  try {
    const res = await getUserDetail(authStore.userInfo.id)
    userDetail.value = res.data
  } catch {
    // 忽略加载失败
  }
}

const resetForm = () => {
  infoForm.nickname = authStore.userInfo?.nickname || ''
  infoForm.email = (userDetail.value as any)?.email || ''
  infoForm.phone = (userDetail.value as any)?.phone || ''
}

watch(userDetail, () => {
  resetForm()
})

// ==================== 保存信息 ====================
const handleSaveInfo = async () => {
  if (!infoFormRef.value) return
  await infoFormRef.value.validate(async (valid) => {
    if (!valid || !authStore.userInfo) return
    saving.value = true
    try {
      await updateUser(authStore.userInfo.id, {
        nickname: infoForm.nickname,
        email: infoForm.email,
        phone: infoForm.phone,
      } as any)
      // 更新 Store 中的用户信息
      authStore.userInfo = {
        ...authStore.userInfo,
        nickname: infoForm.nickname,
      }
      ElMessage.success('个人信息修改成功')
    } catch {
      ElMessage.error('修改失败，请稍后重试')
    } finally {
      saving.value = false
    }
  })
}

const handleResetInfo = () => {
  resetForm()
  infoFormRef.value?.resetFields()
  ElMessage.info('已重置')
}

// ==================== 修改密码 ====================
const handleChangePwd = async () => {
  if (!pwdFormRef.value) return
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid || !authStore.userInfo) return
    changingPwd.value = true
    try {
      await updateUser(authStore.userInfo.id, {
        password: pwdForm.new_password,
        old_password: pwdForm.old_password,
      } as any)
      ElMessage.success('密码修改成功，请重新登录')
      pwdForm.old_password = ''
      pwdForm.new_password = ''
      pwdForm.confirm_password = ''
      pwdFormRef.value?.resetFields()
      // 密码修改后需要重新登录
      setTimeout(() => authStore.logout(), 1500)
    } catch {
      ElMessage.error('密码修改失败，请确认当前密码正确')
    } finally {
      changingPwd.value = false
    }
  })
}
</script>

<style lang="scss" scoped>
.profile-page { max-width: 960px; }

.page-header {
  margin-bottom: 24px;
  h2 { font-size: 22px; font-weight: 700; color: var(--text-primary); margin: 0 0 4px 0; }
  .page-desc { font-size: 13px; color: var(--text-secondary); margin: 0; }
}

.profile-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
}

.profile-card {
  background: #fff;
  border-radius: 12px;
  padding: 32px 24px 20px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  height: fit-content;
  position: sticky;
  top: 24px;

  .card-avatar { margin-bottom: 12px; }
  .card-info {
    h3 { font-size: 18px; margin: 8px 0 4px; color: var(--text-primary); }
    .card-username { font-size: 13px; color: var(--text-secondary); margin: 6px 0 0; }
    .el-tag { margin-top: 4px; }
  }

  .card-stats {
    display: flex;
    justify-content: space-around;
    padding: 0 4px;
    .stat-item {
      display: flex; flex-direction: column; align-items: center;
      .stat-value { font-size: 16px; font-weight: 700; color: #6c5ce7; }
      .stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
    }
  }
}

.profile-forms {
  display: flex; flex-direction: column; gap: 20px;

  .form-card {
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
    .card-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
  }
}

.form-text { color: var(--text-secondary); font-size: 14px; }

// responsive
@media (max-width: 768px) {
  .profile-content { grid-template-columns: 1fr; }
  .profile-card { position: static; }
}
</style>
