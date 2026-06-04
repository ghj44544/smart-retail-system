<!--
  =====================================================
  src/views/users/index.vue
  用户列表页 - 表格展示 + 搜索筛选 + CRUD 操作
  严格遵循 API 文档第三章: 用户管理接口
  支持: 分页、关键词搜索、角色筛选、新增、编辑、删除
  =====================================================
-->
<template>
  <div class="user-list-page">
    <!-- ========== 页面标题栏 ========== -->
    <div class="page-header">
      <div>
        <h2 class="page-title">用户分析</h2>
        <p class="page-subtitle">管理平台用户，查看用户消费行为数据</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="handleAdd">
        新增用户
      </el-button>
    </div>

    <!-- ========== 统计概览卡片 ========== -->
    <div class="stats-row">
      <div class="stat-card" v-for="item in statCards" :key="item.label">
        <div class="stat-card-icon" :style="{ background: item.bg }">
          <component :is="item.icon" :size="20" />
        </div>
        <div class="stat-card-info">
          <div class="stat-card-value">{{ item.value }}</div>
          <div class="stat-card-label">{{ item.label }}</div>
        </div>
      </div>
    </div>

    <!-- ========== 搜索筛选栏 ========== -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索用户名或昵称..."
          :prefix-icon="Search"
          clearable
          class="filter-input"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-select
          v-model="filterRole"
          placeholder="全部角色"
          clearable
          class="filter-select"
          @change="handleSearch"
        >
          <el-option label="管理员" value="admin" />
          <el-option label="普通用户" value="user" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">
          搜索
        </el-button>
        <el-button :icon="RefreshRight" @click="handleReset">
          重置
        </el-button>
      </div>
    </el-card>

    <!-- ========== 用户表格 ========== -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="userList"
        stripe
        border
        style="width: 100%"
        row-key="id"
      >
        <!-- 用户ID -->
        <el-table-column prop="id" label="ID" width="70" align="center" />

        <!-- 用户名 -->
        <el-table-column prop="username" label="用户名" min-width="120">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row.id)">
              {{ row.username }}
            </el-link>
          </template>
        </el-table-column>

        <!-- 昵称 -->
        <el-table-column prop="nickname" label="昵称" min-width="100" />

        <!-- 角色 -->
        <el-table-column prop="role" label="角色" width="100" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.role === 'admin' ? 'primary' : 'info'"
              size="small"
              effect="light"
            >
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>

        <!-- 邮箱 -->
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />

        <!-- 手机号 -->
        <el-table-column prop="phone" label="手机号" width="130" />

        <!-- 累计消费 -->
        <el-table-column label="累计消费" width="130" align="right">
          <template #default="{ row }">
            <span class="amount-text">¥{{ row.total_consumption.toFixed(2) }}</span>
          </template>
        </el-table-column>

        <!-- 订单数 -->
        <el-table-column prop="order_count" label="订单数" width="90" align="center">
          <template #default="{ row }">
            <el-badge :value="row.order_count" :type="row.order_count > 20 ? 'primary' : 'info'" />
          </template>
        </el-table-column>

        <!-- 注册时间 -->
        <el-table-column label="注册时间" width="170">
          <template #default="{ row }">
            <span class="time-text">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="180" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleViewDetail(row.id)">
              详情
            </el-button>
            <el-button link type="success" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-popconfirm
              title="确定要删除该用户吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- ========== 新增/编辑用户对话框 ========== -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="540px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        label-position="right"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" maxlength="20" />
        </el-form-item>
        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="formData.nickname" placeholder="请输入昵称" maxlength="20" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" placeholder="请输入手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入初始密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ isEdit ? '保 存' : '创 建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 用户列表页逻辑
// =====================================================
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  Plus, Search, RefreshRight, User, UserFilled, Coin, List,
} from '@element-plus/icons-vue'
import {
  getUserList, createUser, updateUser, deleteUser,
} from '@/api/user'
import type { UserItem, UserQueryParams } from '@/types/api'

// ==================== 依赖注入 ====================

const router = useRouter()

// ==================== 状态定义 ====================

/** 表格加载状态 */
const loading = ref(false)

/** 用户列表数据 */
const userList = ref<UserItem[]>([])

/** 搜索关键词 */
const searchKeyword = ref('')

/** 角色筛选 */
const filterRole = ref('')

/** 分页参数 */
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

const userStats = reactive({
  total: 0,
  admins: 0,
  total_consumption: 0,
  order_count: 0,
})

// ==================== 统计概览卡片 ====================

/** 用户统计概览 */
const statCards = computed(() => [
  {
    label: '用户总数',
    value: userStats.total.toLocaleString(),
    icon: UserFilled,
    bg: 'linear-gradient(135deg, rgba(108,92,231,0.12), rgba(162,155,254,0.06))',
  },
  {
    label: '管理员',
    value: userStats.admins + ' 人',
    icon: User,
    bg: 'linear-gradient(135deg, rgba(0,184,148,0.12), rgba(85,239,196,0.06))',
  },
  {
    label: '消费总额',
    value: '¥' + userStats.total_consumption.toFixed(2),
    icon: Coin,
    bg: 'linear-gradient(135deg, rgba(116,185,255,0.12), rgba(116,185,255,0.06))',
  },
  {
    label: '总订单数',
    value: userStats.order_count.toLocaleString(),
    icon: List,
    bg: 'linear-gradient(135deg, rgba(253,203,110,0.12), rgba(253,203,110,0.06))',
  },
])

// ==================== 对话框相关 ====================

const dialogVisible = ref(false)
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const editingUserId = ref<number | null>(null)

