<!--
  =====================================================
  src/views/orders/index.vue
  订单管理列表页
  严格遵循 API 文档 5.1-5.5
  功能: 订单列表、状态筛选、日期筛选、状态流转、销售趋势图
  =====================================================
-->
<template>
  <div class="order-page">
    <!-- ========== 页面标题 ========== -->
    <div class="page-header">
      <div>
        <h2 class="page-title">订单管理</h2>
        <p class="page-subtitle">管理平台订单，跟踪订单状态，分析销售趋势</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="handleAdd">创建订单</el-button>
    </div>

    <!-- ========== 统计卡片 ========== -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in statCards" :key="s.label" :style="{ '--sc': s.color }">
        <div class="stat-icon" :style="{ background: s.bg }"><component :is="s.icon" :size="20" /></div>
        <div class="stat-info"><div class="stat-value">{{ s.value }}</div><div class="stat-label">{{ s.label }}</div></div>
      </div>
    </div>

    <!-- ========== 销售趋势图 ========== -->
    <el-card class="chart-card" shadow="never">
      <template #header>
        <div class="chart-card-hd">
          <h3>销售趋势</h3>
          <el-radio-group v-model="trendDays" size="small" @change="loadTrend">
            <el-radio-button :value="7">近7天</el-radio-button>
            <el-radio-button :value="30">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </template>
      <div ref="trendChartRef" style="width:100%;height:300px"></div>
    </el-card>

    <!-- ========== 筛选栏 ========== -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width:130px" @change="handleSearch">
          <el-option v-for="(l, k) in statusLabels" :key="k" :label="l" :value="k" />
        </el-select>
        <el-date-picker
          v-model="dateRange" type="daterange" range-separator="至"
          start-placeholder="开始日期" end-placeholder="结束日期"
          format="YYYY-MM-DD" value-format="YYYY-MM-DD"
          style="width:260px" @change="handleSearch"
        />
        <el-select
          v-model="filterUserId"
          filterable
          remote
          clearable
          reserve-keyword
          placeholder="搜索用户"
          style="width:180px"
          :remote-method="loadUserOptions"
          @change="handleSearch"
          @focus="loadUserOptions('')"
        >
          <el-option
            v-for="u in userOptions"
            :key="u.id"
            :label="`${u.nickname || u.username} (${u.id})`"
            :value="u.id"
          />
        </el-select>
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button :icon="RefreshRight" @click="handleReset">重置</el-button>
      </div>
    </el-card>

    <!-- ========== 订单表格 ========== -->
    <el-card class="table-card" shadow="never">
      <el-table v-loading="loading" :data="orderList" stripe border row-key="id" :scrollbar-always-on="true">
        <el-table-column prop="id" label="ID" width="86" align="center" />
        <el-table-column prop="order_no" label="订单编号" width="170" />
        <el-table-column prop="user_name" label="用户" width="120" />
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }"><span class="amount">¥{{ row.total_amount.toFixed(2) }}</span></template>
        </el-table-column>
        <el-table-column prop="item_count" label="商品数" width="90" align="center" />
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="light" size="small">
              {{ statusLabels[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态流转" width="460">
          <template #default="{ row }">
            <div class="status-flow" :class="{ cancelled: row.status === 'cancelled' }">
              <div
                v-for="(step, index) in orderStatusSteps"
                :key="step.key"
                class="flow-step"
                :class="flowStepClass(row.status, index)"
              >
                <span class="flow-dot">{{ row.status === 'cancelled' ? '×' : index + 1 }}</span>
                <span class="flow-title">{{ row.status === 'cancelled' ? '已取消' : step.label }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button link type="primary" size="small" @click="handleViewDetail(row.id)">详情</el-button>
              <el-dropdown trigger="click" @command="(cmd: string) => handleStatusChange(row, cmd)">
                <el-button link type="warning" size="small">
                  流转 <el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-for="(l, k) in statusLabels" :key="k"
                      :command="k" :disabled="k === row.status"
                    >{{ l }}</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper" background
          @size-change="handleSizeChange" @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- ========== 创建订单对话框 ========== -->
    <el-dialog v-model="dialogVisible" title="创建订单" width="480px" :close-on-click-modal="false" destroy-on-close>
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="80px">
        <el-form-item label="用户ID" prop="user_id">
          <el-select
            v-model="formData.user_id"
            filterable
            remote
            reserve-keyword
            placeholder="搜索用户"
            style="width:100%"
            :remote-method="loadUserOptions"
            @focus="loadUserOptions('')"
          >
            <el-option
              v-for="u in userOptions"
              :key="u.id"
              :label="`${u.nickname || u.username} (${u.id})`"
              :value="u.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="商品">
          <div v-for="(item, idx) in formData.items" :key="idx" class="order-item-row">
            <el-input-number v-model="item.product_id" :min="1" placeholder="商品ID" controls-position="right" style="width:140px" />
            <el-input-number v-model="item.quantity" :min="1" placeholder="数量" controls-position="right" style="width:100px" />
            <el-button :icon="Delete" circle size="small" @click="removeItem(idx)" v-if="formData.items.length > 1" />
          </div>
          <el-button type="primary" link :icon="Plus" @click="addItem" size="small">添加商品</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">创 建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 订单列表页逻辑
// =====================================================
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Search, RefreshRight, Delete, ArrowDown, List, Coin, Goods, ShoppingCart } from '@element-plus/icons-vue'
import { getOrderList, updateOrderStatus, createOrder, getOrderTrend } from '@/api/order'
import { getUserList } from '@/api/user'
import type { OrderItem, OrderQueryParams, UserItem } from '@/types/api'

const router = useRouter()

type OrderPageCache = {
  orderList: OrderItem[]
  filterStatus: string
  dateRange: [string, string] | null
  filterUserId: number | null
  userOptions: UserItem[]
  pagination: { page: number; pageSize: number; total: number }
  orderStats: { total: number; sales_amount: number; completed: number; pending: number; cancelled: number }
  trendDays: number
  trendOption: EChartsOption | null
}

let orderPageCache: OrderPageCache | null = null

const statusLabels: Record<string, string> = {
  pending: '待支付', paid: '已支付', shipped: '已发货', completed: '已完成', cancelled: '已取消',
}

const statusTagType = (s: string): string => {
  const m: Record<string, string> = { pending: 'warning', paid: 'primary', shipped: '', completed: 'success', cancelled: 'danger' }
  return m[s] || 'info'
}

const orderStatusSteps = [
  { key: 'pending', label: '待支付' },
  { key: 'paid', label: '已支付' },
  { key: 'shipped', label: '已发货' },
  { key: 'completed', label: '已完成' },
  { key: 'cancelled', label: '已取消' },
]

const flowStepClass = (status: string, index: number): string => {
  if (status === 'cancelled') return 'is-cancelled'
  const currentIndex = orderStatusSteps.findIndex((s) => s.key === status)
  if (index < currentIndex) return 'is-done'
  if (index === currentIndex) return 'is-current'
  return 'is-wait'
}

const statusStep = (s: string): number => {
  const keys = Object.keys(statusLabels)
  const idx = keys.indexOf(s)
  return idx === keys.length - 1 ? idx : idx
}

// ==================== 状态 ====================

const loading = ref(false)
const orderList = ref<OrderItem[]>([])
const filterStatus = ref('')
const dateRange = ref<[string, string] | null>(null)
const filterUserId = ref<number | null>(null)
const userOptions = ref<UserItem[]>([])
const orderStats = reactive({ total: 0, sales_amount: 0, completed: 0, pending: 0, cancelled: 0 })

const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const trendDays = ref(30)
const trendChartRef = ref<HTMLDivElement | null>(null)
let trendChart: echarts.ECharts | null = null

const statCards = computed(() => [
  { label: '订单总数', value: orderStats.total + ' 笔', icon: List, color: '#6c5ce7', bg: 'rgba(108,92,231,0.08)' },
  { label: '成交金额', value: '¥' + orderStats.sales_amount.toFixed(2), icon: Coin, color: '#00b894', bg: 'rgba(0,184,148,0.08)' },
  { label: '已完成', value: orderStats.completed + ' 笔', icon: ShoppingCart, color: '#74b9ff', bg: 'rgba(116,185,255,0.08)' },
  { label: '待处理', value: orderStats.pending + ' 笔', icon: Goods, color: '#fdcb6e', bg: 'rgba(253,203,110,0.08)' },
])

const formatDate = (s: string) => s ? new Date(s).toLocaleString('zh-CN') : '--'

// 对话框
const dialogVisible = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const formData = reactive({ user_id: 1, items: [{ product_id: 1, quantity: 1 }] })
const formRules: FormRules = { user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }] }
const addItem = () => formData.items.push({ product_id: 1, quantity: 1 })
const removeItem = (i: number) => formData.items.splice(i, 1)

// ==================== 数据加载 ====================

const buildQuery = (): OrderQueryParams => ({
  page: pagination.page, page_size: pagination.pageSize,
  status: filterStatus.value || undefined,
  user_id: filterUserId.value || undefined,
  start_date: dateRange.value?.[0],
  end_date: dateRange.value?.[1],
})

const applyStats = (stats?: Record<string, number>) => {
  orderStats.total = stats?.total ?? pagination.total
  orderStats.sales_amount = stats?.sales_amount ?? 0
  orderStats.completed = stats?.completed ?? 0
  orderStats.pending = stats?.pending ?? 0
  orderStats.cancelled = stats?.cancelled ?? 0
}

const loadUserOptions = async (keyword = '') => {
  try {
    const res = await getUserList({ page: 1, page_size: 20, keyword: keyword || undefined })
    userOptions.value = res.data.items
  } catch { /* handled by request interceptor */ }
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await getOrderList(buildQuery())
    orderList.value = res.data.items
    pagination.total = res.data.total
    applyStats(res.data.stats)
  } catch { ElMessage.error('订单数据加载失败') } finally { loading.value = false }
}

