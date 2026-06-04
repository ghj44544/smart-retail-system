<!--
  =====================================================
  src/views/orders/detail.vue
  订单详情页
  严格遵循 API 文档 5.2: GET /orders/{order_id}
  =====================================================
-->
<template>
  <div class="order-detail-page">
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="goBack">返回列表</el-button>
      <h2 class="page-title">{{ detail?.order_no || '订单详情' }}</h2>
      <el-tag v-if="detail" :type="tagType" effect="light" size="large">
        {{ statusLabels[detail.status] }}
      </el-tag>
    </div>

    <div v-loading="loading" class="detail-content">
      <template v-if="detail">
        <!-- 订单信息 -->
        <el-card class="info-card" shadow="never">
          <template #header><h3>订单信息</h3></template>
          <div class="info-grid">
            <div class="info-item"><span class="info-label">订单编号</span><span class="info-value mono">{{ detail.order_no }}</span></div>
            <div class="info-item"><span class="info-label">下单用户</span><span class="info-value">{{ detail.user_name }} (ID: {{ detail.user_id }})</span></div>
            <div class="info-item"><span class="info-label">订单金额</span><span class="info-value amount">¥{{ detail.total_amount.toFixed(2) }}</span></div>
            <div class="info-item"><span class="info-label">商品数量</span><span class="info-value">{{ detail.item_count }} 件</span></div>
            <div class="info-item"><span class="info-label">下单时间</span><span class="info-value time">{{ formatDate(detail.created_at) }}</span></div>
            <div class="info-item"><span class="info-label">支付时间</span><span class="info-value time">{{ formatDate(detail.paid_at) }}</span></div>
            <div class="info-item"><span class="info-label">完成时间</span><span class="info-value time">{{ formatDate(detail.completed_at) }}</span></div>
            <div class="info-item"><span class="info-label">当前状态</span><span class="info-value"><el-tag :type="tagType" effect="light">{{ statusLabels[detail.status] }}</el-tag></span></div>
          </div>
        </el-card>

        <!-- 订单进度 -->
        <el-card class="info-card" shadow="never">
          <template #header><h3>订单进度</h3></template>
          <el-steps :active="statusStep" align-center finish-status="success" process-status="process">
            <el-step
              v-for="(l, k) in statusLabels" :key="k"
              :title="l"
              :description="k === detail.status ? '当前状态' : ''"
              :status="statusKeys.indexOf(k) < statusKeys.indexOf(detail.status) ? 'success' : k === detail.status ? 'process' : 'wait'"
            />
          </el-steps>
        </el-card>

        <!-- 商品明细 -->
        <el-card class="info-card" shadow="never">
          <template #header><h3>商品明细</h3></template>
          <el-table :data="detail.items" stripe border>
            <el-table-column prop="product_id" label="商品ID" width="90" align="center" />
            <el-table-column prop="product_name" label="商品名称" min-width="180">
              <template #default="{ row }">
                <el-link type="primary" @click="$router.push('/products/' + row.product_id)">{{ row.product_name }}</el-link>
              </template>
            </el-table-column>
            <el-table-column label="单价" width="110" align="right">
              <template #default="{ row }"><span class="price">¥{{ row.price.toFixed(2) }}</span></template>
            </el-table-column>
            <el-table-column prop="quantity" label="数量" width="80" align="center" />
            <el-table-column label="小计" width="120" align="right">
              <template #default="{ row }"><span class="amount">¥{{ (row.price * row.quantity).toFixed(2) }}</span></template>
            </el-table-column>
          </el-table>

          <!-- 金额汇总 -->
          <div class="amount-summary">
            <div class="amount-row">
              <span>商品金额</span>
              <span class="amount">¥{{ detail.total_amount.toFixed(2) }}</span>
            </div>
            <div class="amount-row">
              <span>运费</span>
              <span class="free">免运费</span>
            </div>
            <div class="amount-row total-row">
              <span>实付金额</span>
              <span class="total-amount">¥{{ detail.total_amount.toFixed(2) }}</span>
            </div>
          </div>
        </el-card>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 订单详情页逻辑
// =====================================================
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getOrderDetail } from '@/api/order'
import type { OrderDetail } from '@/types/api'

const route = useRoute()
const router = useRouter()
const orderId = computed(() => Number(route.params.id))

const statusLabels: Record<string, string> = { pending: '待支付', paid: '已支付', shipped: '已发货', completed: '已完成', cancelled: '已取消' }
const statusKeys = Object.keys(statusLabels)

const tagType = computed(() => {
  const m: Record<string, string> = { pending: 'warning', paid: 'primary', shipped: '', completed: 'success', cancelled: 'danger' }
  return detail.value ? (m[detail.value.status] || 'info') : 'info'
})

const loading = ref(false)
const detail = ref<OrderDetail | null>(null)

const statusStep = computed(() => {
  if (!detail.value) return 0
  return statusKeys.indexOf(detail.value.status)
})

const formatDate = (s?: string) => s ? new Date(s).toLocaleString('zh-CN') : '--'

const loadData = async () => {
  loading.value = true
  try { const res = await getOrderDetail(orderId.value); detail.value = res.data } catch {/* */} finally { loading.value = false }
}

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.push('/orders')
}

watch(orderId, () => loadData())
onMounted(() => loadData())
</script>

<style lang="scss" scoped>
.order-detail-page { max-width: 900px; margin: 0 auto; animation: fadeIn 0.5s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.page-title { font-size: 20px; font-weight: 700; color: #2d3436; }

.detail-content { min-height: 400px; }
.info-card { border: 1px solid var(--border-light); border-radius: 14px; margin-bottom: 16px;
  :deep(.el-card__header) { padding: 16px 20px; border-bottom: 1px solid var(--border-light);
    h3 { margin: 0; font-size: 15px; font-weight: 700; color: #2d3436; }
  }
  :deep(.el-card__body) { padding: 20px; }
}

.info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0; border: 1px solid var(--border-light); border-radius: 12px; overflow: hidden; }
.info-item { display: flex; padding: 14px 18px; border-bottom: 1px solid var(--border-light);
  &:nth-child(odd) { border-right: 1px solid var(--border-light); }
  &:nth-last-child(-n+2) { border-bottom: none; }
}
.info-label { width: 80px; font-size: 13px; color: #b2bec3; flex-shrink: 0; }
.info-value { font-size: 14px; color: #2d3436; font-weight: 500;
  &.amount { color: #6c5ce7; font-weight: 600; }
  &.time { color: #b2bec3; font-size: 13px; }
  &.mono { font-family: 'Courier New', monospace; }
}

/* 表格 */
:deep(.el-table) {
  --el-table-border-color: #f0f3f7;
  th.el-table__cell { background: rgba(108,92,231,0.03); color: #636e72; font-weight: 600; }
}
.price { color: #636e72; }
.amount { color: #6c5ce7; font-weight: 600; }

/* 金额汇总 */
.amount-summary { margin-top: 20px; border-top: 1px solid var(--border-light); padding-top: 16px; display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.amount-row { display: flex; justify-content: space-between; width: 240px; font-size: 14px; color: #636e72; }
.total-row { margin-top: 8px; padding-top: 8px; border-top: 1px dashed var(--border-light); }
.free { color: #00b894; font-weight: 500; }
.total-amount { font-size: 18px; font-weight: 700; color: #e17055 !important; }

@media (max-width: 768px) { .info-grid { grid-template-columns: 1fr; } .amount-row { width: 100%; } }
</style>