/** 表单数据 */
const formData = reactive({
  username: '',
  nickname: '',
  email: '',
  phone: '',
  role: 'user' as string,
  password: '',
})

/** 表单验证规则 */
const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '3-20个字符', trigger: 'blur' },
  ],
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

// ==================== 工具函数 ====================

/** 格式化日期 - 将 ISO 字符串转为可读格式 */
const formatDate = (dateStr: string): string => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

/** 构建查询参数 */
const buildQueryParams = (): UserQueryParams => ({
  page: pagination.page,
  page_size: pagination.pageSize,
  keyword: searchKeyword.value || undefined,
  role: filterRole.value || undefined,
})

// ==================== 数据加载 ====================

/** 加载用户列表 */
const loadList = async (): Promise<void> => {
  loading.value = true
  try {
    const res = await getUserList(buildQueryParams())
    userList.value = res.data.items
    pagination.total = res.data.total
    userStats.total = res.data.stats?.total ?? res.data.total
    userStats.admins = res.data.stats?.admins ?? 0
    userStats.total_consumption = res.data.stats?.total_consumption ?? 0
    userStats.order_count = res.data.stats?.order_count ?? 0
  } catch {
    // 错误由 request 拦截器处理
  } finally {
    loading.value = false
  }
}

/** 搜索 - 重置到第一页 */
const handleSearch = (): void => {
  pagination.page = 1
  loadList()
}

/** 重置搜索条件 */
const handleReset = (): void => {
  searchKeyword.value = ''
  filterRole.value = ''
  pagination.page = 1
  loadList()
}

/** 分页大小改变 */
const handleSizeChange = (): void => {
  pagination.page = 1
  loadList()
}

/** 页码改变 */
const handlePageChange = (): void => {
  loadList()
}

// ==================== CRUD 操作 ====================

/** 打开新增对话框 */
const handleAdd = (): void => {
  isEdit.value = false
  editingUserId.value = null
  formData.username = ''
  formData.nickname = ''
  formData.email = ''
  formData.phone = ''
  formData.role = 'user'
  formData.password = ''
  dialogVisible.value = true
}

/** 打开编辑对话框 */
const handleEdit = (row: UserItem): void => {
  isEdit.value = true
  editingUserId.value = row.id
  formData.username = row.username
  formData.nickname = row.nickname
  formData.email = row.email
  formData.phone = row.phone
  formData.role = row.role
  formData.password = ''
  dialogVisible.value = true
}

/** 提交表单（新增/编辑） */
const handleSubmit = async (): Promise<void> => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value && editingUserId.value) {
      // 编辑用户 - API 3.4: PUT /users/{user_id}
      await updateUser(editingUserId.value, {
        username: formData.username,
        nickname: formData.nickname,
        email: formData.email,
        phone: formData.phone,
        role: formData.role,
      } as any)
      ElMessage.success('用户信息更新成功')
    } else {
      // 新增用户 - API 3.3: POST /users
      await createUser({
        username: formData.username,
        nickname: formData.nickname,
        email: formData.email,
        phone: formData.phone,
        role: formData.role,
        password: formData.password,
      })
      ElMessage.success('用户创建成功')
    }
    dialogVisible.value = false
    loadList()
  } catch {
    // 错误已处理
  } finally {
    submitting.value = false
  }
}

/** 删除用户 - API 3.5: DELETE /users/{user_id} */
const handleDelete = async (userId: number): Promise<void> => {
  try {
    await deleteUser(userId)
    ElMessage.success('用户已删除')
    // 如果删除后当前页空了，返回上一页
    if (userList.value.length === 1 && pagination.page > 1) {
      pagination.page--
    }
    loadList()
  } catch {
    // 错误已处理
  }
}

/** 查看用户详情 - 跳转到详情页 */
const handleViewDetail = (userId: number): void => {
  router.push(`/users/${userId}`)
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadList()
})
</script>

<style lang="scss" scoped>
.user-list-page {
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ========== 页面头部 ========== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #2d3436;
  background: linear-gradient(135deg, #6c5ce7, #a29bfe);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  font-size: 13px;
  color: #b2bec3;
  margin-top: 4px;
}

/* ========== 统计卡片 ========== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid var(--border-light);
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }
}

.stat-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c5ce7;
  flex-shrink: 0;
}

.stat-card-value {
  font-size: 18px;
  font-weight: 700;
  color: #2d3436;
}

.stat-card-label {
  font-size: 12px;
  color: #b2bec3;
  margin-top: 2px;
}

/* ========== 筛选卡片 ========== */
.filter-card {
  margin-bottom: 16px;
  border: 1px solid var(--border-light);
  border-radius: 14px;

  :deep(.el-card__body) {
    padding: 16px 20px;
  }
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-input {
  width: 280px;
}

.filter-select {
  width: 140px;
}

/* ========== 表格卡片 ========== */
.table-card {
  border: 1px solid var(--border-light);
  border-radius: 14px;

  :deep(.el-card__body) {
    padding: 0;
  }
}

/* 表格样式微调 */
:deep(.el-table) {
  --el-table-border-color: #f0f3f7;

  th.el-table__cell {
    background: rgba(108, 92, 231, 0.03);
    color: #636e72;
    font-weight: 600;
    font-size: 13px;
    height: 48px;
  }

  td.el-table__cell {
    font-size: 13px;
    height: 52px;
  }

  .el-table__row:hover > td {
    background: rgba(108, 92, 231, 0.03);
  }
}

.amount-text {
  color: #6c5ce7;
  font-weight: 600;
}

.time-text {
  color: #b2bec3;
  font-size: 12px;
}

/* 分页 */
.pagination-wrap {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
}

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: 1fr;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-input,
  .filter-select {
    width: 100%;
  }
}
</style>
