<!--
  =====================================================
  src/views/users/detail.vue
  用户详情页 - Tab 切换展示基础信息 + RFM 评分 + 聚类 + 用户画像
  严格遵循 API 文档:
    3.2 GET /users/{user_id} - 用户详情
    7.5 GET /analysis/profile/{user_id} - 用户画像
  =====================================================
-->
<template>
  <div class="user-detail-page">
    <!-- 返回按钮 + 标题 -->
    <div class="page-header">
      <el-button :icon="ArrowLeft" @click="$router.push('/users')">返回列表</el-button>
      <div class="page-header-info">
        <h2 class="page-title">{{ detail?.nickname || '用户详情' }}</h2>
        <el-tag :type="detail?.role === 'admin' ? 'primary' : 'info'" size="small" effect="light">
          {{ detail?.role === 'admin' ? '管理员' : '普通用户' }}
        </el-tag>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="border-card" class="detail-tabs">
      <!-- ========== Tab 1: 基本信息 ========== -->
      <el-tab-pane label="基本信息" name="basic">
        <div class="tab-content" v-loading="detailLoading">
          <div class="info-grid">
            <div class="info-item">
              <span class="info-label">用户ID</span>
              <span class="info-value">{{ detail?.id }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">用户名</span>
              <span class="info-value">{{ detail?.username }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">昵称</span>
              <span class="info-value">{{ detail?.nickname }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">邮箱</span>
              <span class="info-value">{{ detail?.email || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">手机号</span>
              <span class="info-value">{{ detail?.phone || '--' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">角色</span>
              <span class="info-value">{{ detail?.role === 'admin' ? '管理员' : '普通用户' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">累计消费</span>
              <span class="info-value amount">¥{{ detail?.total_consumption?.toFixed(2) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">订单数量</span>
              <span class="info-value">{{ detail?.order_count }} 笔</span>
            </div>
            <div class="info-item">
              <span class="info-label">客单价</span>
              <span class="info-value amount">¥{{ detail?.avg_order_value?.toFixed(2) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">最近购买</span>
              <span class="info-value">{{ formatDate(detail?.last_purchase) }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">注册时间</span>
              <span class="info-value">{{ formatDate(detail?.created_at) }}</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 2: RFM 评分 ========== -->
      <el-tab-pane label="RFM评分" name="rfm">
        <div class="tab-content" v-loading="detailLoading">
          <div class="rfm-section">
            <!-- RFM 评分卡片 -->
            <div class="rfm-cards">
              <div class="rfm-card" v-for="item in rfmCards" :key="item.key">
                <div class="rfm-card-circle" :style="{ '--percent': item.percent, '--color': item.color }">
                  <svg viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#f0f3f7" stroke-width="6" />
                    <circle
                      cx="50" cy="50" r="42" fill="none"
                      :stroke="item.color" stroke-width="6"
                      stroke-linecap="round"
                      :stroke-dasharray="264"
                      :stroke-dashoffset="264 - 264 * item.percent"
                      transform="rotate(-90 50 50)"
                    />
                  </svg>
                  <div class="rfm-card-center">
                    <span class="rfm-score">{{ item.value }}</span>
                    <span class="rfm-unit">/ 5分</span>
                  </div>
                </div>
                <div class="rfm-card-info">
                  <div class="rfm-card-name">{{ item.name }}</div>
                  <div class="rfm-card-desc">{{ item.desc }}</div>
                </div>
              </div>
            </div>

            <!-- RFM 雷达图 -->
            <el-card class="sub-chart-card" shadow="never">
              <template #header><h4>RFM 雷达图</h4></template>
              <div ref="rfmRadarRef" style="width:100%;height:350px"></div>
            </el-card>
          </div>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 3: 聚类信息 ========== -->
      <el-tab-pane label="聚类分析" name="cluster">
        <div class="tab-content" v-loading="detailLoading">
          <el-empty v-if="!detail" description="暂无聚类数据" />
          <template v-else>
            <div class="cluster-info">
              <div class="cluster-badge">
                <div class="cluster-circle" :style="{ background: clusterColor }">
                  {{ detail.cluster_label }}
                </div>
                <div class="cluster-meta">
                  <div class="cluster-name">{{ clusterName }}</div>
                  <div class="cluster-desc">{{ clusterDesc }}</div>
                </div>
              </div>
            </div>
            <el-alert
              title="说明"
              type="info"
              :closable="false"
              show-icon
              description="聚类标签由 K-Means 算法根据用户消费行为自动分配。取值范围 0-4，分别代表不同的用户群体。完整聚类可视化请查看「聚类分析」页面。"
              style="margin-top:16px"
            />
          </template>
        </div>
      </el-tab-pane>

      <!-- ========== Tab 4: 用户画像 ========== -->
      <el-tab-pane label="用户画像" name="profile">
        <div class="tab-content" v-loading="profileLoading">
          <el-empty v-if="!profile" description="暂无画像数据" />
          <template v-else>
            <!-- 用户标签 -->
            <div class="profile-tags">
              <h4>用户标签</h4>
              <div class="tags-wrap">
                <el-tag
                  v-for="tag in profile.tags"
                  :key="tag"
                  type="primary"
                  effect="light"
                  size="default"
                >
                  {{ tag }}
                </el-tag>
              </div>
            </div>

            <!-- 偏好分类 -->
            <div class="profile-charts">
              <el-card shadow="never">
                <template #header><h4>偏好商品分类</h4></template>
                <div ref="categoryChartRef" style="width:100%;height:280px"></div>
              </el-card>
            </div>

            <!-- 关键指标 -->
            <div class="profile-indicators">
              <div class="profile-indicator" v-for="ind in profileIndicators" :key="ind.label">
                <span class="ind-label">{{ ind.label }}</span>
                <span class="ind-value">{{ ind.value }}</span>
              </div>
            </div>
          </template>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
// =====================================================
// 用户详情页逻辑
// =====================================================
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import type { EChartsOption } from 'echarts'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getUserDetail } from '@/api/user'
import { getUserProfile } from '@/api/analysis'
import type { UserDetail, UserProfile } from '@/types/api'

// ==================== 路由参数 ====================

const route = useRoute()
const userId = computed(() => Number(route.params.id))

// ==================== 状态定义 ====================

const activeTab = ref('basic')
const detailLoading = ref(false)
const profileLoading = ref(false)
const detail = ref<UserDetail | null>(null)
const profile = ref<UserProfile | null>(null)

// ==================== 图表引用 ====================

const rfmRadarRef = ref<HTMLDivElement | null>(null)
const categoryChartRef = ref<HTMLDivElement | null>(null)

let rfmRadarChart: echarts.ECharts | null = null
let categoryChart: echarts.ECharts | null = null

// ==================== RFM 卡片数据 ====================

const rfmCards = computed(() => {
  const score = detail.value?.rfm_score
  return [
    {
      key: 'recency', name: 'R 近度', desc: '最近购买天数',
      value: score?.recency || 0, percent: (score?.recency || 0) / 5,
      color: '#6c5ce7',
    },
    {
      key: 'frequency', name: 'F 频度', desc: '购买频率',
      value: score?.frequency || 0, percent: (score?.frequency || 0) / 5,
      color: '#00b894',
    },
    {
      key: 'monetary', name: 'M 额度', desc: '消费金额',
      value: score?.monetary || 0, percent: (score?.monetary || 0) / 5,
      color: '#fdcb6e',
    },
  ]
})

// ==================== 聚类信息 ====================

const clusterNames = ['高消费活跃用户', '中等消费用户', '低频低消费用户', '新用户群体', '流失预警用户']
const clusterDescs = [
  '消费频率高、金额大，为平台核心用户，需重点维护',
  '消费稳定，有一定忠诚度，可通过促销活动提升消费',
  '消费频次和金额偏低，需通过精准推荐激活',
  '刚注册不久的用户，需引导完成首次购买',
  '长时间未消费，有流失风险，需进行召回',
]
const clusterColors = ['#6c5ce7', '#00b894', '#fdcb6e', '#74b9ff', '#e17055']

const clusterName = computed(() => {
  if (detail.value == null) return '--'
  return clusterNames[detail.value.cluster_label] || '未分类'
})
const clusterDesc = computed(() => {
  if (detail.value == null) return ''
  return clusterDescs[detail.value.cluster_label] || ''
})
const clusterColor = computed(() => {
  if (detail.value == null) return '#ccc'
  return clusterColors[detail.value.cluster_label] || '#ccc'
})

// ==================== 用户画像指标 ====================

const profileIndicators = computed(() => {
  if (!profile.value) return []
  return [
    { label: '平均客单价', value: `¥${profile.value.avg_order_value.toFixed(2)}` },
    { label: '累计订单', value: `${profile.value.total_orders} 笔` },
    { label: '距上次购买', value: `${profile.value.days_since_last_purchase} 天` },
    { label: '活跃时段', value: profile.value.active_hours.map((h) => `${h}:00`).join(', ') },
  ]
})

// ==================== 工具函数 ====================

const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString('zh-CN')
}

// ==================== 图表渲染 ====================

/** 渲染 RFM 雷达图 */
const renderRFMRadar = (): void => {
  if (!rfmRadarRef.value || !detail.value) return
  if (!rfmRadarChart) rfmRadarChart = echarts.init(rfmRadarRef.value)

  const score = detail.value.rfm_score
  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8ecf1',
      textStyle: { color: '#2d3436', fontSize: 13 },
      padding: [10, 14],
      extraCssText: 'border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.06);',
    },
    radar: {
      center: ['50%', '50%'],
      radius: '65%',
      indicator: [
        { name: 'R 近度', max: 5 },
        { name: 'F 频度', max: 5 },
        { name: 'M 额度', max: 5 },
      ],
      axisName: { color: '#636e72', fontSize: 13 },
      splitArea: {
        areaStyle: { color: ['rgba(108,92,231,0.02)', 'rgba(108,92,231,0.04)'] },
      },
      splitLine: { lineStyle: { color: '#e8ecf1' } },
      axisLine: { lineStyle: { color: '#e8ecf1' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [score.recency, score.frequency, score.monetary],
        name: 'RFM评分',
        areaStyle: { color: 'rgba(108,92,231,0.2)' },
        lineStyle: { color: '#6c5ce7', width: 2 },
        itemStyle: { color: '#6c5ce7' },
        symbol: 'circle',
        symbolSize: 8,
      }],
    }],
  }

  rfmRadarChart.setOption(option)
}

/** 渲染用户画像-偏好分类柱状图 */
const renderCategoryChart = (): void => {
  if (!categoryChartRef.value || !profile.value) return
  if (!categoryChart) categoryChart = echarts.init(categoryChartRef.value)

  const cats = profile.value.prefer_categories
  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e8ecf1',
      textStyle: { color: '#2d3436', fontSize: 13 },
      padding: [10, 14],
      extraCssText: 'border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,0.06);',
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#b2bec3', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f0f3f7', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: cats.map((c) => c.name),
      inverse: true,
      axisLabel: { color: '#636e72', fontSize: 12 },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    series: [{
      type: 'bar',
      data: cats.map((c, i) => ({
        value: c.count,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: ['#6c5ce7', '#00b894', '#74b9ff', '#fdcb6e', '#e17055'][i] },
            { offset: 1, color: ['#a29bfe', '#55efc4', '#81ecec', '#ffeaa7', '#fab1a0'][i] },
          ]),
          borderRadius: [0, 10, 10, 0],
        },
      })),
      barWidth: 22,
      label: { show: true, position: 'right', color: '#636e72', fontSize: 12 },
    }],
  }

  categoryChart.setOption(option)
}

// ==================== 数据加载 ====================

const loadDetail = async (): Promise<void> => {
  detailLoading.value = true
  try {
    const res = await getUserDetail(userId.value)
    detail.value = res.data
    await nextTick()
    if (activeTab.value === 'rfm') renderRFMRadar()
  } catch { /* handled */ } finally { detailLoading.value = false }
}

const loadProfile = async (): Promise<void> => {
  profileLoading.value = true
  try {
    const res = await getUserProfile(userId.value)
    profile.value = res.data
    await nextTick()
    renderCategoryChart()
  } catch { /* handled */ } finally { profileLoading.value = false }
}

/** Tab 切换时的处理 */
const handleTabChange = (tab: string): void => {
  nextTick(() => {
    if (tab === 'rfm') renderRFMRadar()
    if (tab === 'profile' && profile.value) renderCategoryChart()
  })
}

watch(activeTab, handleTabChange)
watch(userId, () => { loadDetail(); loadProfile() })

// ==================== 生命周期 ====================

onMounted(() => {
  loadDetail()
  loadProfile()
})

const handleResize = () => {
  rfmRadarChart?.resize()
  categoryChart?.resize()
}

onMounted(() => window.addEventListener('resize', handleResize))
onBeforeUnmount(() => {
  rfmRadarChart?.dispose()
  categoryChart?.dispose()
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
.user-detail-page {
  max-width: 1000px;
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
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #2d3436;
}

/* ========== Tabs ========== */
.detail-tabs {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--border-light);
  box-shadow: none;

  :deep(.el-tabs__header) {
    background: #fafbfc;
    border-bottom: 1px solid var(--border-light);
    margin: 0;
  }

  :deep(.el-tabs__content) {
    padding: 0;
  }
}

.tab-content {
  padding: 24px;
  min-height: 360px;
}

/* ========== 基本信息网格 ========== */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  overflow: hidden;
}

.info-item {
  display: flex;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-light);

  &:nth-child(odd) {
    border-right: 1px solid var(--border-light);
  }

  &:nth-last-child(-n+2) {
    border-bottom: none;
  }
}

.info-label {
  width: 90px;
  font-size: 13px;
  color: #b2bec3;
  flex-shrink: 0;
}

.info-value {
  font-size: 14px;
  color: #2d3436;
  font-weight: 500;

  &.amount {
    color: #6c5ce7;
    font-weight: 600;
  }
}

/* ========== RFM 卡片区 ========== */
.rfm-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.rfm-cards {
  display: flex;
  gap: 24px;
  justify-content: center;
}

.rfm-card {
  text-align: center;
}

.rfm-card-circle {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 12px;

  svg {
    width: 100%;
    height: 100%;
  }
}

.rfm-card-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.rfm-score {
  font-size: 28px;
  font-weight: 800;
  color: #2d3436;
}

.rfm-unit {
  font-size: 11px;
  color: #b2bec3;
}

.rfm-card-name {
  font-size: 14px;
  font-weight: 600;
  color: #2d3436;
}

.rfm-card-desc {
  font-size: 12px;
  color: #b2bec3;
  margin-top: 2px;
}

.sub-chart-card {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  :deep(.el-card__header) h4 { margin: 0; font-size: 15px; color: #2d3436; }
}

/* ========== 聚类信息 ========== */
.cluster-info {
  display: flex;
  justify-content: center;
  padding: 32px 0;
}

.cluster-badge {
  display: flex;
  align-items: center;
  gap: 20px;
}

.cluster-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
}

.cluster-name {
  font-size: 20px;
  font-weight: 700;
  color: #2d3436;
}

.cluster-desc {
  font-size: 13px;
  color: #636e72;
  margin-top: 6px;
  max-width: 320px;
}

/* ========== 用户画像 ========== */
.profile-tags {
  margin-bottom: 24px;

  h4 { margin: 0 0 12px; color: #2d3436; }
}

.tags-wrap {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.profile-charts {
  margin-bottom: 24px;

  .el-card {
    border: 1px solid var(--border-light);
    border-radius: 12px;
  }
}

.profile-indicators {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.profile-indicator {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  background: rgba(108,92,231,0.03);
  border-radius: 10px;

  .ind-label { font-size: 13px; color: #b2bec3; }
  .ind-value { font-size: 14px; font-weight: 600; color: #2d3436; }
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .info-grid { grid-template-columns: 1fr; }
  .rfm-cards { flex-wrap: wrap; }
  .profile-indicators { grid-template-columns: 1fr; }
}
</style>