const loadTrend = async () => {
  try {
    const res = await getOrderTrend('day', trendDays.value)
    if (!trendChartRef.value) return
    if (!trendChart) trendChart = echarts.init(trendChartRef.value)
    const d = res.data as any
    const opt: EChartsOption = {
      tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#e8ecf1', textStyle: { color: '#2d3436', fontSize: 13 }, padding: [10,14], extraCssText: 'border-radius:8px;' },
      legend: { data: ['销售额(元)', '订单量(笔)'], bottom: 0, textStyle: { color: '#636e72', fontSize: 11 } },
      grid: { left: '3%', right: '4%', bottom: '12%', top: '8%', containLabel: true },
      xAxis: { type: 'category', data: d.dates, axisLabel: { color: '#b2bec3', fontSize: 10, formatter: (v: string) => v.slice(5) } },
      yAxis: [
        { type: 'value', name: '元', nameTextStyle: { color: '#b2bec3', fontSize: 11 }, axisLabel: { color: '#b2bec3', fontSize: 11, formatter: (v: number) => v >= 10000 ? (v / 10000).toFixed(1) + '万' : String(v) }, splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } } },
        { type: 'value', name: '笔', nameTextStyle: { color: '#b2bec3', fontSize: 11 }, axisLabel: { color: '#b2bec3', fontSize: 11 }, splitLine: { show: false } },
      ],
      series: [
        { name: '销售额(元)', type: 'bar', yAxisIndex: 0, data: d.sales, barWidth: 14, itemStyle: { color: 'rgba(108,92,231,0.25)', borderRadius: [6,6,0,0] }, emphasis: { itemStyle: { color: 'rgba(108,92,231,0.5)' } } },
        { name: '订单量(笔)', type: 'line', yAxisIndex: 1, data: d.orders, smooth: true, symbol: 'circle', symbolSize: 6, lineStyle: { color: '#00b894', width: 3 }, itemStyle: { color: '#00b894', borderColor: '#fff', borderWidth: 2 } },
      ],
    }
    trendChart.setOption(opt)
    if (orderPageCache) orderPageCache.trendOption = opt
  } catch {/* */}
}

const handleSearch = () => { pagination.page = 1; loadList() }
const handleReset = () => { filterStatus.value = ''; dateRange.value = null; filterUserId.value = null; pagination.page = 1; loadList() }
const handleSizeChange = () => { pagination.page = 1; loadList() }
const handlePageChange = () => { loadList() }

// ==================== 状态流转 ====================

const handleStatusChange = async (row: OrderItem, status: string) => {
  try {
    await updateOrderStatus(row.id, status)
    row.status = status
    ElMessage.success(`已更新为「${statusLabels[status]}」`)
  } catch {/* */}
}

// 创建订单
const handleAdd = () => {
  if (!userOptions.value.length) loadUserOptions('')
  formData.user_id = userOptions.value[0]?.id || 1
  formData.items = [{ product_id: 1, quantity: 1 }]
  dialogVisible.value = true
}
const handleSubmit = async () => {
  if (!formRef.value) return
  try { await formRef.value.validate() } catch { return }
  submitting.value = true
  try {
    await createOrder({ user_id: formData.user_id, items: formData.items.map((i) => ({ product_id: i.product_id, quantity: i.quantity })) })
    ElMessage.success('订单创建成功')
    dialogVisible.value = false; loadList()
  } catch {/* */} finally { submitting.value = false }
}

const handleViewDetail = (id: number) => router.push(`/orders/${id}`)

// 生命周期
const handleResize = () => trendChart?.resize()

const savePageCache = () => {
  orderPageCache = {
    orderList: orderList.value,
    filterStatus: filterStatus.value,
    dateRange: dateRange.value ? [...dateRange.value] as [string, string] : null,
    filterUserId: filterUserId.value,
    userOptions: userOptions.value,
    pagination: { ...pagination },
    orderStats: { ...orderStats },
    trendDays: trendDays.value,
    trendOption: trendChart?.getOption() as EChartsOption || orderPageCache?.trendOption || null,
  }
}

const restorePageCache = () => {
  if (!orderPageCache) return false
  orderList.value = orderPageCache.orderList
  filterStatus.value = orderPageCache.filterStatus
  dateRange.value = orderPageCache.dateRange
  filterUserId.value = orderPageCache.filterUserId
  userOptions.value = orderPageCache.userOptions
  pagination.page = orderPageCache.pagination.page
  pagination.pageSize = orderPageCache.pagination.pageSize
  pagination.total = orderPageCache.pagination.total
  Object.assign(orderStats, orderPageCache.orderStats)
  trendDays.value = orderPageCache.trendDays
  nextTick(() => {
    if (trendChartRef.value && orderPageCache?.trendOption) {
      trendChart = echarts.init(trendChartRef.value)
      trendChart.setOption(orderPageCache.trendOption)
    }
  })
  return true
}

onMounted(() => {
  const restored = restorePageCache()
  if (!restored) {
    loadList()
    loadTrend()
    loadUserOptions('')
  }
  window.addEventListener('resize', handleResize)
})
onBeforeUnmount(() => { savePageCache(); trendChart?.dispose(); window.removeEventListener('resize', handleResize) })
</script>

<style lang="scss" scoped>
.order-page { max-width: 1500px; margin: 0 auto; animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-title { font-size: 22px; font-weight: 700; background: linear-gradient(135deg, #6c5ce7, #a29bfe); background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.page-subtitle { font-size: 13px; color: #b2bec3; margin-top: 4px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; gap: 14px; padding: 18px 20px; background: #fff; border-radius: 14px; border: 1px solid var(--border-light); border-left: 3px solid var(--sc); transition: all 0.3s;
  &:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
}
.stat-icon { width: 44px; height: 44px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: var(--sc); flex-shrink: 0; }
.stat-value { font-size: 18px; font-weight: 700; color: #2d3436; }
.stat-label { font-size: 12px; color: #b2bec3; }

.chart-card { border: 1px solid var(--border-light); border-radius: 14px; margin-bottom: 16px;
  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--border-light); }
  :deep(.el-card__body) { padding: 0; }
}
.chart-card-hd { display: flex; justify-content: space-between; align-items: center; h3 { margin: 0; font-size: 15px; font-weight: 700; color: #2d3436; } }

.filter-card { margin-bottom: 16px; border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__body) { padding: 16px 20px; }
}
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }

.table-card { border: 1px solid var(--border-light); border-radius: 14px;
  :deep(.el-card__body) { padding: 0; }
}
:deep(.el-table) {
  --el-table-border-color: #f0f3f7;
  th.el-table__cell { background: rgba(108,92,231,0.03); color: #636e72; font-weight: 600; font-size: 13px; height: 44px; }
  td.el-table__cell { font-size: 13px; }
  .cell { overflow: hidden; }
}
.amount { color: #6c5ce7; font-weight: 600; }
.pagination-wrap { display: flex; justify-content: flex-end; padding: 16px 20px; }

.status-flow {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  align-items: start;
  gap: 0;
  width: 100%;
  min-width: 0;
  padding: 2px 4px;
}

.flow-step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #9ca3af;

  &::before {
    content: '';
    position: absolute;
    top: 12px;
    left: calc(-50% + 12px);
    width: calc(100% - 24px);
    height: 2px;
    background: #d1d5db;
  }

  &:first-child::before {
    display: none;
  }
}

.flow-dot {
  z-index: 1;
  width: 24px;
  height: 24px;
  border: 2px solid currentColor;
  border-radius: 50%;
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.flow-title {
  font-size: 11px;
  white-space: nowrap;
}

.action-cell {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  white-space: nowrap;
}

.action-cell :deep(.el-button) {
  padding-left: 4px;
  padding-right: 4px;
}

.flow-step.is-done {
  color: #52c41a;

  &::before {
    background: #52c41a;
  }
}

.flow-step.is-current {
  color: #409eff;

  &::before {
    background: #52c41a;
  }
}

.flow-step.is-cancelled {
  color: #f56c6c;

  &::before {
    background: #f56c6c;
  }
}

.status-flow.cancelled .flow-title {
  visibility: hidden;
}

.status-flow.cancelled .flow-step:first-child .flow-title {
  visibility: visible;
}

.order-item-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }

@media (max-width: 992px) { .stats-row { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .stats-row { grid-template-columns: 1fr; } .filter-row { flex-direction: column; } }
</style>
